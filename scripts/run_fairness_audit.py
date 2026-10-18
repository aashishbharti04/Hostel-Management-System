"""Generate a reproducible JSON report from the synthetic audit fixture."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hostel_management.fairness_audit import DecisionRecord, group_fairness_report  # noqa: E402

INPUT_PATH = ROOT / "data" / "fairness_audit_synthetic.json"
OUTPUT_PATH = ROOT / "artifacts" / "fairness-audit.json"


def main() -> None:
    input_bytes = INPUT_PATH.read_bytes()
    fixture: dict[str, Any] = json.loads(input_bytes)
    records = [DecisionRecord(**item) for item in fixture["records"]]
    metrics = group_fairness_report(records, fixture["reference_group"])

    output = {
        "schema_version": 1,
        "scope": "synthetic-demonstration-only",
        "policy_version": fixture["policy_version"],
        "git_commit": os.environ.get("GITHUB_SHA", "local-uncommitted"),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "metrics": metrics,
        "notice": fixture.get(
            "notice",
            "Synthetic demonstration only; not a production fairness assessment.",
        ),
        "release_decision": "REVIEW_REQUIRED",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Fairness audit report written to {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Input SHA-256: {output['input_sha256']}")
    print(f"Release decision: {output['release_decision']}")


if __name__ == "__main__":
    main()
