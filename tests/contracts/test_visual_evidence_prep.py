"""Contract tests for the visual_evidence_prep stage output.

Validates that manifests produced according to the visual_evidence_prep-director
rules pass prepared_media_manifest.schema.json, and that invalid manifests fail.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas" / "artifacts" / "prepared_media_manifest.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(manifest: dict) -> list[str]:
    return [e.message for e in Draft7Validator(_schema()).iter_errors(manifest)]


# ── fixture builders ──────────────────────────────────────────────────────────

def _video_asset(asset_id: str = "receipt-001", **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "video",
        "role": "b-roll",
        "input_path": f"/project/clips/{asset_id}.mp4",
        "prepared_path": f"/project/clips/{asset_id}.mp4",
        "source_label_required": True,
        "source_label": "NBC News, Aug 2019",
        "preparation_status": "prepared",
        "qc_notes": "QC passed. 1920x1080, 30fps.",
        "in_seconds": 0.0,
        "out_seconds": 15.0,
        "duration_seconds": 96.0,
        "framing": "full_frame",
        "audio_role": "ambient",
    }
    base.update(overrides)
    return base


def _screenshot_asset(asset_id: str = "SC-01", **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "screenshot",
        "role": "proof",
        "input_path": f"/project/assets/{asset_id}.png",
        "prepared_path": f"/project/assets/{asset_id}.png",
        "source_label_required": True,
        "source_label": "Cloudflare CEO Blog, Aug 2019",
        "preparation_status": "prepared",
        "qc_notes": "Full-page scroll capture. Legible at 1280x720.",
        "legibility_ok": True,
        "framing": "full_page",
        "render_treatment": "scale_fit",
    }
    base.update(overrides)
    return base


def _narration_asset(asset_id: str = "NAR-01", **overrides) -> dict:
    base = {
        "asset_id": asset_id,
        "media_type": "audio",
        "role": "narration",
        "input_path": "/project/narration/narration_full.mp3",
        "prepared_path": "/project/narration/narration_full.mp3",
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "Fish Speech S2 Pro. Silence gate PASS.",
        "duration_seconds": 817.45,
        "audio_role": "narration",
        "loudness_lufs": -16.16,
        "silence_gate_passed": True,
    }
    base.update(overrides)
    return base


def _manifest(*assets: dict, operator_approved: bool = False) -> dict:
    return {
        "episode_id": "cloudflare-chokepoint-test",
        "operator_approved_for_staging": operator_approved,
        "assets": list(assets),
    }


# ── pass tests ────────────────────────────────────────────────────────────────

def test_valid_full_manifest_passes():
    m = _manifest(_video_asset(), _screenshot_asset(), _narration_asset())
    errors = _validate(m)
    assert errors == [], errors


def test_operator_approved_false_accepted():
    """Manifest written with operator_approved_for_staging=false must pass schema."""
    m = _manifest(_video_asset(), operator_approved=False)
    errors = _validate(m)
    assert errors == [], errors


def test_operator_approved_true_also_valid():
    m = _manifest(_video_asset(), operator_approved=True)
    errors = _validate(m)
    assert errors == [], errors


def test_quote_audio_maps_to_quoted_audio():
    """audio_role='quoted_audio' (mapped from original_audio_use='quote_audio') passes schema."""
    asset = _video_asset(audio_role="quoted_audio")
    m = _manifest(asset)
    errors = _validate(m)
    assert errors == [], errors


def test_muted_audio_role_passes():
    asset = _video_asset(audio_role="muted")
    m = _manifest(asset)
    assert _validate(m) == []


def test_ambient_audio_role_passes():
    asset = _video_asset(audio_role="ambient")
    m = _manifest(asset)
    assert _validate(m) == []


def test_video_only_manifest_passes():
    m = _manifest(_video_asset("r-001"), _video_asset("r-002"))
    assert _validate(m) == []


def test_screenshot_without_source_label_when_not_required_passes():
    asset = _screenshot_asset(source_label_required=False)
    del asset["source_label"]
    m = _manifest(asset)
    assert _validate(m) == []


# ── fail tests ────────────────────────────────────────────────────────────────

def test_source_label_missing_when_required_fails():
    """source_label_required=true without source_label must fail schema."""
    asset = _video_asset()
    del asset["source_label"]
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for missing source_label"


def test_narration_missing_loudness_lufs_fails():
    """Narration asset without loudness_lufs must fail schema."""
    asset = _narration_asset()
    del asset["loudness_lufs"]
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for missing loudness_lufs"


def test_narration_missing_silence_gate_fails():
    """Narration (role=narration) without silence_gate_passed must fail schema."""
    asset = _narration_asset()
    del asset["silence_gate_passed"]
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for missing silence_gate_passed"


def test_screenshot_missing_legibility_ok_fails():
    asset = _screenshot_asset()
    del asset["legibility_ok"]
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for missing legibility_ok"


def test_video_missing_in_seconds_fails():
    asset = _video_asset()
    del asset["in_seconds"]
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for missing in_seconds"


def test_invalid_preparation_status_fails():
    asset = _video_asset(preparation_status="already_prepared")
    m = _manifest(asset)
    errors = _validate(m)
    assert errors, "expected schema error for invalid preparation_status"


def test_empty_assets_array_fails():
    m = {"episode_id": "test", "operator_approved_for_staging": False, "assets": []}
    errors = _validate(m)
    assert errors, "expected schema error for empty assets array"


def test_missing_episode_id_fails():
    m = _manifest(_video_asset())
    del m["episode_id"]
    errors = _validate(m)
    assert errors, "expected schema error for missing episode_id"
