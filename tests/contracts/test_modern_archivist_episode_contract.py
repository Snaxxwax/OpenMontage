from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"
SCHEMA_PATH = CHANNEL_DIR / "schemas" / "episode.schema.json"


def test_episode_contract_requires_retention_devices() -> None:
    """Ensure that episode sections have required retention-related fields."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)

    # Fixture demonstrating the failure mode
    episode_without_retention = {
        "episode_id": "test_missing_retention",
        "title": "Test Missing Retention Devices",
        "duration_seconds": 30,
        "sections": [{
            "id": "sec_001",
            "start": 0,
            "end": 10,
            "text": "Missing retention fields",
            "tags": [],
            # Intentionally omitting retention-related fields
        }]
    }

    # Fixture with complete retention information
    episode_with_retention = {
        "episode_id": "test_complete_retention",
        "title": "Test Complete Retention Devices",
        "duration_seconds": 30,
        "sections": [{
            "id": "sec_001",
            "start": 0,
            "end": 10,
            "text": "Proper retention fields",
            "tags": [],
            "narrative_phase": "hook",
            "retention_device": "cold_open_shock",
            "visual_mode": "source_montage",
            "layout": "media_full",
            "color_state": "teal",
            "evidence_role": "primary_evidence",
            "evidence_refs": ["claim_001"],
            "estimated_duration_seconds": 10
        }]
    }

    validator = Draft202012Validator(schema)

    # Validate the retention-complete version (should pass)
    validator.validate(episode_with_retention)

    # Validate the retention-incomplete version (should fail)
    try:
        validator.validate(episode_without_retention)
        assert False, "Validation should fail for missing retention fields"
    except ValidationError:
        pass


def test_episode_section_enforces_retention_constraints() -> None:
    """Validate specific retention-related constraints in section definition."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema)

    # Fixture testing narrative phase
    episode_with_narrative_phase = {
        "episode_id": "test_narrative_phase",
        "title": "Test Narrative Phase",
        "duration_seconds": 30,
        "sections": [{
            "id": "sec_001",
            "start": 0,
            "end": 10,
            "text": "Section with narrative phase",
            "tags": [],
            "narrative_phase": "hook",  # Must be one of the predefined phases
            "retention_device": "cold_open_shock",
            "visual_mode": "source_montage",
            "layout": "media_full",
            "color_state": "teal",
            "evidence_role": "primary_evidence",
            "evidence_refs": ["claim_001"],
            "estimated_duration_seconds": 10
        }]
    }

    # Validate the narrative-phase version
    validator.validate(episode_with_narrative_phase)

    # Test invalid narrative phase
    episode_with_invalid_narrative_phase = episode_with_narrative_phase.copy()
    episode_with_invalid_narrative_phase["sections"][0]["narrative_phase"] = "invalid_phase"

    try:
        validator.validate(episode_with_invalid_narrative_phase)
        assert False, "Validation should fail for invalid narrative phase"
    except ValidationError:
        pass


def test_episode_section_ensures_minimal_retention_metadata() -> None:
    """Ensure sections include minimum retention-related metadata."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema)

    # Comprehensive test fixture
    comprehensive_episode = {
        "episode_id": "test_comprehensive_retention",
        "title": "Comprehensive Retention Test",
        "duration_seconds": 180,
        "sections": [
            {
                "id": "hook_section",
                "start": 0,
                "end": 30,
                "text": "Cold open with strong retention device",
                "tags": ["hook", "retention_critical"],
                "narrative_phase": "hook",
                "retention_device": "cold_open_shock",
                "visual_mode": "source_montage",
                "layout": "media_full",
                "color_state": "teal",
                "evidence_role": "primary_evidence",
                "evidence_refs": ["claim_001"],
                "content_opportunity_refs": ["opp_001"],
                "estimated_duration_seconds": 30,
                "media_overlay": {
                    "type": "case_file_sequence",
                    "motion_plan": [
                        {"at_seconds": 0, "action": "reveal_contradiction"}
                    ]
                }
            },
            {
                "id": "deep_dive_section",
                "start": 30,
                "end": 120,
                "text": "Detailed exploration of the failure",
                "tags": ["deep_dive", "evidence"],
                "narrative_phase": "deep_dive",
                "retention_device": "contradiction_reveal",
                "visual_mode": "case_file",
                "layout": "split_screen_left",
                "color_state": "teal",
                "evidence_role": "secondary_evidence",
                "evidence_refs": ["claim_002", "claim_003"],
                "estimated_duration_seconds": 90
            }
        ]
    }

    validator.validate(comprehensive_episode)