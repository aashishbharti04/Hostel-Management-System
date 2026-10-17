"""Deterministic CP-SAT hostel allocator. Install requirements-allocation.txt."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None

@dataclass(frozen=True)
class AllocationResult:
    status: str
    assignments: tuple[dict[str, Any], ...]
    objective_value: int | None
    best_bound: int | None
    metrics: dict[str, int | str]
    explanation: str

def solve_allocation(applications: Sequence[Mapping[str, Any]], beds: Sequence[Mapping[str, Any]], *,
                     time_limit_seconds: float = 10.0, random_seed: int = 17) -> AllocationResult:
    """Maximize filled beds first, then approved priority and stated room preferences.

    Application: id, student_id, eligible, priority (0..100), requested_hostel_id,
    preferred_room_types, accessibility_required. Bed: id, hostel_id, room_type,
    is_accessible, available. Caller must pass an authorized, consistent snapshot.
    """
    if cp_model is None:
        raise RuntimeError("OR-Tools missing; install requirements-allocation.txt")
    if not 0 < time_limit_seconds <= 120:
        raise ValueError("time_limit_seconds must be in (0, 120]")
    aids = [str(a.get("id", "")) for a in applications]
    bids = [str(b.get("id", "")) for b in beds]
    if not all(aids) or len(set(aids)) != len(aids): raise ValueError("Application ids must be non-empty and unique")
    if not all(bids) or len(set(bids)) != len(bids): raise ValueError("Bed ids must be non-empty and unique")
    eligible = []
    for a in applications:
        if not a.get("eligible", False): continue
        p = a.get("priority", 0)
        if isinstance(p, bool) or not isinstance(p, int) or not 0 <= p <= 100: raise ValueError("priority must be an integer from 0 to 100")
        if not a.get("student_id"): raise ValueError("Every application must have a student_id")
        eligible.append(a)
    if len({str(a["student_id"]) for a in eligible}) != len(eligible):
        raise ValueError("Snapshot contains more than one eligible application per student")
    available = [b for b in beds if b.get("available", True)]
    if not eligible or not available:
        return AllocationResult("optimal", (), 0, 0, {"eligible_applications":len(eligible),"available_beds":len(available),"assigned":0,"unassigned_eligible":len(eligible)}, "No eligible applicants or available beds.")
    model = cp_model.CpModel()
    x = {}
    for i,a in enumerate(eligible):
        for j,b in enumerate(available):
            hostel_ok = not a.get("requested_hostel_id") or str(a["requested_hostel_id"]) == str(b.get("hostel_id"))
            access_ok = not a.get("accessibility_required", False) or bool(b.get("is_accessible", False))
            if hostel_ok and access_ok: x[i,j] = model.new_bool_var(f"app_{i}_bed_{j}")
    for i in range(len(eligible)): model.add(sum(v for (ii,_),v in x.items() if ii == i) <= 1)
    for j in range(len(available)): model.add(sum(v for (_,jj),v in x.items() if jj == j) <= 1)
    # Maximum secondary score is bounded by 210 per assigned student. A larger bonus
    # guarantees cardinality dominates priority/preferences even for large instances.
    assignment_bonus = len(eligible) * 210 + 1
    terms = []
    for (i,j),var in x.items():
        a,b = eligible[i],available[j]
        preferred = b.get("room_type") in (a.get("preferred_room_types") or [])
        score = int(a.get("priority",0)) + (100 if preferred else 0) + max(0,10-j)
        terms.append(var * (assignment_bonus + score))
    model.maximize(sum(terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int(random_seed)
    code = solver.solve(model)
    statuses = {cp_model.OPTIMAL:"optimal",cp_model.FEASIBLE:"feasible",cp_model.INFEASIBLE:"infeasible",cp_model.MODEL_INVALID:"failed",cp_model.UNKNOWN:"failed"}
    status = statuses.get(code,"failed")
    if status not in ("optimal","feasible"):
        return AllocationResult(status,(),None,None,{"eligible_applications":len(eligible),"available_beds":len(available),"assigned":0,"unassigned_eligible":len(eligible)},"No proposal produced; review constraints and snapshot.")
    rows = []
    for (i,j),var in x.items():
        if not solver.boolean_value(var): continue
        a,b=eligible[i],available[j]
        preferred = b.get("room_type") in (a.get("preferred_room_types") or [])
        reasons=["eligible_application_and_available_bed"]
        if a.get("requested_hostel_id"): reasons.append("requested_hostel_satisfied")
        if preferred: reasons.append("preferred_room_type")
        if a.get("accessibility_required"): reasons.append("accessibility_requirement_satisfied")
        rows.append({"application_id":str(a["id"]),"student_id":str(a["student_id"]),"bed_id":str(b["id"]),
                     "score":int(a.get("priority",0))+(100 if preferred else 0),
                     "explanation":{"reason_codes":reasons,"priority_points":int(a.get("priority",0)),"preference_points":100 if preferred else 0}})
    rows.sort(key=lambda r:(r["application_id"],r["bed_id"]))
    count=len(rows)
    return AllocationResult(status,tuple(rows),int(solver.objective_value),int(solver.best_objective_bound),
        {"eligible_applications":len(eligible),"available_beds":len(available),"assigned":count,
         "unassigned_eligible":len(eligible)-count,"coverage_percent":round(100*count/len(eligible))},
        "Capacity is maximized before documented priority and declared room preferences. No protected demographic attribute is a solver input. Human approval is required.")
