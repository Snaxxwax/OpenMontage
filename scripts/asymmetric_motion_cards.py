#!/usr/bin/env python3
"""Generate motion-card MP4s from composed source-card PNGs via FFmpeg zoompan.

Reads visual_motion_plan.json, produces one MP4 per shot under assets/motion/,
and writes a QC report. Exits 0 if all shots pass, 1 if any fail.

Usage:
    python3 scripts/asymmetric_motion_cards.py \
        --manifest <project>/artifacts/visual_motion_plan.json \
        --output   <project>/qc/motion_cards_qc.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FPS = 30
OUTPUT_RESOLUTION = "1280x720"
CRF = 18
INPUT_PRESCALE_W = 4000  # upscale width before zoompan to give zoom headroom


class MotionError(RuntimeError):
    pass


def load_plan(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise MotionError(f"missing manifest: {manifest_path}")
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MotionError(f"invalid JSON in {manifest_path}: {exc}") from exc


def _safe_output_path(output_path_str: str) -> Path:
    if not output_path_str.startswith("assets/motion/"):
        raise MotionError(f"output_path must be under assets/motion/: {output_path_str!r}")
    if ".." in output_path_str:
        raise MotionError(f"output_path must not contain '..': {output_path_str!r}")
    return Path(output_path_str)


def _zoom_expr(motion_type: str, start_scale: float, end_scale: float, n_frames: int) -> str:
    if motion_type == "static":
        return "1"
    delta = (end_scale - start_scale) / max(n_frames - 1, 1)
    if motion_type == "push_in":
        clamp = f"min(pzoom+{delta:.8f},{end_scale:.6f})"
    else:  # pull_out
        clamp = f"max(pzoom+{delta:.8f},{end_scale:.6f})"
    return f"if(eq(on,1),{start_scale:.6f},{clamp})"


def render_shot(shot: dict, project_root: Path) -> None:
    shot_id = shot["shot_id"]
    motion_type = shot["motion_type"]
    duration = float(shot["duration_seconds"])
    n_frames = max(round(duration * FPS), 1)

    input_path = (project_root / shot["input_path"]).resolve()
    if not input_path.exists():
        raise MotionError(f"input not found: {shot['input_path']!r}")

    rel_out = _safe_output_path(shot["output_path"])
    output_path = (project_root / rel_out).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if motion_type == "push_in":
        start_scale = float(shot.get("start_scale", 1.0))
        end_scale = float(shot.get("end_scale", 1.04))
    elif motion_type == "pull_out":
        start_scale = float(shot.get("start_scale", 1.04))
        end_scale = float(shot.get("end_scale", 1.0))
    else:  # static
        start_scale = float(shot.get("start_scale", 1.0))
        end_scale = float(shot.get("end_scale", 1.0))

    z_expr = _zoom_expr(motion_type, start_scale, end_scale, n_frames)
    vf = (
        f"scale={INPUT_PRESCALE_W}:-1,"
        f"zoompan="
        f"z='{z_expr}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={n_frames}:"
        f"s={OUTPUT_RESOLUTION},"
        f"fps={FPS}"
    )
    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-framerate", str(FPS),
        "-t", f"{duration:.3f}",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(CRF),
        "-r", str(FPS),
        "-t", f"{duration:.3f}",
        "-y",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MotionError(
            f"FFmpeg failed for {shot_id!r}:\n{result.stderr[-1500:]}"
        )


def write_qc(
    output_path: Path,
    episode_id: str,
    rows: list[dict],
    failures: list[str],
) -> None:
    verdict = "FAIL" if failures else "PASS"
    checked_at = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Motion Cards QC - {episode_id}",
        "",
        f"**checked_at:** {checked_at}",
        f"**verdict:** {verdict}",
        "",
        "| shot_id | motion_type | output | duration_seconds | status |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['shot_id']} | {row['motion_type']} "
            f"| {row['output']} | {row['duration_seconds']} | {row['status']} |"
        )
    lines += ["", "## Failures"]
    lines += [f"- {f}" for f in failures] if failures else ["(none)"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(manifest_path: Path, qc_output: Path) -> int:
    try:
        plan = load_plan(manifest_path)
    except MotionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    project_root = manifest_path.parent.parent
    episode_id = plan.get("episode_id", "unknown")
    shots = plan.get("shots", [])

    rows: list[dict] = []
    failures: list[str] = []

    for shot in shots:
        shot_id = shot.get("shot_id", "?")
        motion_type = shot.get("motion_type", "?")
        duration = shot.get("duration_seconds", 0)
        output_rel = shot.get("output_path", "?")
        try:
            render_shot(shot, project_root)
            rows.append({
                "shot_id": shot_id,
                "motion_type": motion_type,
                "output": output_rel,
                "duration_seconds": duration,
                "status": "PASS",
            })
        except MotionError as exc:
            failures.append(f"{shot_id}: {exc}")
            rows.append({
                "shot_id": shot_id,
                "motion_type": motion_type,
                "output": output_rel,
                "duration_seconds": duration,
                "status": "FAIL",
            })

    write_qc(qc_output, episode_id, rows, failures)

    if failures:
        print(json.dumps({"ok": False, "failures": failures}))
        return 1

    print(json.dumps({"ok": True, "shots": len(rows), "qc": str(qc_output)}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate motion-card MP4s from composed source-card PNGs."
    )
    parser.add_argument("--manifest", required=True, help="Path to visual_motion_plan.json")
    parser.add_argument("--output", required=True, help="Path to write motion_cards_qc.md")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(run(Path(args.manifest), Path(args.output)))


if __name__ == "__main__":
    main()
