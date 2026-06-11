from __future__ import annotations

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from lib.pipeline_loader import (
    discover_channel_packages,
    list_channel_pipelines,
    load_channel_package,
    load_pipeline,
)

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"
PACKAGE_PATH = CHANNEL_DIR / "package.yaml"
PACKAGE_SCHEMA_PATH = ROOT / "schemas" / "channels" / "channel_package.schema.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_modern_archivist_declares_channel_package_metadata() -> None:
    package = load_channel_package("modern-archivist")
    schema = load_yaml(PACKAGE_SCHEMA_PATH)
    Draft202012Validator(schema).validate(package)

    assert package["name"] == "modern-archivist"
    assert package["package_type"] == "openmontage-channel"
    assert package["canonical_pipeline"] == "pipeline.yaml"
    assert package["canonical_renderer"] == "remotion"
    assert package["entrypoints"]["remotion_composition"] == "ModernArchivist"


def test_modern_archivist_official_video_compose_contract() -> None:
    from tools.video.video_compose import VideoCompose

    package = load_channel_package("modern-archivist")

    assert package["canonical_renderer"] == "remotion"
    assert package["entrypoints"]["remotion_composition"] == "ModernArchivist"
    assert VideoCompose._get_composition_id("modern-archivist") == "ModernArchivist"


def test_modern_archivist_package_paths_resolve_inside_declared_boundary() -> None:
    package = load_channel_package("modern-archivist")

    assert (CHANNEL_DIR / package["canonical_pipeline"]).exists()
    assert (CHANNEL_DIR / package["entrypoints"]["channel_doc"]).exists()
    assert (CHANNEL_DIR / package["entrypoints"]["design_doc"]).exists()

    for key in ["skills", "schemas", "templates", "assets", "remotion_src", "remotion_public"]:
        path = (CHANNEL_DIR / package["paths"][key]).resolve()
        assert path.exists(), f"declared package path does not exist: {key} -> {path}"
        assert path.is_relative_to(CHANNEL_DIR.resolve()), (
            f"channel-owned package path must stay inside the channel package: {key} -> {path}"
        )


def test_modern_archivist_pipeline_asset_policy_uses_channel_local_paths() -> None:
    manifest = load_pipeline("modern-archivist", source="channel")
    asset_policy = manifest["metadata"]["asset_policy"]
    requirements_path = ROOT / asset_policy["saved_assets_policy"]
    requirements_text = requirements_path.read_text(encoding="utf-8")
    asset_preflight_text = (ROOT / asset_policy["saved_assets_check"]).read_text(encoding="utf-8")

    assert asset_policy["saved_assets_policy"] == "channels/modern-archivist/assets/comfyui_workflows/asset_requirements.yaml"
    assert requirements_path.exists()
    assert "channel_assets/" not in str(asset_policy)
    assert "channel_assets/" not in requirements_text
    assert "remotion-composer/" not in requirements_text
    assert "modern-archivist" in asset_preflight_text
    assert "asset_requirements.yaml" in asset_preflight_text


def test_channel_pipeline_discovery_is_separate_from_core_pipeline_defs() -> None:
    channel_packages = discover_channel_packages()
    assert "modern-archivist" in channel_packages
    assert channel_packages["modern-archivist"]["source"] == "channel_package"
    assert channel_packages["modern-archivist"]["pipeline_path"] == CHANNEL_DIR / "pipeline.yaml"

    assert "modern-archivist" in list_channel_pipelines()
    assert "modern-archivist" not in [p.stem for p in (ROOT / "pipeline_defs").glob("*.yaml")]


