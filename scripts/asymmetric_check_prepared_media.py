#!/usr/bin/env python3
"""Validate prepared_media_manifest.json before staging.

Checks that screenshots are cropped to readable dimensions, video timing
is consistent, and narration meets loudness/silence-gate requirements.

Always writes qc/prepared_media_qc.md. Exits 0 on pass, 1 on fail.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Rendered width at 1280x720 must be at or above this to be legible.
MIN_RENDERED_WIDTH = 640
RENDER_W, RENDER_H = 1280, 720


def _image_dimensions(path: Path) -> tuple[int, int]:
    """Return (width, height) using PIL. Returns (0, 0) on failure."""
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as img:
            return img.size  # (w, h)
    except Exception:
        return (0, 0)


def _rendered_width(w: int, h: int) -> float:
    if w <= 0 or h <= 0:
        return 0.0
    scale = min(RENDER_W / w, RENDER_H / h)
    return w * scale


def _check_screenshot(asset: dict[str, Any], manifest_dir: Path) -> list[str]:
    failures: list[str] = []
    asset_id = asset["asset_id"]

    input_path = asset.get("input_path", "")
    prepared_str = asset.get("prepared_path", "")

    prepared = Path(prepared_str)
    if not prepared.is_absolute():
        prepared = (manifest_dir / prepared).resolve()

    if not prepared.exists():
        failures.append(f"{asset_id}: prepared_path does not exist: {prepared_str}")
        return failures

    if prepared.stat().st_size == 0:
        failures.append(f"{asset_id}: prepared_path is zero bytes: {prepared_str}")
        return failures

    if str(prepared) == str((manifest_dir / input_path).resolve() if not Path(input_path).is_absolute() else Path(input_path)):
        failures.append(f"{asset_id}: prepared_path == input_path — crop required for screenshots")

    w, h = _image_dimensions(prepared)
    if w == 0 or h == 0:
        failures.append(f"{asset_id}: could not read dimensions from prepared_path")
        return failures

    rw = _rendered_width(w, h)
    if rw < MIN_RENDERED_WIDTH:
        failures.append(
            f"{asset_id}: rendered width {rw:.0f}px < {MIN_RENDERED_WIDTH}px threshold "
            f"(source {w}x{h} — crop to landscape/square aspect)"
        )

    if not asset.get("legibility_ok"):
        failures.append(f"{asset_id}: legibility_ok is not true")

    return failures


def _check_video(asset: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    asset_id = asset["asset_id"]

    in_s = asset.get("in_seconds")
    out_s = asset.get("out_seconds")
    dur = asset.get("duration_seconds")

    if dur is None or dur <= 0:
        failures.append(f"{asset_id}: duration_seconds must be > 0")
    if in_s is None or out_s is None:
        failures.append(f"{asset_id}: in_seconds and out_seconds required")
        return failures
    if in_s >= out_s:
        failures.append(f"{asset_id}: in_seconds ({in_s}) must be < out_seconds ({out_s})")
    if dur is not None and out_s > dur:
        failures.append(f"{asset_id}: out_seconds ({out_s}) > duration_seconds ({dur})")

    return failures


def _check_audio(asset: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    asset_id = asset["asset_id"]

    dur = asset.get("duration_seconds")
    if dur is None or dur <= 0:
        failures.append(f"{asset_id}: duration_seconds must be > 0")

    if not asset.get("audio_role"):
        failures.append(f"{asset_id}: audio_role is required")

    if asset.get("role") == "narration":
        if asset.get("loudness_lufs") is None:
            failures.append(f"{asset_id}: loudness_lufs required for narration")
        if asset.get("silence_gate_passed") is not True:
            failures.append(f"{asset_id}: silence_gate_passed must be true for narration")

    return failures


def _prepared_summary(asset: dict[str, Any], manifest_dir: Path) -> str:
    """One-line prepared column for the report table."""
    media_type = asset.get("media_type")
    if media_type == "screenshot":
        prepared_str = asset.get("prepared_path", "")
        prepared = Path(prepared_str)
        if not prepared.is_absolute():
            prepared = (manifest_dir / prepared).resolve()
        if prepared.exists():
            w, h = _image_dimensions(prepared)
            return f"{w}x{h}" if w else "unreadable"
        return "missing"
    if media_type == "video":
        in_s = asset.get("in_seconds", "?")
        out_s = asset.get("out_seconds", "?")
        dur = asset.get("duration_seconds", "?")
        return f"{in_s}–{out_s}s of {dur}s"
    if media_type == "audio":
        dur = asset.get("duration_seconds", "?")
        lufs = asset.get("loudness_lufs", "?")
        return f"{dur}s / {lufs} LUFS"
    return "—"


def _rendered_width_str(asset: dict[str, Any], manifest_dir: Path) -> str:
    if asset.get("media_type") != "screenshot":
        return "—"
    prepared_str = asset.get("prepared_path", "")
    prepared = Path(prepared_str)
    if not prepared.is_absolute():
        prepared = (manifest_dir / prepared).resolve()
    if not prepared.exists():
        return "missing"
    w, h = _image_dimensions(prepared)
    if w == 0:
        return "unreadable"
    return f"{_rendered_width(w, h):.0f}px"


def check_prepared_media(
    manifest: dict[str, Any],
    manifest_dir: Path,
    output_path: Path,
) -> int:
    """Check all assets. Always writes output_path. Returns 0 (pass) or 1 (fail)."""
    episode_id = manifest.get("episode_id", "unknown")
    assets = manifest.get("assets", [])
    checked_at = datetime.now(timezone.utc).isoformat()

    all_failures: list[str] = []
    rows: list[tuple[str, str, str, str, str]] = []  # id, type, prepared, rw, status

    for asset in assets:
        media_type = asset.get("media_type", "unknown")
        asset_id = asset.get("asset_id", "?")

        if media_type == "screenshot":
            failures = _check_screenshot(asset, manifest_dir)
        elif media_type == "video":
            failures = _check_video(asset)
        elif media_type == "audio":
            failures = _check_audio(asset)
        else:
            failures = [f"{asset_id}: unknown media_type '{media_type}'"]

        all_failures.extend(failures)
        status = "FAIL" if failures else "PASS"
        prepared = _prepared_summary(asset, manifest_dir)
        rw = _rendered_width_str(asset, manifest_dir)
        rows.append((asset_id, media_type, prepared, rw, status))

    overall = "PASS" if not all_failures else "FAIL"

    lines = [
        f"# Prepared Media QC — {episode_id}",
        "",
        f"**checked_at:** {checked_at}  ",
        f"**verdict:** {overall}  ",
        "",
        "| asset_id | type | prepared | rendered_width | status |",
        "|---|---|---|---|---|",
    ]
    for asset_id, media_type, prepared, rw, status in rows:
        lines.append(f"| {asset_id} | {media_type} | {prepared} | {rw} | {status} |")

    lines += ["", "## Failures"]
    if all_failures:
        for f in all_failures:
            lines.append(f"- {f}")
    else:
        lines.append("(none)")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0 if not all_failures else 1


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate prepared_media_manifest.json before staging."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = _load_json(args.manifest)
    return check_prepared_media(
        manifest=manifest,
        manifest_dir=args.manifest.resolve().parent,
        output_path=args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
