"""Contract tests for asymmetric_check_prepared_media.py."""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from asymmetric_check_prepared_media import check_prepared_media  # noqa: E402


# ── PNG helper ────────────────────────────────────────────────────────────────

def _png_bytes(width: int, height: int) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype: bytes, data: bytes) -> bytes:
        crc_payload = ctype + data
        return (
            struct.pack(">I", len(data))
            + ctype
            + data
            + struct.pack(">I", zlib.crc32(crc_payload) & 0xFFFFFFFF)
        )

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    row = b"\x00" + b"\xFF\xFF\xFF" * width
    idat = chunk(b"IDAT", zlib.compress(row * height))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ── fixture builders ──────────────────────────────────────────────────────────

def _write_png(path: Path, width: int, height: int) -> Path:
    path.write_bytes(_png_bytes(width, height))
    return path


def _screenshot_asset(tmp_path: Path, asset_id: str, w: int, h: int,
                       same_prepared: bool = False, **overrides) -> dict:
    input_file = tmp_path / f"{asset_id}_input.png"
    _write_png(input_file, w, h)

    if same_prepared:
        prepared_file = input_file
    else:
        prepared_file = tmp_path / f"{asset_id}_prepared.png"
        _write_png(prepared_file, w, h)

    asset = {
        "asset_id": asset_id,
        "media_type": "screenshot",
        "role": "proof",
        "input_path": str(input_file),
        "prepared_path": str(same_prepared and str(input_file) or str(prepared_file)),
        "source_label_required": True,
        "preparation_status": "prepared",
        "qc_notes": "test",
        "legibility_ok": True,
        "framing": "crop",
        "render_treatment": "scale_fit",
    }
    asset.update(overrides)
    return asset


def _video_asset(**overrides) -> dict:
    base = {
        "asset_id": "vid-001",
        "media_type": "video",
        "role": "b-roll",
        "input_path": "/project/clips/clip.mp4",
        "prepared_path": "/project/clips/clip.mp4",
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "test",
        "in_seconds": 0.0,
        "out_seconds": 30.0,
        "duration_seconds": 96.0,
        "framing": "wide_shot",
        "audio_role": "ambient",
    }
    base.update(overrides)
    return base


def _narration_asset(**overrides) -> dict:
    base = {
        "asset_id": "nar-001",
        "media_type": "audio",
        "role": "narration",
        "input_path": "/project/narration/nar.mp3",
        "prepared_path": "/project/narration/nar.mp3",
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "test",
        "duration_seconds": 817.0,
        "audio_role": "narration",
        "loudness_lufs": -16.16,
        "silence_gate_passed": True,
    }
    base.update(overrides)
    return base


def _manifest(episode_id: str = "test-ep", *assets: dict) -> dict:
    return {
        "episode_id": episode_id,
        "operator_approved_for_staging": False,
        "assets": list(assets),
    }


# ── callable ──────────────────────────────────────────────────────────────────

def test_check_prepared_media_callable():
    assert callable(check_prepared_media)


# ── pass tests ────────────────────────────────────────────────────────────────

def test_landscape_screenshot_passes(tmp_path):
    # 1280x720 — renders at exactly full width
    asset = _screenshot_asset(tmp_path, "sc-land", w=1280, h=720)
    m = _manifest("ep", asset)
    out = tmp_path / "qc" / "prepared_media_qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 0
    assert "PASS" in out.read_text()


def test_valid_video_passes(tmp_path):
    asset = _video_asset()
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 0


def test_valid_narration_passes(tmp_path):
    asset = _narration_asset()
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 0


# ── fail tests ────────────────────────────────────────────────────────────────

def test_screenshot_prepared_equals_input_fails(tmp_path):
    asset = _screenshot_asset(tmp_path, "sc-same", w=1280, h=720, same_prepared=True)
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1
    assert "crop required" in out.read_text()


def test_tall_screenshot_fails(tmp_path):
    # 752x6647 — renders at ~81px wide
    asset = _screenshot_asset(tmp_path, "sc-tall", w=752, h=6647)
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1
    assert "rendered width" in out.read_text()


def test_video_out_exceeds_duration_fails(tmp_path):
    asset = _video_asset(out_seconds=100.0, duration_seconds=96.0)
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1


def test_narration_missing_loudness_fails(tmp_path):
    asset = _narration_asset()
    del asset["loudness_lufs"]
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1
    assert "loudness_lufs" in out.read_text()


def test_narration_silence_gate_false_fails(tmp_path):
    asset = _narration_asset(silence_gate_passed=False)
    m = _manifest("ep", asset)
    out = tmp_path / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1
    assert "silence_gate_passed" in out.read_text()


# ── MD written even on failure ────────────────────────────────────────────────

def test_md_written_on_failure(tmp_path):
    asset = _screenshot_asset(tmp_path, "sc-tall", w=752, h=6647)
    m = _manifest("ep", asset)
    out = tmp_path / "deep" / "qc.md"
    rc = check_prepared_media(m, tmp_path, out)
    assert rc == 1
    assert out.exists()
    assert out.stat().st_size > 0


# ── report content ────────────────────────────────────────────────────────────

def test_report_contains_verdict_and_rows(tmp_path):
    sc = _screenshot_asset(tmp_path, "sc-land", w=1280, h=720)
    vid = _video_asset()
    nar = _narration_asset()
    m = _manifest("ep", sc, vid, nar)
    out = tmp_path / "qc.md"
    check_prepared_media(m, tmp_path, out)
    content = out.read_text()
    assert "verdict" in content.lower()
    assert "sc-land" in content
    assert "vid-001" in content
    assert "nar-001" in content
