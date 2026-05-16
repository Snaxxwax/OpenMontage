#!/usr/bin/env python3
"""Compact hard gates for the Asymmetric source-commentary path."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
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
SCHEMA_DIR = REPO_ROOT / "schemas" / "artifacts"


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


# ── staging gate ──────────────────────────────────────────────────────────────

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_staged_schema() -> dict[str, Any]:
    return json.loads(
        (SCHEMA_DIR / "staged_asset_manifest.schema.json").read_text(encoding="utf-8")
    )


def _write_staging_qc_report(
    staging_root: Path,
    result: GateResult,
    manifest: dict[str, Any] | None,
) -> None:
    checked_at = datetime.now(timezone.utc).isoformat()
    render_id = manifest.get("render_id", "unknown") if manifest else "unknown"
    episode_id = manifest.get("episode_id", "unknown") if manifest else "unknown"
    status = "PASS" if result.ok else "FAIL"

    lines = [
        "# Staging Gate QC",
        "",
        f"**render_id:** `{render_id}`  ",
        f"**episode_id:** `{episode_id}`  ",
        f"**checked_at:** {checked_at}  ",
        f"**result:** {status}  ",
        "",
    ]

    if result.ok:
        lines += ["## All checks passed.", ""]
    else:
        lines += [f"## Failures ({len(result.reasons)})", ""]
        for reason in result.reasons:
            lines.append(f"- {reason}")
        lines.append("")

    (staging_root / "staged_asset_qc.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def run_staging_gate(manifest_path: Path) -> GateResult:
    """Validate staged assets. Writes staged_asset_qc.md. Updates gate_passed on success."""
    from jsonschema import Draft7Validator, ValidationError  # lazy import

    result = GateResult()
    staging_root = manifest_path.parent

    # Load manifest
    try:
        manifest: dict[str, Any] = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        result.fail(f"staged_asset_manifest.json not found: {manifest_path}")
        _write_staging_qc_report(staging_root, result, None)
        return result
    except json.JSONDecodeError as exc:
        result.fail(f"invalid JSON in manifest: {exc}")
        _write_staging_qc_report(staging_root, result, None)
        return result

    # Schema validation
    try:
        Draft7Validator(_load_staged_schema()).validate(manifest)
    except ValidationError as exc:
        result.fail(f"schema invalid: {exc.message}")
        _write_staging_qc_report(staging_root, result, manifest)
        return result

    assets: list[dict[str, Any]] = manifest["assets"]
    manifested_rel = {a["staged_path"] for a in assets}

    # staged_path traversal (defense in depth — schema pattern already rejects ..)
    for asset in assets:
        sp = asset["staged_path"]
        if ".." in Path(sp).parts:
            result.fail(f"[{asset['asset_id']}] staged_path traversal rejected: {sp!r}")

    # File existence, size, sha256
    for asset in assets:
        aid = asset["asset_id"]
        staged_file = staging_root / asset["staged_path"]
        if not staged_file.exists():
            result.fail(f"[{aid}] staged file not found: {asset['staged_path']}")
        elif staged_file.stat().st_size == 0:
            result.fail(f"[{aid}] zero-byte staged file: {asset['staged_path']}")
        else:
            actual_sha = _sha256_file(staged_file)
            if actual_sha != asset["sha256"]:
                result.fail(
                    f"[{aid}] sha256 mismatch: "
                    f"manifest={asset['sha256'][:12]}... actual={actual_sha[:12]}..."
                )

    # Orphan files (files on disk not in manifest)
    for subdir in ("media", "audio"):
        d = staging_root / subdir
        if d.is_dir():
            for f in sorted(d.rglob("*")):
                if f.is_file():
                    rel = str(f.relative_to(staging_root))
                    if rel not in manifested_rel:
                        result.fail(f"orphan file not in manifest: {rel}")

    # Source label content
    for asset in assets:
        if asset.get("source_label_required") and not asset.get("source_label"):
            result.fail(
                f"[{asset['asset_id']}] source_label_required=true but source_label missing"
            )

    # Type-specific business logic
    for asset in assets:
        aid = asset["asset_id"]
        atype = asset["asset_type"]

        if atype == "screenshot":
            dims = asset.get("dimensions") or {}
            if not isinstance(dims, dict) or dims.get("width", 0) <= 0 or dims.get("height", 0) <= 0:
                result.fail(
                    f"[{aid}] screenshot dimensions invalid or zero: {dims!r}"
                )

        elif atype == "video":
            dur = asset.get("duration_seconds", 0)
            out = asset.get("out_seconds", 0)
            if out > dur:
                result.fail(
                    f"[{aid}] out_seconds ({out}) > duration_seconds ({dur})"
                )

        # Narration loudness (schema enforces presence, gate enforces non-None value)
        if asset.get("role") == "narration" and asset.get("loudness_lufs") is None:
            result.fail(f"[{aid}] narration asset missing loudness_lufs")

    _write_staging_qc_report(staging_root, result, manifest)

    if result.ok:
        manifest["gate_passed"] = True
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

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

    staging = sub.add_parser(
        "render-asset-staging",
        help="Validate staged assets against staged_asset_manifest.json",
    )
    staging.add_argument(
        "--staging-manifest",
        type=Path,
        required=True,
        help="Path to staged_asset_manifest.json",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "render-asset-staging":
        result = run_staging_gate(args.staging_manifest)
        print(json.dumps(result.payload(), indent=2, sort_keys=True))
        return 0 if result.ok else 2

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
