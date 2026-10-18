"""Reusable fairness-audit primitives for explicit governance decisions."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class DecisionRecord:
    subject_id: str
    group: str
    eligible: bool
    selected: bool
    decision: str


def selection_rate(records: Iterable[DecisionRecord], group: str) -> float | None:
    eligible = [record for record in records if record.group == group and record.eligible]
    return None if not eligible else sum(record.selected for record in eligible) / len(eligible)


def group_fairness_report(
    records: Sequence[DecisionRecord], reference_group: str
) -> dict[str, Any]:
    groups = sorted({record.group for record in records})
    if reference_group not in groups:
        raise ValueError(f"Unknown reference group: {reference_group}")

    reference_rate = selection_rate(records, reference_group)
    if reference_rate is None:
        raise ValueError("Reference group has no eligible observations")

    report: dict[str, Any] = {
        "reference_group": reference_group,
        "reference_selection_rate": reference_rate,
        "groups": {},
        "interpretation": (
            "Descriptive disparity only; investigate context, sample size, legitimate "
            "policy factors, and applicable law before conclusions."
        ),
    }
    for group in groups:
        eligible = [
            record for record in records if record.group == group and record.eligible
        ]
        rate = selection_rate(records, group)
        report["groups"][group] = {
            "eligible_count": len(eligible),
            "selected_count": sum(record.selected for record in eligible),
            "selection_rate": rate,
            "rate_difference": None if rate is None else rate - reference_rate,
            "selection_rate_ratio": (
                None if rate is None or reference_rate == 0 else rate / reference_rate
            ),
        }
    return report


def counterfactual_check(
    decide: Callable[[Mapping[str, Any]], Any],
    case: Mapping[str, Any],
    attribute: str,
    alternative_value: Any,
) -> dict[str, Any]:
    if attribute not in case:
        raise KeyError(f"Counterfactual attribute not present: {attribute}")

    original = dict(case)
    changed = dict(case)
    changed[attribute] = alternative_value
    before, after = decide(original), decide(changed)
    return {
        "attribute": attribute,
        "passed": before == after,
        "original_decision": before,
        "counterfactual_decision": after,
    }


def exhaustive_optimum(
    candidates: Sequence[Mapping[str, Any]],
    capacity: int,
    score: Callable[[Sequence[Mapping[str, Any]]], int | float],
) -> dict[str, Any]:
    """Exhaustively score eligible subsets; use only as a small-instance oracle."""
    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    ids = [str(candidate["id"]) for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate IDs must be unique")

    eligible = [
        candidate for candidate in candidates if bool(candidate.get("eligible", False))
    ]
    best_score: int | float | None = None
    best_ids: tuple[str, ...] = ()
    examined = 0
    for size in range(min(capacity, len(eligible)) + 1):
        for subset in combinations(eligible, size):
            examined += 1
            subset_ids = tuple(sorted(str(candidate["id"]) for candidate in subset))
            value = score(subset)
            if (
                best_score is None
                or value > best_score
                or (value == best_score and subset_ids < best_ids)
            ):
                best_score, best_ids = value, subset_ids

    return {
        "status": "OPTIMAL_EXHAUSTIVE",
        "objective_value": best_score if best_score is not None else 0,
        "selected_ids": list(best_ids),
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "capacity": capacity,
        "subsets_examined": examined,
    }
