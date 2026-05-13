#!/usr/bin/env python3
"""Compact hard gates for the Asymmetric source-commentary path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from lib.asymmetric_gate_policy import (
    ARTIFACT_NAMES,
    GatePolicy,
    GateResult,
    approved_source_or_proof_events,
    parse_silencedetect_log,
    validate_qc_report,
    validate_render_readiness,
)

DEFAULT_ARTIFACT_NAMES = ARTIFACT_NAMES


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"artifact must be a JSON object: {path}")
    return data


def load_artifacts_from_dir(artifact_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        key: load_json(artifact_dir / filename)
        for key, filename in DEFAULT_ARTIFACT_NAMES.items()
        if (artifact_dir / filename).exists()
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Asymmetric source-commentary gates")
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render-readiness", help="Validate pre-render source/proof and approval gates")
    render.add_argument("--artifact-dir", type=Path)
    render.add_argument("--capture-plan", type=Path)
    render.add_argument("--segment-approval", type=Path)
    render.add_argument("--visual-rhythm", type=Path)

    qc = sub.add_parser("qc", help="Validate post-QC creative and silence gates")
    qc.add_argument("--artifact-dir", type=Path)
    qc.add_argument("--qc-report", type=Path)
    qc.add_argument("--ffmpeg-log", type=Path)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    policy = GatePolicy.asymmetric_source_commentary()
    try:
        artifacts = load_artifacts_from_dir(args.artifact_dir) if args.artifact_dir else {}
        if args.command == "render-readiness":
            if args.capture_plan:
                artifacts["capture_plan"] = load_json(args.capture_plan)
            if args.segment_approval:
                artifacts["segment_approval"] = load_json(args.segment_approval)
            if args.visual_rhythm:
                artifacts["visual_rhythm"] = load_json(args.visual_rhythm)
            result = policy.validate("render-readiness", artifacts)
        else:
            if args.qc_report:
                artifacts["qc_report"] = load_json(args.qc_report)
            ffmpeg_log_text = args.ffmpeg_log.read_text(encoding="utf-8") if args.ffmpeg_log else ""
            result = policy.validate("qc", artifacts, ffmpeg_log_text=ffmpeg_log_text)
    except ValueError as exc:
        result = GateResult(ok=False, reasons=[str(exc)])

    print(json.dumps(result.payload(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
