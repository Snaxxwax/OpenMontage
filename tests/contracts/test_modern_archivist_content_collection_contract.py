from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"


def _schema() -> dict:
    return json.loads((CHANNEL_DIR / "schemas" / "content_collection.schema.json").read_text(encoding="utf-8"))


def test_channel_source_of_truth_names_corporate_true_crime_visual_policy() -> None:
    text = (CHANNEL_DIR / "design" / "channel-source-of-truth.md").read_text(encoding="utf-8")
    for term in [
        "Corporate True Crime",
        "Documents, charts, filings, and graphs are evidence. They are not the show.",
        "source footage",
        "Recreated digital artifacts",
        "content_collection",
        "runtime affinity",
        "Remotion remains the canonical final renderer",
        "HyperFrames is a first-class optional runtime",
    ]:
        assert term in text


def test_content_collection_schema_accepts_source_footage_artifact_packet() -> None:
    packet = {
        "episode_id": "nikola-fake-truck",
        "visual_thesis": "The company sold motion before it sold a working truck.",
        "topic_gate": {
            "stakes": True,
            "failure_mechanism": True,
            "visual_artifacts": True,
            "public_evidence": True,
            "human_consequence": False,
            "decision": "greenlight",
            "notes": "Strong source footage and SEC/legal trail.",
        },
        "opportunities": [
            {
                "id": "opp_001",
                "kind": "source_footage",
                "title": "Truck demo sequence",
                "source_url": "https://example.com/demo",
                "evidence_refs": ["source_001"],
                "rights_status": "needs_review",
                "evidence_role": "primary_evidence",
                "runtime_affinity": "remotion",
                "visual_mode": "source_montage",
                "motion_plan": [
                    {"at_seconds": 0, "action": "show_source_frame"},
                    {"at_seconds": 3, "action": "reveal_contradiction_label"},
                ],
                "script_use": "cold_open",
            }
        ],
        "coverage_report": {
            "source_footage_count": 1,
            "recreated_artifact_count": 0,
            "document_only_count": 0,
            "chart_only_count": 0,
            "visual_feasibility": "strong",
            "boring_visual_risk": "low",
        },
    }
    Draft202012Validator(_schema()).validate(packet)


def test_content_collection_template_validates() -> None:
    template = json.loads((CHANNEL_DIR / "templates" / "content_collection.example.json").read_text(encoding="utf-8"))
    Draft202012Validator(_schema()).validate(template)


def test_content_collection_director_encodes_source_footage_first_policy() -> None:
    text = (CHANNEL_DIR / "skills" / "content-collection-director.md").read_text(encoding="utf-8")
    for term in [
        "What can we actually show?",
        "source footage",
        "recreated digital artifacts",
        "Documents, charts, filings, and graphs are evidence. They are not the show.",
        "runtime_affinity",
        "rights_status",
        "greenlight",
        "Reject or park a topic if it only has filings and charts",
    ]:
        assert term in text


def test_channel_pipeline_inserts_content_collection_before_script() -> None:
    manifest = yaml.safe_load((CHANNEL_DIR / "pipeline.yaml").read_text(encoding="utf-8"))
    stage_names = [stage["name"] for stage in manifest["stages"]]
    assert stage_names.index("research") < stage_names.index("content_collection") < stage_names.index("script")
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    content = stages["content_collection"]
    assert content["skill"] == "channels/modern-archivist/skills/content-collection-director.md"
    assert content["required_artifacts_in"] == ["research_packet"]
    assert content["produces"] == ["content_collection"]
    assert content["checkpoint_required"] is True
    assert "source footage" in "\n".join(content["review_focus"]).lower()
    assert "filings and charts" in "\n".join(content["review_focus"] + content["success_criteria"]).lower()


def test_script_stage_requires_content_collection() -> None:
    manifest = yaml.safe_load((CHANNEL_DIR / "pipeline.yaml").read_text(encoding="utf-8"))
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    assert "content_collection" in stages["script"]["required_artifacts_in"]


def test_script_director_requires_content_collection_visual_opportunities() -> None:
    text = (CHANNEL_DIR / "skills" / "script-director.md").read_text(encoding="utf-8")
    for term in [
        "content_collection",
        "visual opportunity",
        "opportunity IDs",
        "Do not write scenes around abstract ideas when the content_collection packet lacks visual material",
        "source-footage/artifact-first",
    ]:
        assert term in text


def test_media_director_maps_content_collection_to_local_render_inputs() -> None:
    text = (CHANNEL_DIR / "skills" / "media-director.md").read_text(encoding="utf-8")
    for term in [
        "content_collection",
        "opportunity IDs",
        "local render inputs",
        "rights_status",
        "runtime_affinity",
        "source_montage",
        "recreated_ui",
    ]:
        assert term in text


def test_reviewers_guard_against_document_chart_channel_drift() -> None:
    files = [
        CHANNEL_DIR / "skills" / "review" / "evidence-auditor.md",
        CHANNEL_DIR / "skills" / "review" / "visual-identity-reviewer.md",
        CHANNEL_DIR / "skills" / "review" / "render-qc-reviewer.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for term in [
        "document-only",
        "chart-only",
        "source-footage/artifact-first",
        "boring visual risk",
        "content_collection",
    ]:
        assert term in combined


def test_nikola_fixture_exercises_source_montage_and_recreated_ui() -> None:
    fixture = (CHANNEL_DIR / "remotion" / "src" / "fixtures.ts").read_text(encoding="utf-8")
    for term in [
        "nikolaContentFixture",
        'kind: "source_montage"',
        'kind: "recreated_ui"',
        'visual_mode: "source_montage"',
        'visual_mode: "recreated_ui"',
        'content_opportunity_refs: ["opp_001"]',
        'content_opportunity_refs: ["opp_002"]',
    ]:
        assert term in fixture


def test_render_director_uses_runtime_affinity_without_silent_swaps() -> None:
    text = (CHANNEL_DIR / "skills" / "render-director.md").read_text(encoding="utf-8")
    for term in [
        "runtime_affinity",
        "Remotion remains the canonical final renderer",
        "HyperFrames",
        "local segment assets",
        "Do not silently swap runtimes",
        "render_runtime_selection",
    ]:
        assert term in text
