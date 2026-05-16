"""Contract tests for the render-asset-staging gate."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from asymmetric_gate import run_staging_gate  # noqa: E402


# ── PNG helper (no PIL required) ──────────────────────────────────────────────

def _png_bytes(width: int = 10, height: int = 8) -> bytes:
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── asset fixture helpers ─────────────────────────────────────────────────────

def _screenshot(asset_id: str = "sc001", w: int = 10, h: int = 8, **overrides: Any) -> tuple[dict, bytes]:
    content = _png_bytes(w, h)
    asset: dict[str, Any] = {
        "asset_id": asset_id,
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "/prepared/frame.png",
        "staged_path": f"media/{asset_id}.png",
        "sha256": "PLACEHOLDER",
        "source_label_required": False,
        "qc_status": "pending",
        "dimensions": {"width": w, "height": h},
    }
    asset.update(overrides)
    return asset, content


def _video(asset_id: str = "vid001", **overrides: Any) -> tuple[dict, bytes]:
    content = b"fake-mp4-content"
    asset: dict[str, Any] = {
        "asset_id": asset_id,
        "asset_type": "video",
        "role": "b-roll",
        "source_path": "/prepared/clip.mp4",
        "staged_path": f"media/{asset_id}.mp4",
        "sha256": "PLACEHOLDER",
        "source_label_required": False,
        "qc_status": "pending",
        "duration_seconds": 10.0,
        "in_seconds": 0.0,
        "out_seconds": 9.0,
        "audio_role": "ambient",
    }
    asset.update(overrides)
    return asset, content


def _audio(asset_id: str = "aud001", **overrides: Any) -> tuple[dict, bytes]:
    content = b"fake-wav-content"
    asset: dict[str, Any] = {
        "asset_id": asset_id,
        "asset_type": "audio",
        "role": "sfx",
        "source_path": "/prepared/sfx.wav",
        "staged_path": f"audio/{asset_id}.wav",
        "sha256": "PLACEHOLDER",
        "source_label_required": False,
        "qc_status": "pending",
        "duration_seconds": 3.5,
        "audio_role": "sfx",
    }
    asset.update(overrides)
    return asset, content


# ── staging dir builder ───────────────────────────────────────────────────────

def _make_staging(
    tmp_path: Path,
    pairs: list[tuple[dict, bytes]],
    render_id: str = "ep001-r001",
    extra_files: dict[str, bytes] | None = None,
) -> Path:
    """Write staged files + manifest to a temp staging dir. Returns manifest_path."""
    staging_root = tmp_path / "staging" / render_id
    staging_root.mkdir(parents=True)

    staged_assets = []
    for asset_dict, content in pairs:
        staged_path = asset_dict["staged_path"]
        dest = staging_root / staged_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        asset_with_sha = {**asset_dict, "sha256": _sha256(content)}
        staged_assets.append(asset_with_sha)

    if extra_files:
        for rel, content in extra_files.items():
            f = staging_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(content)

    manifest: dict[str, Any] = {
        "render_id": render_id,
        "episode_id": "ep001",
        "staged_at": "2026-05-15T12:00:00Z",
        "gate_passed": False,
        "assets": staged_assets,
    }
    manifest_path = staging_root / "staged_asset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def _make_raw_manifest(
    tmp_path: Path,
    assets: list[dict],
    render_id: str = "ep001-r001",
    write_files: dict[str, bytes] | None = None,
) -> Path:
    """Write a manifest from raw dicts (no sha256 computation). For invalid-manifest tests."""
    staging_root = tmp_path / "staging" / render_id
    staging_root.mkdir(parents=True)

    if write_files:
        for rel, content in write_files.items():
            f = staging_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(content)

    manifest: dict[str, Any] = {
        "render_id": render_id,
        "episode_id": "ep001",
        "staged_at": "2026-05-15T12:00:00Z",
        "gate_passed": False,
        "assets": assets,
    }
    manifest_path = staging_root / "staged_asset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


# ── pass tests ────────────────────────────────────────────────────────────────

def test_valid_staged_manifest_passes(tmp_path):
    manifest_path = _make_staging(tmp_path, [
        _screenshot(),
        _video(),
        _audio(),
    ])
    result = run_staging_gate(manifest_path)
    assert result.ok, f"expected pass, got failures: {result.reasons}"
    assert result.reasons == []


def test_valid_manifest_writes_qc_report(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    run_staging_gate(manifest_path)
    assert (manifest_path.parent / "staged_asset_qc.md").exists()


def test_valid_manifest_qc_report_says_pass(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    run_staging_gate(manifest_path)
    qc_text = (manifest_path.parent / "staged_asset_qc.md").read_text()
    assert "PASS" in qc_text


# ── file existence / integrity tests ─────────────────────────────────────────

def test_missing_staged_file_fails(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    (manifest_path.parent / "media" / "sc001.png").unlink()
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("not found" in r for r in result.reasons)


def test_zero_byte_staged_file_fails(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    (manifest_path.parent / "media" / "sc001.png").write_bytes(b"")
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("zero-byte" in r for r in result.reasons)


def test_sha256_mismatch_fails(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    # Overwrite with different (non-empty) content after manifest is written
    (manifest_path.parent / "media" / "sc001.png").write_bytes(b"tampered-content")
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("sha256" in r for r in result.reasons)


def test_sha256_mismatch_qc_report_written(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    (manifest_path.parent / "media" / "sc001.png").write_bytes(b"tampered")
    run_staging_gate(manifest_path)
    assert (manifest_path.parent / "staged_asset_qc.md").exists()


# ── orphan file test ──────────────────────────────────────────────────────────

def test_orphan_staged_file_fails(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    # Plant a file in media/ that's not in the manifest
    (manifest_path.parent / "media" / "orphan.png").write_bytes(b"orphan-content")
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("orphan" in r for r in result.reasons)


def test_orphan_in_audio_dir_fails(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    (manifest_path.parent / "audio").mkdir(exist_ok=True)
    (manifest_path.parent / "audio" / "rogue.wav").write_bytes(b"rogue")
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("orphan" in r for r in result.reasons)


# ── source label test ─────────────────────────────────────────────────────────

def test_source_label_missing_fails(tmp_path):
    content = _png_bytes()
    # Manifest with source_label_required=True but no source_label
    # Schema validation will catch this.
    asset = {
        "asset_id": "sc001",
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "/prepared/frame.png",
        "staged_path": "media/sc001.png",
        "sha256": _sha256(content),
        "source_label_required": True,
        # source_label deliberately absent
        "qc_status": "pending",
        "dimensions": {"width": 10, "height": 8},
    }
    manifest_path = _make_raw_manifest(
        tmp_path, [asset], write_files={"media/sc001.png": content}
    )
    result = run_staging_gate(manifest_path)
    assert not result.ok


# ── staged_path escape test ───────────────────────────────────────────────────

def test_staged_path_escape_fails(tmp_path):
    # staged_path with traversal — schema pattern rejects it
    asset = {
        "asset_id": "sc001",
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "/prepared/frame.png",
        "staged_path": "../evil/frame.png",
        "sha256": "a" * 64,
        "source_label_required": False,
        "qc_status": "pending",
        "dimensions": {"width": 10, "height": 8},
    }
    manifest_path = _make_raw_manifest(tmp_path, [asset])
    result = run_staging_gate(manifest_path)
    assert not result.ok


def test_staged_path_no_prefix_fails(tmp_path):
    # staged_path not starting with media/ or audio/
    asset = {
        "asset_id": "sc001",
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "/prepared/frame.png",
        "staged_path": "tmp/sc001.png",
        "sha256": "a" * 64,
        "source_label_required": False,
        "qc_status": "pending",
        "dimensions": {"width": 10, "height": 8},
    }
    manifest_path = _make_raw_manifest(tmp_path, [asset])
    result = run_staging_gate(manifest_path)
    assert not result.ok


# ── screenshot dimensions test ────────────────────────────────────────────────

def test_screenshot_missing_dimensions_fails(tmp_path):
    # Dimensions present but zero (PIL unavailable fallback).
    # Schema enforces minimum: 1 for width/height, so schema validation catches it first.
    asset, content = _screenshot(w=10, h=8)
    asset["dimensions"] = {"width": 0, "height": 0}
    manifest_path = _make_staging(tmp_path, [(asset, content)])
    result = run_staging_gate(manifest_path)
    assert not result.ok  # schema or gate rejects zero dimensions


def test_screenshot_valid_dimensions_passes(tmp_path):
    asset, content = _screenshot(w=1920, h=1080)
    manifest_path = _make_staging(tmp_path, [(asset, content)])
    result = run_staging_gate(manifest_path)
    assert result.ok


# ── video timing test ─────────────────────────────────────────────────────────

def test_video_out_seconds_exceeds_duration_fails(tmp_path):
    asset, content = _video(duration_seconds=10.0, out_seconds=15.0)
    manifest_path = _make_staging(tmp_path, [(asset, content)])
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert any("out_seconds" in r for r in result.reasons)


def test_video_out_seconds_equals_duration_passes(tmp_path):
    # out_seconds == duration_seconds is valid (takes entire clip)
    asset, content = _video(duration_seconds=10.0, out_seconds=10.0)
    manifest_path = _make_staging(tmp_path, [(asset, content)])
    result = run_staging_gate(manifest_path)
    assert result.ok


# ── narration loudness test ───────────────────────────────────────────────────

def test_narration_missing_loudness_lufs_fails(tmp_path):
    # Schema requires loudness_lufs for narration — write raw manifest without it
    content = b"fake-narration"
    asset = {
        "asset_id": "aud001",
        "asset_type": "audio",
        "role": "narration",
        "source_path": "/prepared/narration.wav",
        "staged_path": "audio/aud001.wav",
        "sha256": _sha256(content),
        "source_label_required": False,
        "qc_status": "pending",
        "duration_seconds": 60.0,
        "audio_role": "narration",
        # loudness_lufs deliberately absent
    }
    manifest_path = _make_raw_manifest(
        tmp_path, [asset], write_files={"audio/aud001.wav": content}
    )
    result = run_staging_gate(manifest_path)
    assert not result.ok


def test_narration_with_loudness_lufs_passes(tmp_path):
    asset, content = _audio(role="narration", loudness_lufs=-18.5, audio_role="narration")
    manifest_path = _make_staging(tmp_path, [(asset, content)])
    result = run_staging_gate(manifest_path)
    assert result.ok


# ── gate_passed update tests ──────────────────────────────────────────────────

def test_gate_passed_set_true_on_success(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    assert json.loads(manifest_path.read_text())["gate_passed"] is False
    result = run_staging_gate(manifest_path)
    assert result.ok
    assert json.loads(manifest_path.read_text())["gate_passed"] is True


def test_gate_passed_not_changed_on_failure(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    # Corrupt the staged file to force failure
    (manifest_path.parent / "media" / "sc001.png").write_bytes(b"tampered")
    result = run_staging_gate(manifest_path)
    assert not result.ok
    assert json.loads(manifest_path.read_text())["gate_passed"] is False


def test_qc_report_written_on_failure_too(tmp_path):
    manifest_path = _make_staging(tmp_path, [_screenshot()])
    (manifest_path.parent / "media" / "sc001.png").unlink()
    run_staging_gate(manifest_path)
    assert (manifest_path.parent / "staged_asset_qc.md").exists()
    qc_text = (manifest_path.parent / "staged_asset_qc.md").read_text()
    assert "FAIL" in qc_text
