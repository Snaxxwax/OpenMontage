#!/usr/bin/env python3
"""Preprocess source video excerpts into Remotion-safe static assets.

This is a narrow deterministic utility: it does not choose sources, decide fair use,
or route pipeline stages. It reads an explicit source_assets JSON artifact, converts
video_clip assets into video-only H.264 files under remotion-composer/public/, emits
poster frames, and enriches the artifact with render_src/poster_src/preprocessed
metadata for the agent/renderer to consume.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


@dataclass(frozen=True)
class PreprocessJob:
    asset_id: str
    input_path: Path
    output_path: Path
    poster_path: Path
    ffmpeg_command: list[str]
    poster_command: list[str]


def _repo_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _resolve_repo_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / value


def public_render_path(root: Path, local_path: str) -> Path:
    """Return the deterministic public H.264 path for a source clip."""
    source = Path(local_path)
    stem = f"{source.stem}_remotion_h264.mp4"
    return root / "remotion-composer" / "public" / source.with_name(stem)


def public_poster_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_poster.jpg")


def public_static_src(root: Path, public_path: Path) -> str:
    public_root = root / "remotion-composer" / "public"
    return public_path.resolve().relative_to(public_root.resolve()).as_posix()


def build_ffmpeg_command(input_path: Path, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        "scale='min(1280,iw)':-2,fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def build_poster_command(output_path: Path, poster_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "0.2",
        "-i",
        str(output_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(poster_path),
    ]


def _is_video_clip(asset: dict[str, Any]) -> bool:
    if asset.get("asset_type") != "video_clip":
        return False
    local_path = str(asset.get("local_path") or asset.get("absolute_path") or "")
    return Path(local_path).suffix.lower() in VIDEO_EXTENSIONS


def enrich_source_assets(root: Path, source_assets_path: Path, execute: bool = False) -> tuple[dict[str, Any], list[PreprocessJob]]:
    payload = json.loads(source_assets_path.read_text(encoding="utf-8"))
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ValueError(f"{source_assets_path} must contain an assets list")

    jobs: list[PreprocessJob] = []
    for asset in assets:
        if not isinstance(asset, dict) or not _is_video_clip(asset):
            continue
        local_path = str(asset.get("local_path") or asset.get("absolute_path"))
        input_path = _resolve_repo_path(root, local_path)
        output_path = public_render_path(root, local_path)
        poster_path = public_poster_path(output_path)
        job = PreprocessJob(
            asset_id=str(asset.get("asset_id")),
            input_path=input_path,
            output_path=output_path,
            poster_path=poster_path,
            ffmpeg_command=build_ffmpeg_command(input_path, output_path),
            poster_command=build_poster_command(output_path, poster_path),
        )
        jobs.append(job)

        asset["absolute_path"] = _repo_relative(input_path, root) if input_path.is_absolute() and input_path.is_relative_to(root) else str(input_path)
        asset["render_src"] = public_static_src(root, output_path)
        asset["poster_src"] = public_static_src(root, poster_path)
        asset["preprocessed"] = {
            "remotion_safe": True,
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "fps": 30,
            "max_width": 1280,
            "audio": "stripped_for_narration_mix",
            "source_path": local_path,
            "output_path": asset["render_src"],
            "poster_path": asset["poster_src"],
        }

        if execute:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(job.ffmpeg_command, check=True)
            subprocess.run(job.poster_command, check=True)

    payload["motion_capable_asset_count"] = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("asset_type") == "video_clip")
    payload["preprocessing"] = {
        "remotion_safe_video": True,
        "strategy": "video_only_h264_yuv420p_30fps_public_static_asset",
        "job_count": len(jobs),
    }
    return payload, jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess source video clips for Remotion source_sequence playback")
    parser.add_argument("source_assets", type=Path, help="Path to source_assets.json")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="Write enriched source_assets JSON in place")
    parser.add_argument("--execute", action="store_true", help="Run ffmpeg/poster jobs")
    parser.add_argument("--output", type=Path, help="Write enriched JSON to this path instead of stdout/in-place")
    args = parser.parse_args()

    enriched, jobs = enrich_source_assets(args.repo_root, args.source_assets, execute=args.execute)

    if args.write:
        args.source_assets.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")
    if not args.write and not args.output:
        print(json.dumps(enriched, indent=2))
    print(f"SOURCE_CLIP_PREPROCESS_{'EXECUTED' if args.execute else 'PLAN'} jobs={len(jobs)}")
    for job in jobs:
        print(f"{job.asset_id}\t{job.input_path}\t{job.output_path}\t{job.poster_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
