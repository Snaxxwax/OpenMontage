#!/usr/bin/env python3
"""Render fresh retention-motion previews from canonical Asymmetric artifacts."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROJECT = Path("projects/chip-factory-runs-world-v2")
ARTIFACTS = PROJECT / "artifacts"
OUT_DIR = PROJECT / "renders" / "previews_retention_fresh"
WORK_DIR = OUT_DIR / "_work"
WIDTH = 1920
HEIGHT = 1080
FPS = 15
CLIP_DURATION = 30.0

PALETTE = {
    "paper": "#FFF8F0",
    "surface": "#F5EDE0",
    "border": "#D4CBBA",
    "ink": "#1A1208",
    "muted": "#8C7A68",
    "amber": "#C94B00",
    "cyan": "#1D6A8C",
    "red": "#B8291A",
}


@dataclass(frozen=True)
class PreviewSpec:
    key: str
    output_name: str
    section_id: str
    section_audio_offset: float
    scene_ids: tuple[str, str]
    global_start: float
    title: str


PREVIEWS = [
    PreviewSpec(
        key="intro",
        output_name="intro.mp4",
        section_id="s01",
        section_audio_offset=0.0,
        scene_ids=("sc01", "sc02"),
        global_start=0.0,
        title="INTRO: ONE VALVE",
    ),
    PreviewSpec(
        key="middle_diagram",
        output_name="middle_diagram.mp4",
        section_id="s06",
        section_audio_offset=0.0,
        scene_ids=("sc21", "sc22"),
        global_start=300.0,
        title="MIDDLE: PACKAGING BOTTLENECK",
    ),
    PreviewSpec(
        key="final_leverage_map",
        output_name="final_leverage_map.mp4",
        section_id="s13",
        section_audio_offset=0.0,
        scene_ids=("sc49", "sc50"),
        global_start=720.0,
        title="FINAL: LEVERAGE MAP",
    ),
]


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    if capture:
        return subprocess.run(cmd, check=True, text=True, capture_output=True)
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def probe_duration(path: Path) -> float:
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture=True,
    ).stdout.strip()
    return float(out)


def probe_streams(path: Path) -> dict:
    out = run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture=True,
    ).stdout
    return json.loads(out)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    elif bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:4]


def lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, p))


def ease(p: float) -> float:
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], color: str, width: int = 7) -> None:
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 24
    points = [
        end,
        (end[0] - size * math.cos(angle - 0.5), end[1] - size * math.sin(angle - 0.5)),
        (end[0] - size * math.cos(angle + 0.5), end[1] - size * math.sin(angle + 0.5)),
    ]
    draw.polygon(points, fill=color)


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str, size: int = 30, mono: bool = False) -> None:
    draw.text(xy, text.upper(), fill=color, font=font(size, bold=True, mono=mono))


def scene_for_time(spec: PreviewSpec, scenes: dict[str, dict], t: float) -> tuple[dict, float]:
    first = scenes[spec.scene_ids[0]]
    if t < 15.0:
        return first, t
    return scenes[spec.scene_ids[1]], t - 15.0


def active_state(scene: dict, scene_t: float) -> dict | None:
    changes = [c for c in scene.get("state_changes", []) if isinstance(c.get("t"), (int, float))]
    changes = sorted(changes, key=lambda c: c["t"])
    current = changes[0] if changes else None
    for change in changes:
        if scene_t >= float(change["t"]):
            current = change
    return current


def event_progress(scene: dict, scene_t: float) -> float:
    changes = sorted(
        [c for c in scene.get("state_changes", []) if isinstance(c.get("t"), (int, float))],
        key=lambda c: c["t"],
    )
    last = 0.0
    nxt = 15.0
    for i, change in enumerate(changes):
        if scene_t >= float(change["t"]):
            last = float(change["t"])
            nxt = float(changes[i + 1]["t"]) if i + 1 < len(changes) else 15.0
    return ease((scene_t - last) / max(0.1, nxt - last))


def draw_preview_frame(spec: PreviewSpec, script_sections: dict[str, dict], scenes: dict[str, dict], source_claims: dict[str, dict], t: float) -> Image.Image:
    scene, scene_t = scene_for_time(spec, scenes, t)
    section = script_sections[scene["script_section_id"]]
    state = active_state(scene, scene_t) or {}
    device = state.get("device_id", "route-trace")
    p = event_progress(scene, scene_t)
    pulse = 0.5 + 0.5 * math.sin(t * math.tau * 0.75)

    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(PALETTE["paper"]))
    draw = ImageDraw.Draw(img)

    ink = PALETTE["ink"]
    cyan = PALETTE["cyan"]
    amber = PALETTE["amber"]
    red = PALETTE["red"]
    muted = PALETTE["muted"]
    surface = PALETTE["surface"]
    border = PALETTE["border"]

    # Print Intelligence frame.
    draw.rectangle([64, 58, WIDTH - 64, HEIGHT - 58], outline=hex_to_rgb(border), width=3)
    draw.line([64, 170, WIDTH - 64, 170], fill=hex_to_rgb(border), width=2)
    draw_label(draw, (104, 92), spec.title, ink, 34, mono=True)
    draw_label(draw, (104, 136), f"{scene['id']} / {scene['script_section_id']} / {scene['tension_type']}", muted, 22, mono=True)
    draw_label(draw, (1510, 92), "RETENTION EVENT", muted, 22, mono=True)
    draw_label(draw, (1510, 128), str(device).replace("-", " "), amber if "amber" in device or "final" in device else cyan, 30, mono=True)

    # Left narrative column.
    title_font = font(46, bold=True)
    body_font = font(30)
    draw.text((104, 220), section["label"], fill=hex_to_rgb(ink), font=title_font)
    hook_lines = wrap_text(draw, scene["viewer_hook"], body_font, 560)
    y = 300
    for line in hook_lines:
        draw.text((104, y), line, fill=hex_to_rgb(ink), font=body_font)
        y += 42
    draw.rounded_rectangle([104, 510, 660, 700], radius=8, fill=hex_to_rgb(surface), outline=hex_to_rgb(border), width=3)
    draw_label(draw, (132, 536), "WHY KEEP WATCHING", amber, 20, mono=True)
    for line in wrap_text(draw, scene["retention_function"], font(25), 500):
        draw.text((132, y := y if y > 572 else 572), line, fill=hex_to_rgb(ink), font=font(25))
        y += 34

    # System map diagram area.
    map_box = [760, 230, 1760, 835]
    draw.rounded_rectangle(map_box, radius=10, fill=hex_to_rgb("#FFFFFF"), outline=hex_to_rgb(border), width=3)
    draw_label(draw, (790, 260), "DEVICE-DRIVEN SYSTEM MAP", muted, 22, mono=True)

    nodes = [
        ("BUYERS", 880, 690),
        ("TOOLS", 1080, 470),
        ("YIELD", 1280, 595),
        ("PACKAGING", 1450, 415),
        ("ALLOCATOR", 1620, 620),
    ]
    if spec.key == "intro":
        nodes = [("NVIDIA", 880, 690), ("APPLE", 1040, 500), ("OPENAI", 1200, 680), ("TSMC", 1430, 500), ("VALVE", 1620, 640)]
    elif spec.key == "final_leverage_map":
        nodes = [("ROUTING", 900, 690), ("YIELD", 1110, 470), ("PACKAGING", 1320, 625), ("ONSHORING", 1500, 430), ("LEVERAGE", 1630, 650)]
        resolve = ease(min(1.0, t / CLIP_DURATION))
        sweep_x = int(760 + ((t * 190) % 1000))
        draw.rectangle([sweep_x - 42, 230, sweep_x + 42, 835], fill=hex_to_rgb("#F5EDE0"))
        draw.line([sweep_x, 230, sweep_x, 835], fill=hex_to_rgb(amber), width=8)
        fan_center = (int(1620 - 120 * (1 - resolve)), int(650 - 70 * (1 - resolve)))
        for angle_idx, angle in enumerate([-2.4, -1.55, -0.75, 0.1]):
            end = (
                fan_center[0] + int((300 + angle_idx * 40) * math.cos(angle + t * 0.08)),
                fan_center[1] + int((210 + angle_idx * 30) * math.sin(angle + t * 0.08)),
            )
            draw_arrow(draw, end, fan_center, cyan if angle_idx < 2 else amber, 5)

    route_end = int(1 + p * (len(nodes) - 1))
    for idx in range(min(route_end, len(nodes) - 1)):
        a = nodes[idx]
        b = nodes[idx + 1]
        draw_arrow(draw, (a[1], a[2]), (b[1], b[2]), cyan, 8)

    for idx, (label, x, yy) in enumerate(nodes):
        fill = surface
        outline = cyan
        radius = 54
        if idx == min(route_end, len(nodes) - 1) or label in {"TSMC", "VALVE", "LEVERAGE", "PACKAGING"}:
            outline = amber
            radius += int(10 * pulse)
        if "red" in device or "consequence" in str(state.get("beat", "")):
            if idx >= len(nodes) - 2:
                outline = red
        draw.ellipse([x - radius, yy - radius, x + radius, yy + radius], fill=hex_to_rgb(fill), outline=hex_to_rgb(outline), width=8)
        bbox = draw.textbbox((0, 0), label, font=font(22, bold=True, mono=True))
        draw.text((x - (bbox[2] - bbox[0]) / 2, yy - 13), label, fill=hex_to_rgb(ink), font=font(22, bold=True, mono=True))

    if "source-card-reveal" in device or scene_t >= 6.0:
        claim_id = (scene.get("source_claim_ids") or [""])[0]
        claim = source_claims.get(claim_id, {})
        card_x = int(lerp(1880, 1150, p if scene_t >= 6.0 else 0))
        draw.rounded_rectangle([card_x, 720, card_x + 540, 805], radius=8, fill=hex_to_rgb(surface), outline=hex_to_rgb(amber), width=4)
        draw_label(draw, (card_x + 24, 738), f"SOURCE PROOF {claim_id}", amber, 20, mono=True)
        proof = claim.get("claim_text") or scene.get("payoff_moment", "")
        for i, line in enumerate(wrap_text(draw, proof, font(22), 490)[:2]):
            draw.text((card_x + 24, 766 + i * 26), line, fill=hex_to_rgb(ink), font=font(22))

    if spec.key == "middle_diagram":
        bottleneck_y = 905
        w = int(760 * p)
        draw_label(draw, (790, 880), "BOTTLENECK CONSEQUENCE", red if scene_t > 8 else amber, 20, mono=True)
        draw.rounded_rectangle([790, bottleneck_y, 1550, bottleneck_y + 36], radius=5, fill=hex_to_rgb("#EFE2D0"))
        draw.rounded_rectangle([790, bottleneck_y, 790 + w, bottleneck_y + 36], radius=5, fill=hex_to_rgb(red if scene_t > 8 else amber))
        draw_label(draw, (1580, 902), "QUEUE TIGHTENS", red if scene_t > 8 else muted, 24, mono=True)

    if spec.key == "final_leverage_map":
        draw_label(draw, (790, 880), "FINAL SYNTHESIS", amber, 22, mono=True)
        labels = ["ROUTING", "ALLOCATION", "SCHEDULE"]
        for i, label in enumerate(labels):
            x = int(790 + i * 265 + math.sin(t * 1.7 + i) * 12)
            alpha_ready = p > i * 0.22 or scene_t > 7
            color = amber if alpha_ready else muted
            lift = int((1.0 - ease(min(1.0, max(0.0, (t - i * 2.0) / 5.0)))) * 70)
            draw.rounded_rectangle([x, 910 + lift, x + 230, 970 + lift], radius=7, fill=hex_to_rgb(surface), outline=hex_to_rgb(color), width=4)
            draw_label(draw, (x + 24, 928 + lift), label, color, 24, mono=True)

    # Payoff strike at bottom.
    payoff_y = 842
    draw.rectangle([104, payoff_y, 660, 975], fill=hex_to_rgb(PALETTE["paper"]))
    draw.line([104, payoff_y, 660, payoff_y], fill=hex_to_rgb(amber if scene_t < 10 else red), width=6)
    draw_label(draw, (104, payoff_y + 24), "PAYOFF", amber if scene_t < 10 else red, 22, mono=True)
    for i, line in enumerate(wrap_text(draw, scene["payoff_moment"], font(28), 540)[:3]):
        draw.text((104, payoff_y + 62 + i * 36), line, fill=hex_to_rgb(ink), font=font(28))

    # Micro motion markers.
    for change in scene.get("state_changes", []):
        x = 760 + int(float(change["t"]) / 15.0 * 1000)
        color = amber if float(change["t"]) <= scene_t else border
        draw.line([x, 190, x, 214], fill=hex_to_rgb(color), width=4)
    draw.ellipse([760 + int(scene_t / 15.0 * 1000) - 9, 186, 760 + int(scene_t / 15.0 * 1000) + 9, 204], fill=hex_to_rgb(red if scene_t > 11 else amber))

    return img


def render_video_frames(spec: PreviewSpec, script_sections: dict[str, dict], scenes: dict[str, dict], source_claims: dict[str, dict]) -> Path:
    frames_dir = WORK_DIR / f"{spec.key}_frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_count = int(CLIP_DURATION * FPS)
    for frame_idx in range(frame_count):
        t = frame_idx / FPS
        image = draw_preview_frame(spec, script_sections, scenes, source_claims, t)
        image.save(frames_dir / f"frame_{frame_idx:05d}.png", quality=95)
    video_no_audio = WORK_DIR / f"{spec.key}_video.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(video_no_audio),
        ]
    )
    return video_no_audio


def mux_audio(spec: PreviewSpec, video_no_audio: Path, audio_path: Path, output_path: Path) -> Path:
    audio_clip = WORK_DIR / f"{spec.key}_audio.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(spec.section_audio_offset),
            "-t",
            str(CLIP_DURATION),
            "-i",
            str(audio_path),
            "-ac",
            "2",
            "-ar",
            "48000",
            str(audio_clip),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_no_audio),
            "-i",
            str(audio_clip),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    )
    return output_path


def make_contact_sheet(video_path: Path, output_path: Path) -> None:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    timestamps = [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0]
    images: list[Image.Image] = []
    for ts in timestamps:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * fps))
        ok, frame = cap.read()
        if not ok:
            frame = np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((384, 216))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([8, 8, 78, 34], radius=4, fill=(26, 18, 8))
        d.text((14, 12), f"{ts:04.1f}s", fill=(255, 248, 240), font=font(16, bold=True, mono=True))
        images.append(img)
    cap.release()
    sheet = Image.new("RGB", (384 * 5, 216 * 2), hex_to_rgb(PALETTE["paper"]))
    for i, img in enumerate(images):
        sheet.paste(img, ((i % 5) * 384, (i // 5) * 216))
    sheet.save(output_path)


def combine_contact_sheets(paths: list[Path], output_path: Path) -> None:
    sheets = [Image.open(path).convert("RGB").resize((960, 216)) for path in paths]
    combined = Image.new("RGB", (960, 216 * len(sheets)), hex_to_rgb(PALETTE["paper"]))
    for i, sheet in enumerate(sheets):
        combined.paste(sheet, (0, i * 216))
    combined.save(output_path)


def visual_qa(video_path: Path) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps else probe_duration(video_path)
    sample_step = max(1, int(fps * 0.5))
    prev_gray = None
    intervals = []
    blank_count = 0
    dark_bg_count = 0
    sampled = 0
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % sample_step == 0:
            sampled += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            paper = np.array(hex_to_rgb(PALETTE["paper"]), dtype=np.float32)
            dist = np.sqrt(np.sum((rgb.astype(np.float32) - paper) ** 2, axis=2))
            non_paper_ratio = float(np.mean(dist > 28))
            if non_paper_ratio < 0.035:
                blank_count += 1
            if float(np.mean(gray < 60)) > 0.35:
                dark_bg_count += 1
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                changed_ratio = float(np.mean(diff > 12))
                intervals.append(changed_ratio)
            prev_gray = gray
        frame_idx += 1
    cap.release()

    static_threshold = 0.004
    small_threshold = 0.018
    longest_static = 0.0
    current_static = 0.0
    for value in intervals:
        if value < static_threshold:
            current_static += 0.5
            longest_static = max(longest_static, current_static)
        else:
            current_static = 0.0
    static_ratio = float(np.mean([v < static_threshold for v in intervals])) if intervals else 1.0
    small_area_motion_ratio = float(np.mean([(static_threshold <= v < small_threshold) for v in intervals])) if intervals else 1.0
    motion_density = float(mean(intervals)) if intervals else 0.0
    return {
        "duration_seconds": round(duration, 2),
        "motion_density": round(motion_density, 4),
        "longest_static_span_seconds": round(longest_static, 2),
        "static_ratio": round(static_ratio, 4),
        "small_area_motion_ratio": round(small_area_motion_ratio, 4),
        "blank_paper_risk": round(blank_count / max(1, sampled), 4),
        "stale_dark_system_color_ratio": round(dark_bg_count / max(1, sampled), 4),
        "thumbnail_contact_sheet_created": True,
    }


def audio_qa(video_path: Path) -> dict:
    streams = probe_streams(video_path)
    audio_streams = [s for s in streams.get("streams", []) if s.get("codec_type") == "audio"]
    video_duration = float(streams["format"]["duration"])
    audio_present = bool(audio_streams)
    silence_events = []
    peak_db = None
    rms_db = None
    if audio_present:
        proc = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(video_path),
                "-af",
                "silencedetect=noise=-42dB:d=0.75,astats=metadata=1:reset=1",
                "-f",
                "null",
                "-",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        stderr = proc.stderr
        starts: list[float] = []
        for line in stderr.splitlines():
            if "silence_start:" in line:
                try:
                    starts.append(float(line.split("silence_start:")[1].strip().split()[0]))
                except ValueError:
                    pass
            if "silence_end:" in line:
                try:
                    rest = line.split("silence_end:")[1].strip()
                    end = float(rest.split()[0])
                    dur = float(rest.split("silence_duration:")[1].strip().split()[0])
                    silence_events.append({"start": round(end - dur, 3), "end": round(end, 3), "duration": round(dur, 3)})
                except (ValueError, IndexError):
                    pass
            if "Peak level dB:" in line:
                try:
                    peak_db = float(line.split("Peak level dB:")[1].strip().split()[0])
                except ValueError:
                    pass
            if "RMS level dB:" in line:
                try:
                    rms_db = float(line.split("RMS level dB:")[1].strip().split()[0])
                except ValueError:
                    pass
    max_silence = max((e["duration"] for e in silence_events), default=0.0)
    audio_duration = float(audio_streams[0].get("duration") or video_duration) if audio_streams else 0.0
    return {
        "audio_present": audio_present,
        "video_duration_seconds": round(video_duration, 2),
        "audio_duration_seconds": round(audio_duration, 2),
        "duration_delta_seconds": round(abs(video_duration - audio_duration), 2),
        "max_silence_seconds": round(max_silence, 2),
        "long_silence": max_silence > 2.0,
        "peak_db": peak_db,
        "rms_db": rms_db,
        "clipping_detected": peak_db is not None and peak_db > -0.1,
        "narration_starts_expected_beat": not any(e["start"] <= 0.2 and e["duration"] > 1.25 for e in silence_events),
        "voice_mismatch_detectable": False,
        "voice_mismatch_note": "Same canonical Fish Speech narration section files used; no speaker classifier available.",
    }


def preview_passes(vqa: dict, aqa: dict, spec: PreviewSpec) -> tuple[bool, list[str]]:
    issues = []
    if vqa["longest_static_span_seconds"] > 4.0:
        issues.append("static span exceeds 4.0s")
    if vqa["blank_paper_risk"] > 0.15:
        issues.append("mostly blank/paper-only risk")
    if vqa["static_ratio"] > 0.85:
        issues.append("static ratio exceeds 0.85")
    if vqa["small_area_motion_ratio"] > 0.8:
        issues.append("motion mostly small-area/text-only")
    if vqa["stale_dark_system_color_ratio"] > 0.1:
        issues.append("stale dark-system color risk")
    if not aqa["audio_present"]:
        issues.append("audio missing")
    if aqa["duration_delta_seconds"] > 0.35:
        issues.append("audio/video duration mismatch")
    if aqa["long_silence"]:
        issues.append("long silence detected")
    if aqa["clipping_detected"]:
        issues.append("clipping detected")
    if not aqa["narration_starts_expected_beat"]:
        issues.append("narration does not start at expected beat")
    if spec.key == "final_leverage_map" and vqa["motion_density"] < 0.02:
        issues.append("final leverage map lacks clear resolving motion")
    return not issues, issues


def main() -> int:
    script = json.load(open(ARTIFACTS / "script.json"))
    scene_plan = json.load(open(ARTIFACTS / "scene_plan.json"))
    source_map = json.load(open(ARTIFACTS / "source_map.json"))
    asset_manifest = json.load(open(ARTIFACTS / "asset_manifest.json"))

    sections = {s["id"]: s for s in script["sections"]}
    scenes = {s["id"]: s for s in scene_plan["scenes"]}
    claims = {c["claim_id"]: c for c in source_map.get("claims", [])}
    receipts = {r["section_id"]: r for r in asset_manifest.get("tts_chunk_receipts", [])}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    existing_report_path = OUT_DIR / "preview_validation_report.json"
    if existing_report_path.exists():
        report = json.loads(existing_report_path.read_text())
    else:
        report = {
        "render_method": "Fresh deterministic Print Intelligence frame renderer driven by canonical script.json + scene_plan.json; FFmpeg muxes current per-section narration.",
        "artifact_inputs": {
            "script": str(ARTIFACTS / "script.json"),
            "scene_plan": str(ARTIFACTS / "scene_plan.json"),
            "source_map": str(ARTIFACTS / "source_map.json"),
            "asset_manifest": str(ARTIFACTS / "asset_manifest.json"),
        },
        "previews": {},
        }

    contact_paths: list[Path] = []
    requested = {k for k in os.environ.get("PREVIEW_KEYS", "").split(",") if k.strip()}
    selected = [spec for spec in PREVIEWS if not requested or spec.key in requested]
    for spec in selected:
        receipt = receipts.get(spec.section_id)
        if not receipt:
            raise RuntimeError(f"Missing TTS receipt for {spec.section_id}")
        audio_path = PROJECT / receipt["final_output_path"]
        if not audio_path.exists():
            raise RuntimeError(f"Missing narration file: {audio_path}")
        audio_duration = probe_duration(audio_path)
        if audio_duration < spec.section_audio_offset + CLIP_DURATION - 0.05:
            raise RuntimeError(
                f"Narration stale/mismatched for {spec.key}: {audio_path} duration {audio_duration:.2f}s "
                f"cannot cover offset {spec.section_audio_offset:.2f}s + {CLIP_DURATION:.2f}s"
            )

        output_path = OUT_DIR / spec.output_name
        video_no_audio = render_video_frames(spec, sections, scenes, claims)
        mux_audio(spec, video_no_audio, audio_path, output_path)
        contact_path = OUT_DIR / f"{spec.key}_contact_sheet.png"
        make_contact_sheet(output_path, contact_path)
        contact_paths.append(contact_path)

        vqa = visual_qa(output_path)
        aqa = audio_qa(output_path)
        passed, issues = preview_passes(vqa, aqa, spec)
        report["previews"][spec.key] = {
            "output_path": str(output_path),
            "contact_sheet": str(contact_path),
            "scene_ids": list(spec.scene_ids),
            "global_timestamp_seconds": [spec.global_start, spec.global_start + CLIP_DURATION],
            "section_id": spec.section_id,
            "section_audio_offset_seconds": spec.section_audio_offset,
            "narration_path": str(audio_path),
            "source_audio_duration_seconds": round(audio_duration, 2),
            "visual_qa": vqa,
            "audio_qa": aqa,
            "passed": passed,
            "issues": issues,
        }

    combined = OUT_DIR / "contact_sheet_combined.png"
    all_contact_paths = []
    for spec in PREVIEWS:
        contact = OUT_DIR / f"{spec.key}_contact_sheet.png"
        if contact.exists():
            all_contact_paths.append(contact)
    combine_contact_sheets(all_contact_paths, combined)
    report["combined_contact_sheet"] = str(combined)
    report["all_passed"] = all(p["passed"] for p in report["previews"].values())
    report["recommendation"] = "approve full render" if report["all_passed"] else "revise scene plan/templates/narration before full render"
    report_path = OUT_DIR / "preview_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["all_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
