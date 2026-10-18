"""Independent post-solve allocation validation."""
from __future__ import annotations
from dataclasses import dataclass
from .models import Scenario

@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    violations: tuple[str, ...]

def validate_allocation(scenario: Scenario, assignments: dict[str, str], *, freeze_previous: bool = False) -> ValidationReport:
    """Validate a candidate without relying on the optimizer's internal model."""
    violations: list[str] = []
    students, beds = set(scenario.students), set(scenario.beds)
    unknown_students = set(assignments) - students
    if unknown_students:
        violations.append(f"unknown students: {sorted(unknown_students)}")
    values = list(assignments.values())
    if len(values) != len(set(values)):
        violations.append("a bed is assigned to more than one student")
    for student, bed in assignments.items():
        if student not in students:
            continue
        if bed not in beds:
            violations.append(f"unknown bed {bed!r} assigned to {student!r}")
            continue
        if bed not in scenario.eligible_beds[student]:
            violations.append(f"ineligible assignment: {student!r} -> {bed!r}")
    if freeze_previous:
        for student, old_bed in scenario.previous_assignments.items():
            if assignments.get(student) != old_bed:
                violations.append(f"frozen assignment changed for {student!r}")
    return ValidationReport(not violations, tuple(violations))