def test_modern_archivist_pipeline_has_thumbnail_stage() -> None:
    manifest = load_pipeline("modern-archivist", source="channel")
    
    # Assert that thumbnail is a valid stage
    thumbnail_stage = next((stage for stage in manifest["stages"] if stage["name"] == "thumbnail"), None)
    assert thumbnail_stage is not None, "Thumbnail stage must exist in the pipeline"
    
    # Check stage requirements and characteristics
    assert "checkpoint_required" in thumbnail_stage, "Thumbnail stage must have checkpoint configuration"
    assert "human_approval_default" in thumbnail_stage, "Thumbnail stage must specify human approval policy"
    assert thumbnail_stage.get("checkpoint_required", False) is True, "Thumbnail stage must require checkpointing"
    assert thumbnail_stage.get("human_approval_default", False) is True, "Thumbnail stage must default to human approval"
    
    # Check that it produces thumbnail artifacts
    assert "produces" in thumbnail_stage
    assert "thumbnail_manifest" in thumbnail_stage["produces"], "Thumbnail stage must produce thumbnail_manifest artifact"
    
    # Check required inputs
    assert "required_artifacts_in" in thumbnail_stage
    assert "episode" in thumbnail_stage["required_artifacts_in"], "Thumbnail stage should require episode artifact"


def test_load_pipeline_can_load_channel_pipeline_explicitly_without_core_mix_in() -> None:
    manifest = load_pipeline("modern-archivist", source="channel")

    assert manifest["name"] == "modern-archivist"
    assert manifest["metadata"]["channel_package"] is True
    assert manifest["metadata"]["canonical_renderer"] == "remotion"


def test_modern_archivist_declares_package_local_subagent_quality_gates() -> None:
    manifest = load_pipeline("modern-archivist", source="channel")
    subagent_policy = manifest["subagent_policy"]

    assert subagent_policy["enabled"] is True
    assert subagent_policy["decision_owner"] == "executive_producer"
    assert subagent_policy["nested_subagents_allowed"] is False
    assert subagent_policy["completion_contract_required"] is True
    assert subagent_policy["main_session_verifies_outputs"] is True
    assert subagent_policy["blocker_handling"] == "surface_to_operator"

    lanes_by_stage = {
        stage["name"]: {lane["name"]: lane for lane in stage.get("subagents", [])}
        for stage in manifest["stages"]
    }

    assert lanes_by_stage["research"]["evidence_auditor"]["mode"] == "blocking"
    assert lanes_by_stage["script"]["failure_thesis_critic"]["mode"] == "blocking"
    assert lanes_by_stage["script"]["voice_consistency_critic"]["mode"] == "blocking"
    assert lanes_by_stage["media_manifest"]["visual_identity_reviewer"]["mode"] == "advisory"
    assert lanes_by_stage["render"]["render_qc_reviewer"]["mode"] == "blocking"

    for stage_lanes in lanes_by_stage.values():
        for lane in stage_lanes.values():
            skill_path = ROOT / lane["skill"]
            assert skill_path.exists(), f"subagent skill missing: {lane['skill']}"
            assert skill_path.is_relative_to(CHANNEL_DIR)
            assert lane["completion_contract"] == "agent_gate_report"
            assert lane["review_focus"]


def test_modern_archivist_pipeline_has_retention_review_stage() -> None:
    manifest = load_pipeline("modern-archivist", source="channel")
    
    # Assert that retention_review is a valid stage
    retention_review_stage = next((stage for stage in manifest["stages"] if stage["name"] == "retention_review"), None)
    assert retention_review_stage is not None, "Retention review stage must exist in the pipeline"
    
    # Check stage characteristics
    assert "checkpoint_required" in retention_review_stage, "Retention review stage must have checkpoint configuration"
    assert retention_review_stage.get("checkpoint_required", False) is False, "Retention review stage should not require checkpointing"
    assert "human_approval_default" in retention_review_stage, "Retention review stage must specify human approval policy"
    assert retention_review_stage.get("human_approval_default", False) is False, "Retention review stage should not default to human approval"
    
    # Check that it produces retention analysis artifacts
    assert "produces" in retention_review_stage
    assert "retention_analysis" in retention_review_stage["produces"], "Retention review stage must produce retention_analysis artifact"
    
    # Check required inputs
    assert "required_artifacts_in" in retention_review_stage
    assert "publish_packet" in retention_review_stage["required_artifacts_in"], "Retention review stage should require publish_packet artifact"
    assert "render_report" in retention_review_stage["required_artifacts_in"], "Retention review stage should require render_report artifact"
    
    # Check the skill
    assert "skill" in retention_review_stage
    assert "skills/retention-analyst.md" in retention_review_stage["skill"], "Retention review stage must use retention-analyst skill"