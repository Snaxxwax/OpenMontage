"""Unit tests for scripts/asymmetric_stage_assets.py"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from asymmetric_stage_assets import StagingError, stage_assets  # noqa: E402


# ── PNG helpers (no PIL required) ─────────────────────────────────────────────

def _png_bytes(width: int = 10, height: int = 8) -> bytes:
    """Create a minimal valid PNG with known dimensions."""
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
    row = b"\x00" + b"\xFF\xFF\xFF" * width  # filter=None + white RGB pixels
    idat = chunk(b"IDAT", zlib.compress(row * height))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── manifest / file fixtures ──────────────────────────────────────────────────

def _write_file(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _screenshot_asset(asset_id: str, prepared_path: str, **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "screenshot",
        "role": "proof",
        "input_path": prepared_path,
        "prepared_path": prepared_path,
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "",
        "legibility_ok": True,
        "framing": "full",
        "render_treatment": "grade",
    }
    base.update(overrides)
    return base


def _video_asset(asset_id: str, prepared_path: str, **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "video",
        "role": "b-roll",
        "input_path": prepared_path,
        "prepared_path": prepared_path,
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "",
        "in_seconds": 5.0,
        "out_seconds": 15.0,
        "duration_seconds": 10.0,
        "framing": "full",
        "audio_role": "ambient",
    }
    base.update(overrides)
    return base


def _audio_asset(asset_id: str, prepared_path: str, **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "audio",
        "role": "sfx",
        "input_path": prepared_path,
        "prepared_path": prepared_path,
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "",
        "duration_seconds": 3.5,
        "audio_role": "sfx",
        "loudness_lufs": -20.0,
    }
    base.update(overrides)
    return base


def _write_manifest(manifest_dir: Path, assets: list[dict]) -> Path:
    manifest = {
        "episode_id": "ep001",
        "operator_approved_for_staging": True,
        "assets": assets,
    }
    path = manifest_dir / "prepared_media_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _run(manifest_path: Path, staging_base: Path, render_id: str = "ep001-r001", overwrite: bool = False) -> dict:
    return stage_assets(manifest_path, staging_base, render_id, overwrite=overwrite)


# ── copy tests ────────────────────────────────────────────────────────────────

def test_copies_screenshot_into_media(tmp_path):
    src = _write_file(tmp_path / "prepared" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "prepared/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    staged_root = result["staging_root"]
    assert (staged_root / "media" / "sc001.png").exists()


def test_copies_video_into_media(tmp_path):
    src = _write_file(tmp_path / "prepared" / "clip.mp4", b"fake-mp4-data")
    manifest = _write_manifest(tmp_path, [_video_asset("vid001", "prepared/clip.mp4")])
    result = _run(manifest, tmp_path / "staging")
    staged_root = result["staging_root"]
    assert (staged_root / "media" / "vid001.mp4").exists()


def test_copies_audio_into_audio_subdir(tmp_path):
    _write_file(tmp_path / "prepared" / "narration.wav", b"fake-wav-data")
    manifest = _write_manifest(tmp_path, [_audio_asset("aud001", "prepared/narration.wav")])
    result = _run(manifest, tmp_path / "staging")
    staged_root = result["staging_root"]
    assert (staged_root / "audio" / "aud001.wav").exists()


def test_copies_all_three_types(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    _write_file(tmp_path / "p" / "clip.mp4", b"fake-mp4")
    _write_file(tmp_path / "p" / "sfx.wav", b"fake-wav")
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "p/frame.png"),
        _video_asset("vid001", "p/clip.mp4"),
        _audio_asset("aud001", "p/sfx.wav"),
    ])
    result = _run(manifest, tmp_path / "staging")
    assert result["asset_count"] == 3


# ── manifest output tests ─────────────────────────────────────────────────────

def test_writes_staged_asset_manifest(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    staged_root = result["staging_root"]
    assert (staged_root / "staged_asset_manifest.json").exists()


def test_staged_manifest_gate_passed_is_false(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    manifest_out = json.loads(
        (result["staging_root"] / "staged_asset_manifest.json").read_text()
    )
    assert manifest_out["gate_passed"] is False


def test_staged_manifest_has_required_top_level_fields(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging", render_id="ep001-r001")
    manifest_out = json.loads(
        (result["staging_root"] / "staged_asset_manifest.json").read_text()
    )
    for key in ("render_id", "episode_id", "staged_at", "gate_passed", "assets"):
        assert key in manifest_out, f"missing key: {key}"
    assert manifest_out["render_id"] == "ep001-r001"
    assert manifest_out["episode_id"] == "ep001"


# ── QC report tests ───────────────────────────────────────────────────────────

def test_writes_staged_asset_qc_md(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    assert (result["staging_root"] / "staged_asset_qc.md").exists()


def test_qc_md_contains_render_id_and_asset_ids(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging", render_id="ep001-r099")
    qc_text = (result["staging_root"] / "staged_asset_qc.md").read_text()
    assert "ep001-r099" in qc_text
    assert "sc001" in qc_text


# ── staged_path relative tests ────────────────────────────────────────────────

def test_staged_paths_are_relative(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    _write_file(tmp_path / "p" / "clip.mp4", b"fake-mp4")
    _write_file(tmp_path / "p" / "sfx.wav", b"fake-wav")
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "p/frame.png"),
        _video_asset("vid001", "p/clip.mp4"),
        _audio_asset("aud001", "p/sfx.wav"),
    ])
    result = _run(manifest, tmp_path / "staging")
    for asset in result["manifest_out"]["assets"]:
        sp = asset["staged_path"]
        assert not sp.startswith("/"), f"staged_path is absolute: {sp!r}"
        assert ".." not in sp, f"staged_path contains traversal: {sp!r}"


def test_staged_paths_start_with_media_or_audio(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    _write_file(tmp_path / "p" / "sfx.wav", b"fake-wav")
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "p/frame.png"),
        _audio_asset("aud001", "p/sfx.wav"),
    ])
    result = _run(manifest, tmp_path / "staging")
    for asset in result["manifest_out"]["assets"]:
        sp = asset["staged_path"]
        assert sp.startswith("media/") or sp.startswith("audio/"), (
            f"staged_path has wrong prefix: {sp!r}"
        )


# ── sha256 tests ──────────────────────────────────────────────────────────────

def test_sha256_values_match_staged_files(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    _write_file(tmp_path / "p" / "clip.mp4", b"fake-mp4-content")
    _write_file(tmp_path / "p" / "sfx.wav", b"fake-wav-content")
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "p/frame.png"),
        _video_asset("vid001", "p/clip.mp4"),
        _audio_asset("aud001", "p/sfx.wav"),
    ])
    result = _run(manifest, tmp_path / "staging")
    staged_root = result["staging_root"]
    for asset in result["manifest_out"]["assets"]:
        staged_file = staged_root / asset["staged_path"]
        expected = _sha256(staged_file)
        assert asset["sha256"] == expected, (
            f"sha256 mismatch for {asset['asset_id']}: "
            f"got {asset['sha256']!r}, expected {expected!r}"
        )


def test_sha256_is_64_hex_chars(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    for asset in result["manifest_out"]["assets"]:
        sha = asset["sha256"]
        assert len(sha) == 64, f"sha256 wrong length: {len(sha)}"
        assert all(c in "0123456789abcdef" for c in sha), f"sha256 not lowercase hex: {sha!r}"


# ── screenshot dimensions test ────────────────────────────────────────────────

def test_screenshot_dimensions_recorded(tmp_path):
    w, h = 10, 8
    _write_file(tmp_path / "p" / "frame.png", _png_bytes(w, h))
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging")
    asset_out = result["manifest_out"]["assets"][0]
    assert "dimensions" in asset_out

    try:
        from PIL import Image  # noqa: F401
        has_pil = True
    except ImportError:
        has_pil = False

    dims = asset_out["dimensions"]
    assert isinstance(dims, dict)
    assert "width" in dims and "height" in dims
    if has_pil:
        assert dims["width"] == w
        assert dims["height"] == h


# ── failure tests ─────────────────────────────────────────────────────────────

def test_fails_on_missing_prepared_path(tmp_path):
    # File does not exist on disk
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "prepared/ghost.png")
    ])
    with pytest.raises(StagingError, match="not found"):
        _run(manifest, tmp_path / "staging")


def test_fails_on_zero_byte_file(tmp_path):
    _write_file(tmp_path / "p" / "empty.png", b"")
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/empty.png")])
    with pytest.raises(StagingError, match="zero-byte"):
        _run(manifest, tmp_path / "staging")


def test_fails_on_path_escape(tmp_path):
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "../../etc/passwd")
    ])
    with pytest.raises(StagingError, match="traversal"):
        _run(manifest, tmp_path / "staging")


def test_fails_on_path_escape_double_dot_mid(tmp_path):
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "prepared/../../../secret.png")
    ])
    with pytest.raises(StagingError, match="traversal"):
        _run(manifest, tmp_path / "staging")


# ── overwrite tests ───────────────────────────────────────────────────────────

def test_refuses_existing_staging_dir_without_overwrite(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    staging_base = tmp_path / "staging"
    _run(manifest, staging_base, render_id="ep001-r001")
    # Second run without --overwrite must fail
    with pytest.raises(StagingError, match="already exists"):
        _run(manifest, staging_base, render_id="ep001-r001", overwrite=False)


def test_overwrites_existing_staging_dir_with_flag(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    staging_base = tmp_path / "staging"
    _run(manifest, staging_base, render_id="ep001-r001")
    # Second run with overwrite=True must succeed
    result = _run(manifest, staging_base, render_id="ep001-r001", overwrite=True)
    assert result["asset_count"] == 1


# ── operator approval tests ───────────────────────────────────────────────────

def test_refuses_when_operator_not_approved(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest_path = tmp_path / "prepared_media_manifest.json"
    manifest_path.write_text(json.dumps({
        "episode_id": "ep001",
        "operator_approved_for_staging": False,
        "assets": [_screenshot_asset("sc001", "p/frame.png")],
    }), encoding="utf-8")
    with pytest.raises(StagingError, match="operator_approved_for_staging"):
        _run(manifest_path, tmp_path / "staging")


# ── render_id validation tests ────────────────────────────────────────────────

def test_bad_render_id_rejected(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    with pytest.raises(StagingError, match="render_id"):
        _run(manifest, tmp_path / "staging", render_id="INVALID ID!")


def test_valid_render_id_with_hyphens_accepted(tmp_path):
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [_screenshot_asset("sc001", "p/frame.png")])
    result = _run(manifest, tmp_path / "staging", render_id="ep001-render-20260515")
    assert result["render_id"] == "ep001-render-20260515"


# ── staging cleans up on failure ──────────────────────────────────────────────

def test_staging_dir_removed_on_failure(tmp_path):
    # First asset ok, second missing → whole staging dir removed
    _write_file(tmp_path / "p" / "frame.png", _png_bytes())
    manifest = _write_manifest(tmp_path, [
        _screenshot_asset("sc001", "p/frame.png"),
        _screenshot_asset("sc002", "p/ghost.png"),  # missing
    ])
    staging_base = tmp_path / "staging"
    with pytest.raises(StagingError):
        _run(manifest, staging_base, render_id="ep001-r001")
    assert not (staging_base / "ep001-r001").exists()
