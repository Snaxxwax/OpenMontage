#!/usr/bin/env python3
"""Stage prepared assets into staging/<render_id>/ for a render pass.

Reads prepared_media_manifest.json, copies each prepared asset into a clean
staging directory, computes sha256, and writes staged_asset_manifest.json
(gate_passed: false) plus staged_asset_qc.md.

The renderer reads only staged_asset_manifest.json. Raw asset paths never
reach the renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class StagingError(RuntimeError):
    """Operator-facing staging failure."""


# ── path helpers ──────────────────────────────────────────────────────────────

def _check_no_traversal(path_str: str) -> None:
    if ".." in Path(path_str).parts:
        raise StagingError(f"path traversal rejected: {path_str!r}")


def _dest_subdir(media_type: str) -> str:
    return "audio" if media_type == "audio" else "media"


def _staged_filename(asset_id: str, src_suffix: str) -> str:
    safe_id = re.sub(r"[^\w-]", "_", asset_id.lower()).strip("_-") or "asset"
    return f"{safe_id}{src_suffix}"


def _validate_render_id(render_id: str) -> None:
    if not RENDER_ID_RE.match(render_id):
        raise StagingError(
            f"render_id {render_id!r} must match ^[a-z0-9][a-z0-9_-]*$"
        )


def _auto_render_id(episode_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe = re.sub(r"[^a-z0-9]", "-", episode_id.lower()).strip("-") or "ep"
    return f"{safe}-{ts}"


# ── file ops ──────────────────────────────────────────────────────────────────

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe_image_dimensions(path: Path) -> dict[str, int]:
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as img:
            w, h = img.size
        return {"width": w, "height": h}
    except Exception:
        return {"width": 0, "height": 0}


# ── per-asset staging ─────────────────────────────────────────────────────────

def stage_asset(asset: dict[str, Any], staging_root: Path, manifest_dir: Path) -> dict[str, Any]:
    """Copy one prepared asset into staging_root, return the staged asset record."""
    asset_id = asset["asset_id"]
    prepared_str = asset["prepared_path"]

    _check_no_traversal(prepared_str)

    src = Path(prepared_str)
    if not src.is_absolute():
        src = manifest_dir / src
    src = src.resolve()

    if not src.exists():
        raise StagingError(f"[{asset_id}] prepared_path not found: {src}")
    if src.stat().st_size == 0:
        raise StagingError(f"[{asset_id}] zero-byte file rejected: {src}")

    media_type = asset["media_type"]
    subdir = _dest_subdir(media_type)
    dest_dir = staging_root / subdir
    dest_dir.mkdir(exist_ok=True)

    filename = _staged_filename(asset_id, src.suffix)
    dest = dest_dir / filename
    shutil.copy2(src, dest)

    sha = _sha256_file(dest)
    staged_path = f"{subdir}/{filename}"

    staged: dict[str, Any] = {
        "asset_id": asset_id,
        "asset_type": media_type,
        "role": asset["role"],
        "source_path": str(src),
        "staged_path": staged_path,
        "sha256": sha,
        "source_label_required": asset["source_label_required"],
        "qc_status": "pending",
    }

    if asset.get("source_label"):
        staged["source_label"] = asset["source_label"]

    if media_type == "screenshot":
        staged["dimensions"] = _probe_image_dimensions(dest)
    elif media_type == "video":
        staged["in_seconds"] = asset.get("in_seconds", 0.0)
        staged["out_seconds"] = asset.get("out_seconds", 0.0)
        staged["duration_seconds"] = asset.get("duration_seconds", 0.0)
        staged["audio_role"] = asset.get("audio_role", "")
    elif media_type == "audio":
        staged["duration_seconds"] = asset.get("duration_seconds", 0.0)
        staged["audio_role"] = asset.get("audio_role", "")

    # narration loudness carried forward if present in prepared manifest
    if asset.get("role") == "narration" and asset.get("loudness_lufs") is not None:
        staged["loudness_lufs"] = asset["loudness_lufs"]

    return staged


# ── top-level orchestrator ────────────────────────────────────────────────────

def stage_assets(
    manifest_path: Path,
    staging_base: Path,
    render_id: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Stage all assets from manifest_path into staging_base/render_id/.

    Returns a result dict with keys: staging_root, render_id, asset_count, manifest_out.
    Raises StagingError on any failure.
    """
    _validate_render_id(render_id)

    manifest_path = manifest_path.resolve()
    manifest_dir = manifest_path.parent

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise StagingError(f"manifest not found: {manifest_path}")
    except json.JSONDecodeError as exc:
        raise StagingError(f"invalid JSON in manifest: {exc}")

    if not manifest.get("operator_approved_for_staging"):
        raise StagingError("operator_approved_for_staging is false — refusing to stage")

    staging_root = staging_base / render_id
    if staging_root.exists():
        if not overwrite:
            raise StagingError(
                f"staging dir already exists: {staging_root}\n"
                "Pass --overwrite to replace it."
            )
        shutil.rmtree(staging_root)

    staging_root.mkdir(parents=True)

    errors: list[str] = []
    staged_assets: list[dict[str, Any]] = []

    for asset in manifest.get("assets", []):
        try:
            staged_assets.append(stage_asset(asset, staging_root, manifest_dir))
        except StagingError as exc:
            errors.append(str(exc))

    if errors:
        shutil.rmtree(staging_root)
        raise StagingError("staging failed:\n" + "\n".join(f"  {e}" for e in errors))

    now = datetime.now(timezone.utc).isoformat()

    manifest_out: dict[str, Any] = {
        "render_id": render_id,
        "episode_id": manifest["episode_id"],
        "staged_at": now,
        "gate_passed": False,
        "assets": staged_assets,
    }
    (staging_root / "staged_asset_manifest.json").write_text(
        json.dumps(manifest_out, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    _write_qc_report(staging_root, manifest_out)

    return {
        "staging_root": staging_root,
        "render_id": render_id,
        "asset_count": len(staged_assets),
        "manifest_out": manifest_out,
    }


def _write_qc_report(staging_root: Path, manifest_out: dict[str, Any]) -> None:
    render_id = manifest_out["render_id"]
    episode_id = manifest_out["episode_id"]
    staged_at = manifest_out["staged_at"]
    assets = manifest_out["assets"]

    lines = [
        "# Staged Asset QC",
        "",
        f"**render_id:** `{render_id}`  ",
        f"**episode_id:** `{episode_id}`  ",
        f"**staged_at:** {staged_at}  ",
        "**gate_passed:** false  ",
        "",
        f"## Assets ({len(assets)})",
        "",
    ]
    for a in assets:
        sha_preview = a["sha256"][:16]
        lines += [
            f"### {a['asset_id']}",
            f"- type: {a['asset_type']}",
            f"- role: {a['role']}",
            f"- staged_path: `{a['staged_path']}`",
            f"- sha256: `{sha_preview}...`",
            f"- qc_status: {a['qc_status']}",
            "",
        ]

    (staging_root / "staged_asset_qc.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage prepared assets for a render pass."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to prepared_media_manifest.json",
    )
    parser.add_argument(
        "--staging-dir",
        default="staging",
        help="Base staging directory (default: staging/)",
    )
    parser.add_argument(
        "--render-id",
        help="Render ID (auto-generated if omitted)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing staging dir",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    staging_base = Path(args.staging_dir)

    if args.render_id:
        render_id = args.render_id
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            render_id = _auto_render_id(manifest.get("episode_id", "ep"))
        except Exception:
            render_id = _auto_render_id("ep")

    try:
        result = stage_assets(manifest_path, staging_base, render_id, args.overwrite)
    except StagingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Staged {result['asset_count']} asset(s) → {result['staging_root']}")
    print(f"  staged_asset_manifest.json  gate_passed=false")
    print(f"  staged_asset_qc.md")


if __name__ == "__main__":
    main()
