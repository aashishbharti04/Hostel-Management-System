"""Deterministic allocation baselines."""
from __future__ import annotations
from .models import Scenario

def first_fit(scenario: Scenario) -> dict[str, str]:
    """Assign students in declared order to the first eligible free bed."""
    scenario.validate()
    used: set[str] = set()
    result: dict[str, str] = {}
    for student in scenario.students:
        for bed in scenario.eligible_beds[student]:
            if bed not in used:
                result[student] = bed
                used.add(bed)
                break
    return result

def preference_greedy(scenario: Scenario) -> dict[str, str]:
    """Assign in declared order to the highest-utility free eligible bed."""
    scenario.validate()
    used: set[str] = set()
    result: dict[str, str] = {}
    for student in scenario.students:
        ranked = sorted(scenario.eligible_beds[student], key=lambda bed: (-scenario.utility[(student, bed)], bed))
        for bed in ranked:
            if bed not in used:
                result[student] = bed
                used.add(bed)
                break
    return result
