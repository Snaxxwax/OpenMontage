from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"


def test_retention_doctrine_exists_and_names_core_doctrine() -> None:
    text = (CHANNEL_DIR / "design" / "retention-doctrine.md").read_text(encoding="utf-8")
    for term in ["Coffeezilla", "MagnatesMedia", "case_file", "critical_error", "visual change every 3-6 seconds"]:
        assert term in text


def test_channel_docs_and_directors_reference_retention_contract() -> None:
    channel = (CHANNEL_DIR / "CHANNEL.md").read_text(encoding="utf-8")
    design = (CHANNEL_DIR / "DESIGN.md").read_text(encoding="utf-8")
    script = (CHANNEL_DIR / "skills" / "script-director.md").read_text(encoding="utf-8")
    media = (CHANNEL_DIR / "skills" / "media-director.md").read_text(encoding="utf-8")
    visual = (CHANNEL_DIR / "skills" / "review" / "visual-identity-reviewer.md").read_text(encoding="utf-8")
    render = (CHANNEL_DIR / "skills" / "review" / "render-qc-reviewer.md").read_text(encoding="utf-8")
    assert "retention-doctrine.md" in channel
    assert "design/channel-source-of-truth.md" in channel
    assert "Corporate True Crime" in channel
    assert "No WebGL" in channel and "Live research/data must be fetched before rendering" in channel
    for term in ["Case-file UI", "Cinematic metaphor", "Motion density", "crimson"]:
        assert term in design
    for term in ["Retention-first episode contract", "retention_device", "visual_mode", "evidence_refs", "Red state is scarce"]:
        assert term in script
    for term in ["case_file_sequence", "cinematic_metaphor", "illustrative_only", "Motion plan"]:
        assert term in media
    for term in ["cinematic case-building", "research deck", "illustrative", "red state"]:
        assert term in visual
    for term in ["static visual", "No mascot substitution", "Critical-error", "Illustrative"]:
        assert term in render


def test_modern_archivist_episode_schema_accepts_retention_timeline_block() -> None:
    schema = json.loads((CHANNEL_DIR / "schemas" / "episode.schema.json").read_text(encoding="utf-8"))
    episode = {
        "episode_id": "fixture",
        "title": "Fixture",
        "duration_seconds": 30,
        "sections": [{
            "id": "b001", "start": 0, "end": 8, "text": "The receipt was worse than the pitch.", "tags": [],
            "narrative_phase": "hook", "retention_device": "cold_open_shock", "visual_mode": "source_montage",
            "layout": "media_full", "color_state": "teal",
            "character": {"visible": False, "action": "hidden", "expression": "none"},
            "evidence_role": "primary_evidence", "evidence_refs": ["claim_001", "source_001"],
            "content_opportunity_refs": ["opp_001"],
            "media_overlay": {"type": "case_file_sequence", "beats": []}, "estimated_duration_seconds": 8,
        }],
    }
    Draft202012Validator(schema).validate(episode)


def test_modern_archivist_media_schema_accepts_retention_media_items() -> None:
    schema = json.loads((CHANNEL_DIR / "schemas" / "media.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    validator.validate({
        "id": "case-001", "kind": "case_file_sequence", "title": "The backup claim",
        "evidence_role": "primary_evidence", "evidence_refs": ["source_001"],
        "motion_plan": [{"at_seconds": 0, "action": "show_claim_card"}, {"at_seconds": 2, "action": "reveal_contradiction"}],
    })
    validator.validate({
        "id": "metaphor-001", "kind": "cinematic_metaphor", "title": "Server room goes dark",
        "evidence_role": "illustrative_only", "description": "Illustrative data-center darkness shot", "motion_plan": [],
    })
    validator.validate({
        "id": "source-001",
        "kind": "source_montage",
        "title": "Demo footage contradiction",
        "evidence_role": "primary_evidence",
        "evidence_refs": ["source_001"],
        "content_opportunity_refs": ["opp_001"],
        "runtime_affinity": "hyperframes",
        "rights_status": "needs_review",
        "local_assets": [{"path": "assets/source/demo-frame-001.png", "type": "image"}],
        "motion_plan": [{"at_seconds": 0, "action": "push_into_frame"}],
    })
    validator.validate({
        "id": "ui-001",
        "kind": "recreated_ui",
        "title": "Archived claim recreation",
        "evidence_role": "primary_evidence",
        "evidence_refs": ["source_002"],
        "content_opportunity_refs": ["opp_002"],
        "runtime_affinity": "either",
        "rights_status": "recreate_only",
        "local_assets": [],
        "segment_render": {"runtime": "hyperframes", "workspace_path": "assets/hyperframes/opp_002", "output_path": "assets/video/segments/opp_002.mp4", "status": "planned"},
        "motion_plan": [{"at_seconds": 0, "action": "highlight_claim"}],
    })


def test_channel_manifest_mentions_retention_case_file_and_motion_gates() -> None:
    manifest = yaml.safe_load((CHANNEL_DIR / "pipeline.yaml").read_text(encoding="utf-8"))
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    script_text = "\n".join(stages["script"]["review_focus"] + stages["script"]["success_criteria"])
    media_text = "\n".join(stages["media_manifest"]["review_focus"] + stages["media_manifest"]["success_criteria"])
    render_text = "\n".join(stages["render"]["review_focus"] + stages["render"]["success_criteria"])
    assert "structured retention timeline" in script_text
    assert "case-file" in media_text
    assert "Motion plans" in media_text or "motion" in media_text.lower()
    assert "visual variety" in render_text and "character returns" in render_text


def test_retention_fixture_keeps_critical_error_red_state_short() -> None:
    fixture = (CHANNEL_DIR / "remotion" / "src" / "fixtures.ts").read_text(encoding="utf-8")
    assert 'visual_mode: "critical_error"' in fixture
    assert 'color_state: "red"' in fixture
