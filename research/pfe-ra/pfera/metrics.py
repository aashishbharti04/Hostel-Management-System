"""Metrics for allocation comparisons."""
from __future__ import annotations
from .models import Scenario

def metrics_for(scenario: Scenario, assignments: dict[str, str]) -> dict[str, int | float]:
    regrets: list[int] = []
    utility = 0
    for student in scenario.students:
        eligible = scenario.eligible_beds[student]
        best = max((scenario.utility[(student, bed)] for bed in eligible), default=0)
        bed = assignments.get(student)
        if bed is None:
            regrets.append(best)
        else:
            score = scenario.utility[(student, bed)]
            utility += score
            regrets.append(best - score)
    return {
        "allocated_count": len(assignments),
        "allocation_rate": len(assignments) / len(scenario.students) if scenario.students else 1.0,
        "max_regret": max(regrets, default=0),
        "mean_regret": sum(regrets) / len(regrets) if regrets else 0.0,
        "total_utility": utility,
        "reassignments": sum(1 for student, old in scenario.previous_assignments.items() if assignments.get(student) != old),
    }
