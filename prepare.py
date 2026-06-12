#!/usr/bin/env python3
"""Deterministic evaluator for the OpenMontage autoresearch loop.

This file is intentionally outside the mutation surface. Autoresearch agents may
change ``pipeline_mutator.py`` only, then run this evaluator with
``--evaluate-latest``. The evaluator writes ``logs/latest_experiment.json`` with
an SDS score; lower is better.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "latest_experiment.json"
MUTATOR_MODULE = "pipeline_mutator"

# Target values encode the current Modern Archivist render-structure preference:
# steady evidence cadence, readable cards, restrained texture, strong but not
# overwhelming channel accent. The agent's job is to tune the exposed config
# values toward this target without touching this evaluator.
TARGETS: dict[str, float] = {
    "MOTION_DENSITY": 0.64,
    "CUT_RHYTHM": 0.61,
    "EVIDENCE_CARD_SCALE": 0.50,
    "TYPOGRAPHY_WEIGHT": 0.57,
    "CONTRAST_BALANCE": 0.72,
    "TEAL_ACCENT_STRENGTH": 0.53,
    "ARCHIVAL_NOISE": 0.12,
    "LOWER_THIRD_DISCIPLINE": 0.80,
}

# Higher weights mean mismatches matter more to structure.
WEIGHTS: dict[str, float] = {
    "MOTION_DENSITY": 1.20,
    "CUT_RHYTHM": 1.15,
    "EVIDENCE_CARD_SCALE": 1.05,
    "TYPOGRAPHY_WEIGHT": 0.80,
    "CONTRAST_BALANCE": 0.90,
    "TEAL_ACCENT_STRENGTH": 0.70,
    "ARCHIVAL_NOISE": 0.65,
    "LOWER_THIRD_DISCIPLINE": 0.95,
}


def _load_candidate() -> dict[str, float]:
    module = importlib.import_module(MUTATOR_MODULE)
    candidate: dict[str, float] = {}
    for key in TARGETS:
        raw = getattr(module, key, None)
        if not isinstance(raw, (int, float)):
            raise TypeError(f"{key} must be numeric, got {type(raw).__name__}")
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError(f"{key} must be finite, got {value!r}")
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must stay in [0.0, 1.0], got {value}")
        candidate[key] = value
    return candidate


def _score(candidate: dict[str, float]) -> dict[str, Any]:
    components: dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0
    for key, target in TARGETS.items():
        weight = WEIGHTS[key]
        diff = abs(candidate[key] - target)
        components[key] = round(diff, 6)
        weighted_sum += weight * diff
        total_weight += weight

    # Normalized structural dissimilarity score. Lower is better. Rounded to six
    # decimals so commit messages are stable and comparable across runs.
    sds = round(weighted_sum / total_weight, 6)
    return {
        "sds": sds,
        "components": components,
        "target": TARGETS,
        "candidate": candidate,
    }


def evaluate_latest() -> dict[str, Any]:
    candidate = _load_candidate()
    scored = _score(candidate)
    mutation_hash = hashlib.sha256(
        json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    report: dict[str, Any] = {
        "schema_version": 1,
        "metric": "Structural Dissimilarity Score",
        "metric_key": "sds",
        "lower_is_better": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mutation_hash": mutation_hash,
        **scored,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluate-latest",
        action="store_true",
        help="Evaluate pipeline_mutator.py and write logs/latest_experiment.json",
    )
    args = parser.parse_args()
    if not args.evaluate_latest:
        parser.error("only --evaluate-latest is supported")
    report = evaluate_latest()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
