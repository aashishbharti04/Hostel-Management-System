"""Typed input model for allocation experiments."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Scenario:
    """Utilities are non-negative integer scores for eligible student-bed pairs."""
    students: tuple[str, ...]
    beds: tuple[str, ...]
    eligible_beds: dict[str, tuple[str, ...]]
    utility: dict[tuple[str, str], int]
    previous_assignments: dict[str, str] = field(default_factory=dict)
    scenario_id: str = "unnamed"

    def validate(self) -> None:
        if len(set(self.students)) != len(self.students):
            raise ValueError("student identifiers must be unique")
        if len(set(self.beds)) != len(self.beds):
            raise ValueError("bed identifiers must be unique")
        student_set, bed_set = set(self.students), set(self.beds)
        if set(self.eligible_beds) != student_set:
            raise ValueError("eligible_beds must contain exactly every student")
        for student, eligible in self.eligible_beds.items():
            if len(set(eligible)) != len(eligible):
                raise ValueError(f"duplicate eligible bed for {student}")
            if not set(eligible) <= bed_set:
                raise ValueError(f"unknown bed in eligibility list for {student}")
            for bed in eligible:
                score = self.utility.get((student, bed))
                if score is None or not isinstance(score, int):
                    raise ValueError(f"missing integer utility for eligible pair {(student, bed)}")
                if score < 0:
                    raise ValueError("utilities must be non-negative integers")
        if not set(self.previous_assignments) <= student_set:
            raise ValueError("previous assignments contain unknown students")
        if not set(self.previous_assignments.values()) <= bed_set:
            raise ValueError("previous assignments contain unknown beds")
