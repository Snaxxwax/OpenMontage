"""Contract tests for prepared_media_manifest and staged_asset_manifest schemas."""

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_DIR = PROJECT_ROOT / "schemas" / "artifacts"

_PREPARED_SCHEMA = json.loads(
    (SCHEMA_DIR / "prepared_media_manifest.schema.json").read_text()
)
_STAGED_SCHEMA = json.loads(
    (SCHEMA_DIR / "staged_asset_manifest.schema.json").read_text()
)

_SHA256 = "a" * 64  # 64 hex chars


def _validate_prepared(doc: dict) -> None:
    Draft7Validator(_PREPARED_SCHEMA).validate(doc)


def _validate_staged(doc: dict) -> None:
    Draft7Validator(_STAGED_SCHEMA).validate(doc)


# ── prepared manifest fixtures ────────────────────────────────────────────────

def _screenshot_asset(**overrides) -> dict:
    base = {
        "asset_id": "sc001",
        "media_type": "screenshot",
        "role": "proof",
        "input_path": "raw/screenshot.png",
        "prepared_path": "prepared/screenshot.png",
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "",
        "legibility_ok": True,
        "framing": "full",
        "render_treatment": "grade",
    }
    base.update(overrides)
    return base


def _video_asset(**overrides) -> dict:
    base = {
        "asset_id": "vid001",
        "media_type": "video",
        "role": "b-roll",
        "input_path": "raw/clip.mp4",
        "prepared_path": "prepared/clip.mp4",
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


def _audio_asset(**overrides) -> dict:
    base = {
        "asset_id": "aud001",
        "media_type": "audio",
        "role": "sfx",
        "input_path": "raw/sfx.wav",
        "prepared_path": "prepared/sfx.wav",
        "source_label_required": False,
        "preparation_status": "prepared",
        "qc_notes": "",
        "duration_seconds": 3.5,
        "audio_role": "sfx",
        "loudness_lufs": -20.0,
    }
    base.update(overrides)
    return base


def _prepared_manifest(*assets) -> dict:
    return {
        "episode_id": "ep001",
        "operator_approved_for_staging": True,
        "assets": list(assets) if assets else [_screenshot_asset()],
    }


# ── staged manifest fixtures ──────────────────────────────────────────────────

def _staged_screenshot(**overrides) -> dict:
    base = {
        "asset_id": "sc001",
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "prepared/screenshot.png",
        "staged_path": "media/screenshot.png",
        "sha256": _SHA256,
        "source_label_required": False,
        "qc_status": "pass",
        "dimensions": {"width": 1920, "height": 1080},
    }
    base.update(overrides)
    return base


def _staged_video(**overrides) -> dict:
    base = {
        "asset_id": "vid001",
        "asset_type": "video",
        "role": "b-roll",
        "source_path": "prepared/clip.mp4",
        "staged_path": "media/clip.mp4",
        "sha256": _SHA256,
        "source_label_required": False,
        "qc_status": "pass",
        "duration_seconds": 10.0,
        "in_seconds": 5.0,
        "out_seconds": 15.0,
        "audio_role": "ambient",
    }
    base.update(overrides)
    return base


def _staged_audio(**overrides) -> dict:
    base = {
        "asset_id": "aud001",
        "asset_type": "audio",
        "role": "sfx",
        "source_path": "prepared/sfx.wav",
        "staged_path": "audio/sfx.wav",
        "sha256": _SHA256,
        "source_label_required": False,
        "qc_status": "pass",
        "duration_seconds": 3.5,
        "audio_role": "sfx",
    }
    base.update(overrides)
    return base


def _staged_manifest(*assets) -> dict:
    return {
        "render_id": "ep001-render-001",
        "episode_id": "ep001",
        "staged_at": "2026-05-15T12:00:00Z",
        "gate_passed": True,
        "assets": list(assets) if assets else [_staged_screenshot()],
    }


# ── prepared manifest tests ───────────────────────────────────────────────────

def test_valid_prepared_manifest_passes():
    doc = _prepared_manifest(
        _screenshot_asset(),
        _video_asset(),
        _audio_asset(),
    )
    _validate_prepared(doc)  # must not raise


def test_prepared_manifest_missing_required_source_label_fails():
    asset = _screenshot_asset(source_label_required=True)
    # source_label deliberately absent
    assert "source_label" not in asset
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


def test_prepared_video_missing_in_out_fails():
    asset = _video_asset()
    del asset["in_seconds"]
    del asset["out_seconds"]
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


def test_prepared_narration_missing_loudness_fails():
    # narration audio must have loudness_lufs (required by media_type=audio)
    asset = _audio_asset(role="narration", silence_gate_passed=True)
    del asset["loudness_lufs"]
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


def test_prepared_screenshot_missing_legibility_fails():
    asset = _screenshot_asset()
    del asset["legibility_ok"]
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


def test_prepared_narration_missing_silence_gate_fails():
    # role=narration requires silence_gate_passed
    asset = _audio_asset(role="narration")
    assert "silence_gate_passed" not in asset
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


def test_prepared_manifest_missing_episode_id_fails():
    doc = _prepared_manifest()
    del doc["episode_id"]
    with pytest.raises(ValidationError):
        _validate_prepared(doc)


def test_prepared_manifest_invalid_media_type_fails():
    asset = _screenshot_asset(media_type="pdf")
    with pytest.raises(ValidationError):
        _validate_prepared(_prepared_manifest(asset))


# ── staged manifest tests ─────────────────────────────────────────────────────

def test_valid_staged_manifest_passes():
    doc = _staged_manifest(
        _staged_screenshot(),
        _staged_video(),
        _staged_audio(),
    )
    _validate_staged(doc)  # must not raise


def test_staged_path_escape_fails():
    asset = _staged_screenshot(staged_path="media/../etc/passwd")
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_bad_sha256_fails():
    # too short and uppercase
    asset = _staged_screenshot(sha256="DEADBEEF")
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_missing_required_source_label_fails():
    asset = _staged_screenshot(source_label_required=True)
    assert "source_label" not in asset
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_audio_path_outside_audio_media_fails():
    asset = _staged_audio(staged_path="tmp/narration.mp3")
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_bad_render_id_fails():
    doc = _staged_manifest()
    doc["render_id"] = "RENDER 01"  # uppercase + space
    with pytest.raises(ValidationError):
        _validate_staged(doc)


def test_staged_render_id_with_leading_dash_fails():
    doc = _staged_manifest()
    doc["render_id"] = "-bad-id"
    with pytest.raises(ValidationError):
        _validate_staged(doc)


def test_staged_screenshot_missing_dimensions_fails():
    asset = _staged_screenshot()
    del asset["dimensions"]
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_video_missing_in_out_fails():
    asset = _staged_video()
    del asset["in_seconds"]
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_narration_missing_loudness_lufs_fails():
    asset = _staged_audio(role="narration")
    assert "loudness_lufs" not in asset
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_path_no_prefix_fails():
    asset = _staged_screenshot(staged_path="screenshots/frame.png")
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_path_absolute_fails():
    asset = _staged_screenshot(staged_path="/media/screenshot.png")
    with pytest.raises(ValidationError):
        _validate_staged(_staged_manifest(asset))


def test_staged_path_subdir_valid():
    asset = _staged_video(staged_path="media/clips/scene01.mp4")
    _validate_staged(_staged_manifest(asset))  # must not raise


def test_staged_gate_passed_must_be_bool():
    doc = _staged_manifest()
    doc["gate_passed"] = "true"
    with pytest.raises(ValidationError):
        _validate_staged(doc)
