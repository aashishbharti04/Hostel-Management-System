"""Deterministic CP-SAT hostel allocator. Install requirements-allocation.txt."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

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


def solve_allocation(
    applications: Sequence[Mapping[str, Any]],
    beds: Sequence[Mapping[str, Any]],
    *,
    time_limit_seconds: float = 10.0,
    random_seed: int = 17,
) -> AllocationResult:
    """Maximize filled beds first, then approved priority and room preferences.

    Application: id, student_id, eligible, priority (0..100), requested_hostel_id,
    preferred_room_types, accessibility_required. Bed: id, hostel_id, room_type,
    is_accessible, available. The caller must pass an authorized, consistent snapshot.
    """
    if cp_model is None:
        raise RuntimeError("OR-Tools missing; install requirements-allocation.txt")
    if not 0 < time_limit_seconds <= 120:
        raise ValueError("time_limit_seconds must be in (0, 120]")

    application_ids = [str(app.get("id", "")) for app in applications]
    bed_ids = [str(bed.get("id", "")) for bed in beds]
    if not all(application_ids) or len(set(application_ids)) != len(application_ids):
        raise ValueError("Application ids must be non-empty and unique")
    if not all(bed_ids) or len(set(bed_ids)) != len(bed_ids):
        raise ValueError("Bed ids must be non-empty and unique")

    eligible = []
    for application in applications:
        if not application.get("eligible", False):
            continue
        priority = application.get("priority", 0)
        if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 100:
            raise ValueError("priority must be an integer from 0 to 100")
        if not application.get("student_id"):
            raise ValueError("Every application must have a student_id")
        eligible.append(application)

    if len({str(app["student_id"]) for app in eligible}) != len(eligible):
        raise ValueError("Snapshot contains more than one eligible application per student")

    available = [bed for bed in beds if bed.get("available", True)]
    if not eligible or not available:
        return AllocationResult(
            "optimal",
            (),
            0,
            0,
            {
                "eligible_applications": len(eligible),
                "available_beds": len(available),
                "assigned": 0,
                "unassigned_eligible": len(eligible),
            },
            "No eligible applicants or available beds.",
        )

    model = cp_model.CpModel()
    variables = {}
    for app_index, application in enumerate(eligible):
        for bed_index, bed in enumerate(available):
            hostel_ok = not application.get("requested_hostel_id") or str(
                application["requested_hostel_id"]
            ) == str(bed.get("hostel_id"))
            access_ok = not application.get("accessibility_required", False) or bool(
                bed.get("is_accessible", False)
            )
            if hostel_ok and access_ok:
                variables[app_index, bed_index] = model.new_bool_var(
                    f"app_{app_index}_bed_{bed_index}"
                )

    for app_index in range(len(eligible)):
        model.add(
            sum(variable for (index, _), variable in variables.items() if index == app_index) <= 1
        )
    for bed_index in range(len(available)):
        model.add(
            sum(variable for (_, index), variable in variables.items() if index == bed_index) <= 1
        )

    # This bonus makes assignment coverage dominate all secondary scores.
    assignment_bonus = len(eligible) * 210 + 1
    objective_terms = []
    for (app_index, bed_index), variable in variables.items():
        application = eligible[app_index]
        bed = available[bed_index]
        preferred = bed.get("room_type") in (application.get("preferred_room_types") or [])
        score = (
            int(application.get("priority", 0)) + (100 if preferred else 0) + max(0, 10 - bed_index)
        )
        objective_terms.append(variable * (assignment_bonus + score))

    model.maximize(sum(objective_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int(random_seed)
    code = solver.solve(model)
    statuses = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "failed",
        cp_model.UNKNOWN: "failed",
    }
    status = statuses.get(code, "failed")
    if status not in ("optimal", "feasible"):
        return AllocationResult(
            status,
            (),
            None,
            None,
            {
                "eligible_applications": len(eligible),
                "available_beds": len(available),
                "assigned": 0,
                "unassigned_eligible": len(eligible),
            },
            "No proposal produced; review constraints and snapshot.",
        )

    rows = []
    for (app_index, bed_index), variable in variables.items():
        if not solver.boolean_value(variable):
            continue
        application = eligible[app_index]
        bed = available[bed_index]
        preferred = bed.get("room_type") in (application.get("preferred_room_types") or [])
        reasons = ["eligible_application_and_available_bed"]
        if application.get("requested_hostel_id"):
            reasons.append("requested_hostel_satisfied")
        if preferred:
            reasons.append("preferred_room_type")
        if application.get("accessibility_required"):
            reasons.append("accessibility_requirement_satisfied")
        priority = int(application.get("priority", 0))
        rows.append(
            {
                "application_id": str(application["id"]),
                "student_id": str(application["student_id"]),
                "bed_id": str(bed["id"]),
                "score": priority + (100 if preferred else 0),
                "explanation": {
                    "reason_codes": reasons,
                    "priority_points": priority,
                    "preference_points": 100 if preferred else 0,
                },
            }
        )

    rows.sort(key=lambda row: (row["application_id"], row["bed_id"]))
    assigned = len(rows)
    return AllocationResult(
        status,
        tuple(rows),
        int(solver.objective_value),
        int(solver.best_objective_bound),
        {
            "eligible_applications": len(eligible),
            "available_beds": len(available),
            "assigned": assigned,
            "unassigned_eligible": len(eligible) - assigned,
            "coverage_percent": round(100 * assigned / len(eligible)),
        },
        "Capacity is maximized before documented priority and declared room "
        "preferences. No protected demographic attribute is a solver input. "
        "Human approval is required.",
    )
