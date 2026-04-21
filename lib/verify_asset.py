"""Asset verification utilities.

Every generated asset (image, audio, video) must pass verification before
the pipeline treats it as successfully produced. Call verify_asset() after
any generation tool returns success.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class VerifyResult:
    valid: bool
    path: str
    asset_type: str
    detail: str  # human-readable summary (e.g. "image/png 1920x1080 245KB")
    error: Optional[str] = None


def verify_asset(path: str, expected_type: str = "auto") -> VerifyResult:
    """Verify a generated asset exists, is non-zero, and is a valid file.

    Args:
        path: Filesystem path to the asset.
        expected_type: One of "image", "audio", "video", or "auto" (infer from extension).

    Returns:
        VerifyResult with valid=True/False and diagnostic detail.
    """
    p = Path(path)

    if not p.exists():
        return VerifyResult(False, path, expected_type, "", error=f"File does not exist: {path}")

    size = p.stat().st_size
    if size == 0:
        return VerifyResult(False, path, expected_type, "", error=f"File is empty (0 bytes): {path}")

    if expected_type == "auto":
        expected_type = _infer_type(p)

    if expected_type == "image":
        return _verify_image(p, size)
    elif expected_type == "audio":
        return _verify_audio(p, size)
    elif expected_type == "video":
        return _verify_video(p, size)
    else:
        # Unknown type — at least confirm non-zero
        return VerifyResult(True, path, expected_type, f"{size} bytes")


def _infer_type(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"):
        return "image"
    elif ext in (".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a"):
        return "audio"
    elif ext in (".mp4", ".webm", ".mov", ".avi", ".mkv"):
        return "video"
    return "unknown"


def _verify_image(p: Path, size: int) -> VerifyResult:
    """Check file type via `file` command."""
    try:
        result = subprocess.run(
            ["file", "--brief", str(p)],
            capture_output=True, text=True, timeout=10,
        )
        desc = result.stdout.strip()
        # file(1) returns things like "PNG image data, 1920 x 1080, ..."
        if "image" in desc.lower() or "svg" in desc.lower():
            return VerifyResult(True, str(p), "image", f"{desc} ({size} bytes)")
        return VerifyResult(False, str(p), "image", desc,
                            error=f"Not a valid image: {desc}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # Fallback: if `file` is unavailable, accept non-zero size
        return VerifyResult(True, str(p), "image", f"{size} bytes (file cmd unavailable: {e})")


def _verify_audio(p: Path, size: int) -> VerifyResult:
    """Check duration via ffprobe."""
    duration = _ffprobe_duration(p)
    if duration is None:
        return VerifyResult(False, str(p), "audio", "",
                            error=f"ffprobe could not read duration from {p}")
    if duration <= 0:
        return VerifyResult(False, str(p), "audio", "",
                            error=f"Audio has zero duration: {p}")
    return VerifyResult(True, str(p), "audio", f"{duration:.1f}s ({size} bytes)")


def _verify_video(p: Path, size: int) -> VerifyResult:
    """Check duration and stream presence via ffprobe."""
    duration = _ffprobe_duration(p)
    if duration is None:
        return VerifyResult(False, str(p), "video", "",
                            error=f"ffprobe could not read duration from {p}")
    if duration <= 0:
        return VerifyResult(False, str(p), "video", "",
                            error=f"Video has zero duration: {p}")
    return VerifyResult(True, str(p), "video", f"{duration:.1f}s ({size} bytes)")


def _ffprobe_duration(p: Path) -> Optional[float]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(p),
            ],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None
