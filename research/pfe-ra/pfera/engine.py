"""CP-SAT lexicographic optimizer for PFE-RA."""
from __future__ import annotations
from dataclasses import dataclass
from ortools.sat.python import cp_model
from .models import Scenario
from .validation import validate_allocation

@dataclass(frozen=True)
class AllocationResult:
    assignments: dict[str, str]
    status: str
    stage_statuses: tuple[str, ...]
    allocated_count: int
    max_regret: int
    total_utility: int
    reassignments: int
    runtime_seconds: float

def _metrics(scenario: Scenario, assignments: dict[str, str]) -> tuple[int, int, int, int]:
    allocated = len(assignments)
    regrets: list[int] = []
    utility = 0
    for student in scenario.students:
        options = scenario.eligible_beds[student]
        best = max((scenario.utility[(student, bed)] for bed in options), default=0)
        bed = assignments.get(student)
        if bed is None:
            regrets.append(best)
        else:
            score = scenario.utility[(student, bed)]
            utility += score
            regrets.append(best - score)
    max_regret = max(regrets, default=0)
    changes = sum(1 for student, old in scenario.previous_assignments.items() if assignments.get(student) != old)
    return allocated, max_regret, utility, changes

def solve_pfera(scenario: Scenario, *, time_limit_seconds: float = 10.0, random_seed: int = 0) -> AllocationResult:
    """Optimize lexicographically: accommodation, max regret, utility, stability.

    Every stage must prove OPTIMAL before its objective is fixed and the next
    stage begins. FEASIBLE without proof is reported as incomplete, not optimal.
    """
    scenario.validate()
    if time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive")

    model = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    assigned: dict[str, cp_model.IntVar] = {}
    for student in scenario.students:
        assigned[student] = model.NewBoolVar(f"assigned_{student}")
        for bed in scenario.beds:
            x[(student, bed)] = model.NewBoolVar(f"x_{student}_{bed}")
            if bed not in scenario.eligible_beds[student]:
                model.Add(x[(student, bed)] == 0)
        model.Add(sum(x[(student, bed)] for bed in scenario.beds) == assigned[student])
    for bed in scenario.beds:
        model.Add(sum(x[(student, bed)] for student in scenario.students) <= 1)

    best: dict[str, int] = {
        student: max((scenario.utility[(student, bed)] for bed in scenario.eligible_beds[student]), default=0)
        for student in scenario.students
    }
    regrets: dict[str, cp_model.IntVar] = {}
    for student in scenario.students:
        regrets[student] = model.NewIntVar(0, best[student], f"regret_{student}")
        allocated_regret = sum(
            (best[student] - scenario.utility[(student, bed)]) * x[(student, bed)]
            for bed in scenario.eligible_beds[student]
        )
        model.Add(regrets[student] == allocated_regret + best[student] * (1 - assigned[student]))

    max_regret = model.NewIntVar(0, max(best.values(), default=0), "maximum_regret")
    for student in scenario.students:
        model.Add(max_regret >= regrets[student])

    total_allocated = sum(assigned.values())
    total_utility = sum(
        scenario.utility[(student, bed)] * x[(student, bed)]
        for student in scenario.students
        for bed in scenario.eligible_beds[student]
    )
    changes = sum(
        1 - x[(student, old_bed)]
        for student, old_bed in scenario.previous_assignments.items()
    )
    stages = [
        ("maximize_accommodation", total_allocated, True),
        ("minimize_max_regret", max_regret, False),
        ("maximize_total_utility", total_utility, True),
        ("minimize_reassignments", changes, False),
    ]
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.random_seed = random_seed
    solver.parameters.num_search_workers = 1
    statuses: list[str] = []
    elapsed = 0.0

    for _, expression, maximize in stages:
        if maximize:
            model.Maximize(expression)
        else:
            model.Minimize(expression)
        status = solver.Solve(model)
        name = solver.StatusName(status)
        statuses.append(name)
        elapsed += solver.WallTime()
        if status != cp_model.OPTIMAL:
            candidate = {}
            if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
                candidate = {
                    student: bed for student in scenario.students for bed in scenario.beds
                    if solver.Value(x[(student, bed)]) == 1
                }
            a, r, u, d = _metrics(scenario, candidate)
            return AllocationResult(candidate, name, tuple(statuses), a, r, u, d, elapsed)
        model.Add(expression == solver.Value(expression))

    assignments = {
        student: bed for student in scenario.students for bed in scenario.beds
        if solver.Value(x[(student, bed)]) == 1
    }
    report = validate_allocation(scenario, assignments)
    if not report.valid:
        raise RuntimeError(f"independent allocation validation failed: {report.violations}")
    a, r, u, d = _metrics(scenario, assignments)
    return AllocationResult(assignments, "OPTIMAL", tuple(statuses), a, r, u, d, elapsed)
