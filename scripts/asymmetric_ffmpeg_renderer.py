#!/usr/bin/env python3
"""Deterministic FFmpeg source/proof smoke renderer for Asymmetric runs."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from lib.artifact_bus import ArtifactBus, DEFAULT_PROJECTS_DIR
from lib.source_proof import SourceProofManifest, load_optional_source_proof_manifest

DEFAULT_RUN_BASE_DIR = DEFAULT_PROJECTS_DIR
ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".ppm")
SOURCE_PROOF_EVENTS = {"source", "proof"}


class RenderError(RuntimeError):
    """Expected operator-facing renderer failure."""


@dataclass(frozen=True)
class RenderSegment:
    segment_id: str
    event_type: str
    starts_at_seconds: float
    duration_seconds: float
    source_label: str
    asset_path: Path


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenderError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RenderError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RenderError(f"JSON file must contain an object: {path}")
    return data


def ffmpeg_filter_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def shell_join(cmd: list[str]) -> str:
    return " ".join(cmd)


def run_cmd(cmd: list[str], *, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "$ " + shell_join(cmd) + "\n\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
            encoding="utf-8",
        )
    if proc.returncode != 0:
        raise RenderError(f"Command failed ({proc.returncode}): {shell_join(cmd)}\n{proc.stderr.strip()}")
    return proc


def ffprobe_duration(path: Path) -> float:
    proc = run_cmd(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        duration = float(proc.stdout.strip())
    except ValueError as exc:
        raise RenderError(f"Could not parse duration for {path}: {proc.stdout!r}") from exc
    if duration <= 0:
        raise RenderError(f"render duration must be > 0 for {path}; got {duration}")
    return duration


def approved_source_proof_segments(visual_rhythm: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for raw in visual_rhythm.get("segments") or []:
        if not isinstance(raw, dict):
            continue
        if raw.get("approved") is True and raw.get("event_type") in SOURCE_PROOF_EVENTS:
            segments.append(raw)
    return sorted(segments, key=lambda item: float(item.get("starts_at_seconds", 0)))


def validate_source_labels(segments: list[dict[str, Any]]) -> None:
    missing = []
    for segment in segments:
        label = segment.get("source_label")
        if segment.get("source_label_present") is not True or not isinstance(label, str) or not label.strip():
            missing.append(str(segment.get("id", "<unknown>")))
    if missing:
        raise RenderError(
            "approved source/proof segments require source_label_present=true and source_label: "
            + ", ".join(missing)
        )


def asset_candidates(segment: dict[str, Any], assets_dir: Path) -> list[Path]:
    names = [str(segment.get("id", ""))]
    names.extend(str(item) for item in segment.get("evidence_ids") or [])
    candidates: list[Path] = []
    for name in names:
        if not name:
            continue
        for stem in (name, f"source_card_{name}"):
            candidates.extend(assets_dir / f"{stem}{suffix}" for suffix in ASSET_SUFFIXES)
    return candidates


def resolve_asset(
    segment: dict[str, Any],
    assets_dir: Path,
    source_proof_manifest: SourceProofManifest | None = None,
) -> Path:
    if source_proof_manifest is not None:
        asset = source_proof_manifest.resolve_asset_for_segment(segment)
        if asset is not None:
            return asset
    for candidate in asset_candidates(segment, assets_dir):
        if candidate.is_file():
            return candidate
    raise RenderError(
        "missing source-card asset for approved segment "
        f"{segment.get('id', '<unknown>')} in {assets_dir}; expected segment id or evidence id image"
    )


def build_render_segments(
    visual_rhythm: dict[str, Any],
    assets_dir: Path,
    *,
    default_tail_seconds: float = 4.0,
    source_proof_manifest: SourceProofManifest | None = None,
) -> list[RenderSegment]:
    raw_segments = approved_source_proof_segments(visual_rhythm)
    if not raw_segments:
        raise RenderError("visual_rhythm_plan.json has no approved source/proof segments to render")
    validate_source_labels(raw_segments)

    render_segments: list[RenderSegment] = []
    for index, segment in enumerate(raw_segments):
        start = float(segment.get("starts_at_seconds", 0))
        next_start = (
            float(raw_segments[index + 1].get("starts_at_seconds", start + default_tail_seconds))
            if index + 1 < len(raw_segments)
            else start + default_tail_seconds
        )
        duration = max(next_start - start, 1.0)
        render_segments.append(
            RenderSegment(
                segment_id=str(segment["id"]),
                event_type=str(segment["event_type"]),
                starts_at_seconds=start,
                duration_seconds=duration,
                source_label=str(segment["source_label"]).strip(),
                asset_path=resolve_asset(segment, assets_dir, source_proof_manifest),
            )
        )
    return render_segments


def write_textfile(path: Path, text: str) -> None:
    path.write_text(text.replace("\n", " ").strip() + "\n", encoding="utf-8")


def build_filter_complex(segments: list[RenderSegment], label_dir: Path) -> str:
    chains: list[str] = []
    labels: list[str] = []
    for index, segment in enumerate(segments):
        source_label_path = label_dir / f"{index:03d}_source_label.txt"
        proof_label_path = label_dir / f"{index:03d}_proof_label.txt"
        write_textfile(source_label_path, f"{segment.event_type.upper()} | {segment.source_label}")
        write_textfile(proof_label_path, f"{segment.segment_id} | burned-in source/proof label")
        source_label = ffmpeg_filter_escape(str(source_label_path))
        proof_label = ffmpeg_filter_escape(str(proof_label_path))
        out_label = f"v{index}"
        chains.append(
            f"[{index}:v]"
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x111111,"
            "setsar=1,format=yuv420p,"
            "drawbox=x=0:y=ih-132:w=iw:h=132:color=black@0.72:t=fill,"
            f"drawtext=textfile='{source_label}':fontcolor=white:fontsize=34:x=42:y=main_h-108,"
            f"drawtext=textfile='{proof_label}':fontcolor=0xffd35a:fontsize=24:x=42:y=main_h-58"
            f"[{out_label}]"
        )
        labels.append(f"[{out_label}]")
    chains.append("".join(labels) + f"concat=n={len(segments)}:v=1:a=0[v]")
    return ";".join(chains)


def render_episode(
    *,
    run_dir: Path,
    episode_id: str | None = None,
    overwrite: bool = False,
    output_name: str | None = None,
) -> dict[str, Any]:
    bus = ArtifactBus(root=run_dir)
    artifact_path = bus.artifacts / "visual_rhythm_plan.json"
    assets_dir = bus.assets
    renders_dir = bus.renders
    logs_dir = bus.logs

    visual_rhythm = load_json(artifact_path)
    resolved_episode_id = episode_id or str(visual_rhythm.get("episode") or run_dir.name)
    source_proof_manifest = load_optional_source_proof_manifest(assets_dir)
    segments = build_render_segments(
        visual_rhythm,
        assets_dir,
        source_proof_manifest=source_proof_manifest,
    )
    bus.ensure_dirs()

    output = renders_dir / (output_name or f"{resolved_episode_id}_source_proof_smoke.mp4")
    if output.exists() and not overwrite:
        raise RenderError(f"render already exists; pass --overwrite: {output}")
    if not shutil.which("ffmpeg"):
        raise RenderError("ffmpeg not found on PATH")
    if not shutil.which("ffprobe"):
        raise RenderError("ffprobe not found on PATH")

    total_duration = sum(segment.duration_seconds for segment in segments)
    with tempfile.TemporaryDirectory(prefix="asymmetric_render_labels_") as tmp:
        label_dir = Path(tmp)
        cmd = ["ffmpeg", "-y" if overwrite else "-n"]
        for segment in segments:
            cmd.extend(["-loop", "1", "-t", f"{segment.duration_seconds:.3f}", "-i", str(segment.asset_path)])
        cmd.extend(["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={total_duration:.3f}"])
        cmd.extend(
            [
                "-filter_complex",
                build_filter_complex(segments, label_dir),
                "-map",
                "[v]",
                "-map",
                f"{len(segments)}:a",
                "-r",
                "30",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                "-shortest",
                str(output),
            ]
        )
        run_cmd(cmd, log_path=logs_dir / "ffmpeg_source_proof_smoke.log")

    duration = ffprobe_duration(output)
    return {
        "ok": True,
        "episode_id": resolved_episode_id,
        "render": str(output),
        "duration_seconds": duration,
        "segments": [
            {
                "id": segment.segment_id,
                "event_type": segment.event_type,
                "source_label": segment.source_label,
                "asset": str(segment.asset_path),
                "duration_seconds": segment.duration_seconds,
            }
            for segment in segments
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an Asymmetric source/proof FFmpeg smoke MP4")
    parser.add_argument("--run-base-dir", type=Path, default=DEFAULT_RUN_BASE_DIR)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = render_episode(
            run_dir=args.run_base_dir / args.episode_id,
            episode_id=args.episode_id,
            overwrite=args.overwrite,
            output_name=args.output_name,
        )
        print_json(result)
        return 0
    except RenderError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
