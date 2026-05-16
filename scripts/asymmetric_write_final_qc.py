#!/usr/bin/env python3
"""Write qc/final_qc.md from pipeline JSON artifacts.

Always writes the file. Exits 0 on QC pass, nonzero on QC fail.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_final_qc(
    render_report: dict[str, Any],
    qc_report: dict[str, Any],
    staged_manifest: dict[str, Any],
    approved_clips: dict[str, Any],
    output_path: Path,
) -> int:
    """Assemble and write final_qc.md. Returns 0 (pass) or 1 (fail).

    Always writes the file before returning — even on failure.
    """
    episode_id = qc_report.get("project_id") or render_report.get("project_id", "unknown")
    render_id = staged_manifest.get("render_id", "unknown")
    render_path = render_report.get("render_path", "unknown")
    duration = render_report.get("duration_seconds", 0)
    resolution = render_report.get("resolution", "unknown")
    fps = render_report.get("fps", 0)
    checked_at = datetime.now(timezone.utc).isoformat()

    gate_passed = staged_manifest.get("gate_passed", False)
    assets = staged_manifest.get("assets", [])

    qc_passed = qc_report.get("qc_passed", False)
    traceability = qc_report.get("claim_traceability_passed", False)
    labels_visible = qc_report.get("source_labels_visible", False)
    audio_ok = qc_report.get("audio_mix_passed", False)
    failures = qc_report.get("failures", [])

    overall_pass = gate_passed and qc_passed
    verdict = "PASS" if overall_pass else "FAIL"

    lines = [
        f"# Final QC — {episode_id}",
        "",
        f"**render_id:** `{render_id}`  ",
        f"**render_path:** `{render_path}`  ",
        f"**duration:** {duration}s  ",
        f"**resolution:** {resolution}  ",
        f"**fps:** {fps}  ",
        f"**checked_at:** {checked_at}  ",
        f"**verdict:** {verdict}  ",
        "",
        "## Staging Gate",
        f"- gate_passed: {str(gate_passed).lower()}",
        f"- assets staged: {len(assets)}",
        "",
        "## Source Label Audit",
    ]

    clips = approved_clips.get("approved_clips", [])
    if clips:
        for clip in clips:
            rid = clip.get("receipt_id") or clip.get("asset_id", "?")
            if clip.get("source_label_required"):
                label = clip.get("source_label_text", "").strip()
                mark = "✓" if label else "✗ MISSING"
                lines.append(f'- {rid}: "{label}" {mark}')
            else:
                lines.append(f"- {rid}: source_label_required=false —")
    else:
        lines.append("- (no approved clips)")

    lines += [
        "",
        "## QC Report",
        f"- qc_passed: {str(qc_passed).lower()}",
        f"- claim_traceability_passed: {str(traceability).lower()}",
        f"- source_labels_visible: {str(labels_visible).lower()}",
        f"- audio_mix_passed: {str(audio_ok).lower()}",
        "",
        "## Failures",
    ]

    if failures:
        for f in failures:
            lines.append(f"- {f}")
    elif not overall_pass:
        if not gate_passed:
            lines.append("- staging gate_passed is false")
        if not qc_passed:
            lines.append("- qc_passed is false")
    else:
        lines.append("(none)")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0 if overall_pass else 1


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write qc/final_qc.md from pipeline JSON artifacts."
    )
    parser.add_argument("--render-report", type=Path, required=True)
    parser.add_argument("--qc-report", type=Path, required=True)
    parser.add_argument("--staged-manifest", type=Path, required=True)
    parser.add_argument("--approved-clips", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    return write_final_qc(
        render_report=_load_json(args.render_report),
        qc_report=_load_json(args.qc_report),
        staged_manifest=_load_json(args.staged_manifest),
        approved_clips=_load_json(args.approved_clips),
        output_path=args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
