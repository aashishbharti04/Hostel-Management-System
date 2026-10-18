# PFE-RA Research Engine

Standalone research module for policy-aware hostel room allocation. It remains separate from the Flask/SQLite/MySQL app until solver correctness and integration contracts have been reviewed.

## Model

CP-SAT enforces eligibility and one-student-per-bed. Objectives are optimized lexicographically, fixing each proven optimum before the next stage:

1. Maximize accommodated students.
2. Minimize maximum preference regret. Unallocated students incur their best eligible utility as regret.
3. Maximize total preference utility.
4. Minimize changes to existing assignments.

Utilities are non-negative integers. If a stage is FEASIBLE but not OPTIMAL, the run stops and is reported as incomplete.

## Install and test

Python 3.10+:

    python -m pip install -e ".[test]"
    python -m pytest -q
    python -m pfera.benchmark --output results --sizes 8,16 --seeds 7,17 --time-limit 10

## Exactness tests

Tests compare CP-SAT's objective tuple against exhaustive enumeration on small instances. OR-Tools is required and the dedicated workflow does not skip solver tests.

## Scope and limitations

Research prototype, not production allocation service. It does not encode institution-specific policy, room compatibility, authenticated approvals, database transactions, or application authorization. Never commit real student data. Benchmarks are valid only for the recorded generator, dependencies, platform, solver status, and configuration.
