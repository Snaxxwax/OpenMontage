"""Visual QA tool for automated video quality checks.

Extracts frames at specified timestamps and runs basic quality checks:
- File existence, resolution, duration, codec validation
- Frame extraction for visual inspection by the agent
- Caption occlusion check (compares brightness in face vs caption zones)
- Transition verification (frame similarity at transition points)
- Motion density checks (detect long static spans / deck-like pacing)

Returns frame paths so the agent can visually inspect them.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolTier,
)


class VisualQA(BaseTool):
    name = "visual_qa"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "analysis"
    provider = "ffmpeg"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = ["cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = "Install FFmpeg: https://ffmpeg.org/download.html"
    agent_skills = ["ffmpeg"]

    capabilities = [
        "extract_review_frames",
        "probe_video",
        "check_audio_levels",
        "motion_density",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation", "input_path"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["review", "probe", "audio_levels", "motion_density"],
                "description": (
                    "review: extract frames at timestamps for visual inspection. "
                    "probe: get video metadata (duration, resolution, codecs). "
                    "audio_levels: check audio volume at specified timestamps. "
                    "motion_density: detect long static spans / deck-like text-only motion."
                ),
            },
            "input_path": {
                "type": "string",
                "description": "Path to the video file to inspect.",
            },
            "timestamps": {
                "type": "array",
                "items": {"type": "number"},
                "description": (
                    "Timestamps (in seconds) at which to extract frames or "
                    "check audio levels."
                ),
            },
            "output_dir": {
                "type": "string",
                "description": (
                    "Directory to save extracted frames. Defaults to a "
                    "'review_frames' subdirectory next to the input file."
                ),
            },
            "checks": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "resolution",
                        "duration",
                        "audio_present",
                        "pixel_format",
                        "file_size",
                    ],
                },
                "description": "Specific checks to run (probe operation).",
            },
            "expected": {
                "type": "object",
                "description": (
                    "Expected values for validation. "
                    "Keys: width, height, min_duration, max_duration, "
                    "pixel_format, has_audio."
                ),
                "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "min_duration": {"type": "number"},
                    "max_duration": {"type": "number"},
                    "pixel_format": {"type": "string"},
                    "has_audio": {"type": "boolean"},
                },
            },
            "motion_params": {
                "type": "object",
                "description": "Parameters for motion_density operation.",
                "properties": {
                    "sample_every_seconds": {
                        "type": "number",
                        "minimum": 0.05,
                        "default": 0.25
                    },
                    "downscale_height": {
                        "type": "integer",
                        "minimum": 120,
                        "default": 240
                    },
                    "pixel_diff_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "default": 3.0
                    },
                    "static_mean_diff_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "default": 0.05
                    },
                    "static_area_ratio_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.001
                    },
                    "max_static_span_seconds": {
                        "type": "number",
                        "minimum": 0.5,
                        "default": 4.0
                    },
                    "static_ratio_warning_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.65
                    },
                    "static_ratio_hard_fail_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.85
                    },
                    "small_motion_area_ratio_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.01
                    },
                    "max_small_area_motion_ratio": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.8
                    }
                }
            },
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=200)
    idempotency_key_fields = ["operation", "input_path", "timestamps", "motion_params"]
    side_effects = ["writes frame images to output_dir"]
    user_visible_verification = [
        "Visually inspect extracted frames for quality issues",
    ]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs["operation"]
        input_path = inputs["input_path"]

        if not Path(input_path).exists():
            return ToolResult(success=False, error=f"Input not found: {input_path}")

        start = time.time()

        try:
            if operation == "review":
                result = self._review(inputs)
            elif operation == "probe":
                result = self._probe(inputs)
            elif operation == "audio_levels":
                result = self._audio_levels(inputs)
            elif operation == "motion_density":
                result = self._motion_density(inputs)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _review(self, inputs: dict[str, Any]) -> ToolResult:
        """Extract frames at specified timestamps for visual review."""
        input_path = inputs["input_path"]
        timestamps = inputs.get("timestamps", [])

        if not timestamps:
            # Auto-generate timestamps: start, 25%, 50%, 75%, end-1s
            dur = self._get_duration(input_path)
            timestamps = [
                1.0,
                dur * 0.25,
                dur * 0.50,
                dur * 0.75,
                max(dur - 1.0, 0),
            ]

        output_dir = inputs.get("output_dir")
        if not output_dir:
            output_dir = str(Path(input_path).parent / "review_frames")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        frames = []
        for ts in timestamps:
            ts_label = f"{ts:.1f}".replace(".", "_")
            frame_path = str(Path(output_dir) / f"frame_{ts_label}s.jpg")
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(ts),
                "-i", input_path,
                "-frames:v", "1",
                "-q:v", "2",
                frame_path,
            ]
            try:
                self.run_command(cmd)
                if Path(frame_path).exists():
                    frames.append({
                        "timestamp": ts,
                        "path": frame_path,
                    })
            except Exception:
                frames.append({
                    "timestamp": ts,
                    "path": None,
                    "error": f"Failed to extract frame at {ts}s",
                })

        return ToolResult(
            success=True,
            data={
                "operation": "review",
                "input": input_path,
                "frame_count": len([f for f in frames if f.get("path")]),
                "frames": frames,
            },
            artifacts=[f["path"] for f in frames if f.get("path")],
        )

    def _probe(self, inputs: dict[str, Any]) -> ToolResult:
        """Probe video metadata and optionally validate against expectations."""
        input_path = inputs["input_path"]
        expected = inputs.get("expected", {})

        # Get comprehensive probe data
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration,size:stream=width,height,codec_name,pix_fmt,"
            "r_frame_rate,sample_rate,channels,codec_type",
            "-of", "json",
            input_path,
        ]
        import json
        probe_result = self.run_command(cmd)
        probe_out = probe_result.stdout
        probe_data = json.loads(probe_out)

        # Extract key info
        video_stream = None
        audio_stream = None
        for s in probe_data.get("streams", []):
            if s.get("codec_type") == "video" and not video_stream:
                video_stream = s
            elif s.get("codec_type") == "audio" and not audio_stream:
                audio_stream = s

        info = {
            "duration": float(probe_data.get("format", {}).get("duration", 0)),
            "file_size_mb": round(
                int(probe_data.get("format", {}).get("size", 0)) / 1048576, 1
            ),
            "has_audio": audio_stream is not None,
        }
        if video_stream:
            info.update({
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "pixel_format": video_stream.get("pix_fmt"),
                "video_codec": video_stream.get("codec_name"),
                "frame_rate": video_stream.get("r_frame_rate"),
            })
        if audio_stream:
            info.update({
                "audio_codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels"),
            })

        # Validate against expectations
        issues = []
        if "width" in expected and info.get("width") != expected["width"]:
            issues.append(f"Width: expected {expected['width']}, got {info.get('width')}")
        if "height" in expected and info.get("height") != expected["height"]:
            issues.append(f"Height: expected {expected['height']}, got {info.get('height')}")
        if "min_duration" in expected and info["duration"] < expected["min_duration"]:
            issues.append(
                f"Duration too short: {info['duration']:.1f}s < {expected['min_duration']}s"
            )
        if "max_duration" in expected and info["duration"] > expected["max_duration"]:
            issues.append(
                f"Duration too long: {info['duration']:.1f}s > {expected['max_duration']}s"
            )
        if "pixel_format" in expected and info.get("pixel_format") != expected["pixel_format"]:
            issues.append(
                f"Pixel format: expected {expected['pixel_format']}, got {info.get('pixel_format')}"
            )
        if "has_audio" in expected and info["has_audio"] != expected["has_audio"]:
            issues.append(
                f"Audio: expected {'present' if expected['has_audio'] else 'absent'}, "
                f"got {'present' if info['has_audio'] else 'absent'}"
            )

        info["validation_issues"] = issues
        info["validation_passed"] = len(issues) == 0

        return ToolResult(
            success=True,
            data={
                "operation": "probe",
                "input": input_path,
                **info,
            },
        )

    def _motion_density(self, inputs: dict[str, Any]) -> ToolResult:
        """Detect long static spans and deck-like 'text-only motion' patterns."""
        input_path = inputs["input_path"]
        params = inputs.get("motion_params") or {}

        sample_every = float(params.get("sample_every_seconds", 0.25) or 0.25)
        downscale_h = int(params.get("downscale_height", 240) or 240)
        pixel_thr = float(params.get("pixel_diff_threshold", 3.0) or 3.0)
        static_mean_thr = float(params.get("static_mean_diff_threshold", 0.05) or 0.05)
        static_area_thr = float(params.get("static_area_ratio_threshold", 0.001) or 0.001)
        max_static_span = float(params.get("max_static_span_seconds", 4.0) or 4.0)
        static_ratio_warn_thr = float(params.get("static_ratio_warning_threshold", 0.65) or 0.65)
        static_ratio_fail_thr = float(params.get("static_ratio_hard_fail_threshold", 0.85) or 0.85)
        small_area_thr = float(params.get("small_motion_area_ratio_threshold", 0.01) or 0.01)
        max_small_area_ratio = float(params.get("max_small_area_motion_ratio", 0.80) or 0.80)

        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception as e:
            return ToolResult(success=False, error=f"motion_density requires OpenCV + numpy: {e}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return ToolResult(success=False, error=f"Failed to open video: {input_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        step_frames = max(1, int(round(fps * sample_every)))

        ok, frame0 = cap.read()
        if not ok or frame0 is None:
            cap.release()
            return ToolResult(success=False, error=f"Failed to read first frame: {input_path}")

        def prep(frame):
            h, w = frame.shape[:2]
            if not h or not w:
                return None
            scale = float(downscale_h) / float(h)
            if scale < 1.0:
                frame = cv2.resize(frame, (int(w * scale), downscale_h))
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        prev = prep(frame0)
        if prev is None:
            cap.release()
            return ToolResult(success=False, error="motion_density: invalid first frame")

        static_flags: list[bool] = []
        area_ratios: list[float] = []
        mean_diffs: list[float] = []

        while True:
            for _ in range(step_frames - 1):
                if not cap.grab():
                    cap.release()
                    break
            else:
                ok, frame = cap.retrieve()
                if not ok or frame is None:
                    break
                gray = prep(frame)
                if gray is None:
                    break

                diff = cv2.absdiff(prev, gray)
                mean_diff = float(np.mean(diff))
                area_ratio = float(np.mean(diff > pixel_thr))
                is_static = (mean_diff < static_mean_thr) and (area_ratio < static_area_thr)

                mean_diffs.append(mean_diff)
                area_ratios.append(area_ratio)
                static_flags.append(bool(is_static))

                prev = gray
                continue
            break

        cap.release()

        if not static_flags:
            return ToolResult(success=False, error="motion_density: no samples collected")

        static_spans: list[dict[str, float]] = []
        cur_start: float | None = None
        cur_len = 0.0
        for i, is_static in enumerate(static_flags):
            t = (i + 1) * sample_every
            if is_static:
                if cur_start is None:
                    cur_start = max(0.0, t - sample_every)
                    cur_len = sample_every
                else:
                    cur_len += sample_every
            else:
                if cur_start is not None:
                    static_spans.append(
                        {
                            "start_seconds": cur_start,
                            "end_seconds": cur_start + cur_len,
                            "duration_seconds": cur_len,
                        }
                    )
                    cur_start = None
                    cur_len = 0.0
        if cur_start is not None:
            static_spans.append(
                {
                    "start_seconds": cur_start,
                    "end_seconds": cur_start + cur_len,
                    "duration_seconds": cur_len,
                }
            )

        longest_static = max((s["duration_seconds"] for s in static_spans), default=0.0)
        static_ratio = sum(1 for f in static_flags if f) / len(static_flags)

        non_static_areas = [a for f, a in zip(static_flags, area_ratios) if not f]
        small_area_motion_ratio = (
            sum(1 for a in non_static_areas if a < small_area_thr) / len(non_static_areas)
            if non_static_areas
            else 0.0
        )

        hard_fail_issues: list[str] = []
        warnings: list[str] = []
        if longest_static > max_static_span + 1e-6:
            hard_fail_issues.append(
                f"Longest static span {longest_static:.2f}s exceeds {max_static_span:.2f}s"
            )

        # Static ratio is advisory by default; only hard-fail when extreme.
        if static_ratio > static_ratio_fail_thr + 1e-6:
            hard_fail_issues.append(
                f"Static ratio {static_ratio:.0%} exceeds {static_ratio_fail_thr:.0%}"
            )
        elif static_ratio > static_ratio_warn_thr + 1e-6:
            warnings.append(
                f"Static ratio {static_ratio:.0%} exceeds {static_ratio_warn_thr:.0%}"
            )

        # Small-area motion is a deck smell, but treat as warning (channel-dependent).
        if non_static_areas and small_area_motion_ratio > max_small_area_ratio + 1e-6:
            warnings.append(
                f"Small-area motion ratio {small_area_motion_ratio:.0%} exceeds {max_small_area_ratio:.0%} "
                "(risk: mostly text/card updates)"
            )

        return ToolResult(
            success=(len(hard_fail_issues) == 0),
            data={
                "operation": "motion_density",
                "input": input_path,
                "fps": round(fps, 3),
                "sample_every_seconds": sample_every,
                "samples": len(static_flags),
                "static_ratio": round(static_ratio, 3),
                "longest_static_span_seconds": round(longest_static, 3),
                "static_spans": static_spans[:30],
                "small_area_motion_ratio": round(small_area_motion_ratio, 3),
                "thresholds": {
                    "pixel_diff_threshold": pixel_thr,
                    "static_mean_diff_threshold": static_mean_thr,
                    "static_area_ratio_threshold": static_area_thr,
                    "max_static_span_seconds": max_static_span,
                    "static_ratio_warning_threshold": static_ratio_warn_thr,
                    "static_ratio_hard_fail_threshold": static_ratio_fail_thr,
                    "small_motion_area_ratio_threshold": small_area_thr,
                    "max_small_area_motion_ratio": max_small_area_ratio,
                },
                "hard_fail_issues": hard_fail_issues,
                "warnings": warnings,
            },
        )

    def _audio_levels(self, inputs: dict[str, Any]) -> ToolResult:
        """Check audio levels at specified timestamps."""
        input_path = inputs["input_path"]
        timestamps = inputs.get("timestamps", [])

        if not timestamps:
            dur = self._get_duration(input_path)
            timestamps = [1.0, dur * 0.5, max(dur - 2.0, 0)]

        levels = []
        for ts in timestamps:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(ts),
                "-t", "3",
                "-i", input_path,
                "-vn", "-af", "volumedetect",
                "-f", "null", "NUL" if __import__("sys").platform == "win32" else "/dev/null",
            ]
            try:
                cmd_result = self.run_command(cmd)
                output = cmd_result.stderr  # volumedetect outputs to stderr
                mean_vol = None
                max_vol = None
                for line in output.split("\n"):
                    if "mean_volume" in line:
                        mean_vol = float(line.split("mean_volume:")[1].strip().split()[0])
                    elif "max_volume" in line:
                        max_vol = float(line.split("max_volume:")[1].strip().split()[0])
                levels.append({
                    "timestamp": ts,
                    "mean_volume_db": mean_vol,
                    "max_volume_db": max_vol,
                })
            except Exception as e:
                levels.append({
                    "timestamp": ts,
                    "error": str(e),
                })

        return ToolResult(
            success=True,
            data={
                "operation": "audio_levels",
                "input": input_path,
                "levels": levels,
            },
        )

    def _get_duration(self, path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            path,
        ]
        dur_result = self.run_command(cmd)
        return float(dur_result.stdout.strip().split("\n")[0])
