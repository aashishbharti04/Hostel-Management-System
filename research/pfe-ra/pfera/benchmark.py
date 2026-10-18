"""Reproducible JSON/CSV benchmark runner."""
from __future__ import annotations
import argparse
import csv
import json
import platform
import sys
from pathlib import Path
from .baselines import first_fit, preference_greedy
from .engine import solve_pfera
from .metrics import metrics_for
from .synthetic_data import make_scenario
from .validation import validate_allocation

def run_benchmarks(sizes: list[int], seeds: list[int], time_limit: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for size in sizes:
        for seed in seeds:
            scenario = make_scenario(students=size, beds=max(size, int(size * 1.1)), seed=seed,
                eligibility_density=0.65, previous_assignment_fraction=0.2)
            for name, algorithm in (("first_fit", first_fit), ("preference_greedy", preference_greedy)):
                assignment = algorithm(scenario)
                validation = validate_allocation(scenario, assignment)
                rows.append({
                    "scenario": scenario.scenario_id, "students": size, "beds": len(scenario.beds),
                    "seed": seed, "algorithm": name, "status": "VALIDATED" if validation.valid else "INVALID",
                    **metrics_for(scenario, assignment), "runtime_seconds": None,
                    "validation_errors": list(validation.violations),
                })
            result = solve_pfera(scenario, time_limit_seconds=time_limit, random_seed=seed)
            validation = validate_allocation(scenario, result.assignments)
            rows.append({
                "scenario": scenario.scenario_id, "students": size, "beds": len(scenario.beds),
                "seed": seed, "algorithm": "pfe_ra", "status": result.status,
                "allocated_count": result.allocated_count, "max_regret": result.max_regret,
                "total_utility": result.total_utility, "reassignments": result.reassignments,
                "runtime_seconds": result.runtime_seconds, "validation_errors": list(validation.violations),
                "stage_statuses": list(result.stage_statuses),
            })
    return rows

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results")
    parser.add_argument("--sizes", default="8,16")
    parser.add_argument("--seeds", default="7,17")
    parser.add_argument("--time-limit", type=float, default=10.0)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    rows = run_benchmarks([int(x) for x in args.sizes.split(",")], [int(x) for x in args.seeds.split(",")], args.time_limit)
    (output / "benchmark_results.json").write_text(
        json.dumps({"python": sys.version, "platform": platform.platform(), "results": rows}, indent=2), encoding="utf-8")
    fields = sorted({key for row in rows for key in row if not isinstance(row.get(key), (dict, list))})
    with (output / "benchmark_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: value for key, value in row.items() if key in fields} for row in rows)
    print(f"Wrote {len(rows)} records to {output}")

if __name__ == "__main__":
    main()
