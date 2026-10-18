"""Seeded synthetic scenario generation."""
from __future__ import annotations
import random
from .models import Scenario

def make_scenario(*, students: int, beds: int, seed: int, eligibility_density: float = 0.75, previous_assignment_fraction: float = 0.0) -> Scenario:
    if students < 0 or beds < 0:
        raise ValueError("students and beds must be non-negative")
    if not 0 <= eligibility_density <= 1:
        raise ValueError("eligibility_density must be in [0, 1]")
    if not 0 <= previous_assignment_fraction <= 1:
        raise ValueError("previous_assignment_fraction must be in [0, 1]")
    rng = random.Random(seed)
    student_ids = tuple(f"S{i:04d}" for i in range(students))
    bed_ids = tuple(f"B{i:04d}" for i in range(beds))
    eligible: dict[str, tuple[str, ...]] = {}
    utility: dict[tuple[str, str], int] = {}
    for student in student_ids:
        chosen = [bed for bed in bed_ids if rng.random() < eligibility_density]
        if beds and eligibility_density > 0 and not chosen:
            chosen = [rng.choice(bed_ids)]
        rng.shuffle(chosen)
        eligible[student] = tuple(chosen)
        for bed in chosen:
            utility[(student, bed)] = rng.randint(0, 100)
    previous: dict[str, str] = {}
    if beds:
        available = list(bed_ids)
        rng.shuffle(available)
        count = min(int(students * previous_assignment_fraction), len(available))
        for student, bed in zip(student_ids[:count], available[:count], strict=False):
            if bed in eligible[student]:
                previous[student] = bed
    scenario = Scenario(student_ids, bed_ids, eligible, utility, previous, f"seed-{seed}")
    scenario.validate()
    return scenario
