#!/usr/bin/env python3
"""Benchmark Modern Archivist Remotion renders through the official video_compose route.

This is a deterministic render utility, not a pipeline orchestrator: the caller
must provide explicit props/edit-decisions and output paths. The script records
runtime facts so CSS/audio/public-dir changes can be compared with evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.video.video_compose import VideoCompose  # noqa: E402


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def _human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _package_versions() -> dict[str, str | None]:
    package = _read_json(REPO_ROOT / "remotion-composer" / "package.json")
    deps = package.get("dependencies", {}) or {}
    return {
        "remotion": deps.get("remotion"),
        "@remotion/cli": deps.get("@remotion/cli"),
        "package": package.get("version"),
    }


def _git_sha() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return proc.stdout.strip()
    except Exception:
        return None


def _ffprobe(path: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        data = json.loads(proc.stdout or "{}")
        streams = data.get("streams", []) or []
        return {
            "ok": True,
            "duration_seconds": float((data.get("format") or {}).get("duration") or 0),
            "streams": [
                {
                    "codec_type": s.get("codec_type"),
                    "codec_name": s.get("codec_name"),
                    "width": s.get("width"),
                    "height": s.get("height"),
                    "sample_rate": s.get("sample_rate"),
                }
                for s in streams
            ],
            "has_video": any(s.get("codec_type") == "video" for s in streams),
            "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


VARIANT_PATCHES: dict[str, dict[str, Any]] = {
    "baseline":          {},
    "muted":             {},
    "no-backdrop":       {"debug_disable_backdrop": True},
    "no-puppet":         {"debug_disable_puppet": True},
    "no-media":          {"debug_disable_media": True},
    "no-audio":          {"debug_disable_audio": True},
    # puppet sub-path profiling variants
    "puppet-static":     {"debug_puppet_static": True},
    "puppet-no-filters": {"debug_disable_puppet_filters": True},
    "puppet-no-mouth":   {"debug_disable_puppet_mouth": True},
    "source-plate-only": {"debug_disable_puppet": True, "debug_disable_audio": True},
    "final-overlay":     {},
}


def _apply_variant(edit_decisions: dict[str, Any], variant: str) -> tuple[dict[str, Any], dict[str, Any]]:
    props = json.loads(json.dumps(edit_decisions))
    options: dict[str, Any] = {}
    if variant not in VARIANT_PATCHES:
        raise ValueError(f"Unknown variant {variant!r}")
    props.update(VARIANT_PATCHES[variant])
    if variant == "muted":
        options["muted"] = True
    if variant in ("no-audio", "source-plate-only"):
        options["muted"] = True
    return props, options


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--props", required=True, type=Path, help="Explicit Modern Archivist edit_decisions/render props JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output MP4 path")
    parser.add_argument("--asset-manifest", type=Path, help="Optional asset_manifest JSON; defaults to empty assets")
    parser.add_argument("--audio-path", type=Path, help="Optional current project narration audio path")
    parser.add_argument("--concurrency", type=int, default=0, help="Optional bounded Remotion concurrency")
    parser.add_argument("--port", type=int, default=0, help="Optional explicit Remotion dev-server port")
    parser.add_argument(
        "--variant",
        choices=[
            "baseline", "muted", "no-backdrop", "no-puppet", "no-media", "no-audio",
            "puppet-static", "puppet-no-filters", "puppet-no-mouth",
            "source-plate-only", "final-overlay",
        ],
        default="baseline",
    )
    parser.add_argument("--mode", choices=["final", "preview"], default="final")
    parser.add_argument("--report", type=Path, help="JSON report path; defaults beside output")
    args = parser.parse_args()

    edit_decisions = _read_json(args.props)
    if edit_decisions.get("render_runtime") != "remotion":
        raise SystemExit("props must explicitly set render_runtime='remotion'")
    if edit_decisions.get("renderer_family") != "modern-archivist":
        raise SystemExit("props must explicitly set renderer_family='modern-archivist'")

    asset_manifest = _read_json(args.asset_manifest) if args.asset_manifest else {"assets": []}
    variant_props, variant_options = _apply_variant(edit_decisions, args.variant)
    if args.concurrency > 0:
        variant_options["concurrency"] = args.concurrency
    if args.port > 0:
        variant_options["port"] = args.port
    if args.mode == "preview":
        variant_options.setdefault("muted", True)

    inputs: dict[str, Any] = {
        "operation": "render",
        "edit_decisions": variant_props,
        "asset_manifest": asset_manifest,
        "output_path": str(args.output),
        "options": variant_options,
        "proposal_packet": {"production_plan": {"render_runtime": "remotion"}},
    }
    if args.audio_path:
        inputs["narration_audio_path"] = str(args.audio_path)

    public_dir = REPO_ROOT / "remotion-composer" / "public"
    started = time.perf_counter()
    result = VideoCompose().execute(inputs)
    elapsed = time.perf_counter() - started

    probe = _ffprobe(args.output) if args.output.exists() else {"ok": False, "error": "output missing"}
    duration = float(probe.get("duration_seconds") or 0)
    measured_fps = duration * 30 / elapsed if elapsed > 0 and duration > 0 else None

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "props": str(args.props.resolve()),
        "output": str(args.output.resolve()),
        "variant": args.variant,
        "mode": args.mode,
        "success": result.success,
        "error": result.error,
        "operation": (result.data or {}).get("operation") if result.data else None,
        "wall_clock_seconds": round(elapsed, 3),
        "rendered_duration_seconds": duration,
        "approx_render_fps_at_30fps": round(measured_fps, 3) if measured_fps else None,
        "audio_enabled": not bool(variant_options.get("muted")) and not bool(variant_props.get("debug_disable_audio")),
        "options": variant_options,
        "public_dir_size_bytes": _dir_size_bytes(public_dir),
        "public_dir_size_human": _human_bytes(_dir_size_bytes(public_dir)),
        "ffprobe": probe,
        "git_sha": _git_sha(),
        "remotion_versions": _package_versions(),
    }

    report_path = args.report or args.output.with_suffix(".bench.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result.success and probe.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
