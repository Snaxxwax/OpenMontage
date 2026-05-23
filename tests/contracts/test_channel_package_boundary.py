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


def test_modern_archivist_manifest_tool_names_are_registry_discoverable() -> None:
    from tools.tool_registry import registry

    registry.discover()
    manifest = load_pipeline("modern-archivist", source="channel")
    registry_tool_names = set(registry._tools)
    stage_tool_names: set[str] = set()

    for stage in manifest["stages"]:
        for key in ["required_tools", "optional_tools", "tools_available"]:
            stage_tool_names.update(stage.get(key, []))

    legacy_semantic_labels = {
        "asset_generation_needed",
        "comfyui",
        "comfyui_lifecycle",
        "ffmpeg",
        "ffprobe",
        "fish_speech",
        "remotion",
    }

    assert stage_tool_names
    assert "tts_selector" in stage_tool_names
    assert "fish_speech_tts" in stage_tool_names
    assert "video_compose" in stage_tool_names
    assert "hyperframes_compose" in stage_tool_names
    assert stage_tool_names.isdisjoint(legacy_semantic_labels)
    assert stage_tool_names <= registry_tool_names


def test_channel_specific_terms_are_not_added_to_generic_pipeline_table() -> None:
    project_context = (ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
    available_table = project_context.split("## When Building New Pipelines", 1)[0]

    assert "modern-archivist" not in available_table
    assert "broadcast-explainer" not in available_table
    assert "channels/<channel-name>/" in project_context or "channels/<name>/" in project_context


def test_legacy_broadcast_explainer_is_archived_inside_modern_archivist_channel() -> None:
    legacy_dir = CHANNEL_DIR / "legacy" / "broadcast-explainer"

    assert not (ROOT / "pipeline_defs" / "broadcast-explainer.yaml").exists()
    assert not (ROOT / "skills" / "pipelines" / "broadcast-explainer").exists()
    assert legacy_dir.exists()
    assert (legacy_dir / "pipeline.yaml").exists()
    assert (legacy_dir / "README.md").exists()
    assert (legacy_dir / "skills" / "script-director.md").exists()
    assert (legacy_dir / "styles" / "broadcast-investigative.yaml").exists()

    legacy_manifest = load_yaml(legacy_dir / "pipeline.yaml")
    assert legacy_manifest["name"] == "broadcast-explainer"
    assert legacy_manifest["metadata"]["archived_from"] == "pipeline_defs/broadcast-explainer.yaml"
    assert legacy_manifest["metadata"]["legacy_status"] == "channel-reference-only"
    assert legacy_manifest["metadata"]["canonical_successor"] == "channels/modern-archivist/pipeline.yaml"


def test_core_pipeline_defs_do_not_contain_archived_channel_specific_pipelines() -> None:
    core_pipeline_names = [p.stem for p in (ROOT / "pipeline_defs").glob("*.yaml")]

    assert "broadcast-explainer" not in core_pipeline_names
    assert "modern-archivist" not in core_pipeline_names


def test_remotion_composer_modern_archivist_tree_is_thin_channel_adapter() -> None:
    adapter_dir = ROOT / "remotion-composer" / "src" / "modern-archivist"
    channel_src = CHANNEL_DIR / "remotion" / "src"
    adapter_files = [
        adapter_dir / "index.ts",
        adapter_dir / "ModernArchivistComposition.tsx",
        adapter_dir / "fixtures.ts",
        adapter_dir / "styles.ts",
        adapter_dir / "state.ts",
        adapter_dir / "types.ts",
        adapter_dir / "components" / "ArchivistPuppet.tsx",
        adapter_dir / "components" / "ChannelFrame.tsx",
        adapter_dir / "components" / "MediaContainer.tsx",
        adapter_dir / "components" / "ScrollingCodeBackdrop.tsx",
    ]

    assert channel_src.exists()
    for adapter_file in adapter_files:
        text = adapter_file.read_text(encoding="utf-8")
        assert "Thin adapter" in text
        assert "channels/modern-archivist/remotion/src" in text
        assert "from \"./" not in text
        assert "React.FC" not in text
        assert "AbsoluteFill" not in text


def test_core_broadcast_investigative_playbook_is_generic_not_channel_identity() -> None:
    playbook_path = ROOT / "styles" / "broadcast-investigative.yaml"
    archive_snapshot_path = (
        CHANNEL_DIR / "legacy" / "broadcast-explainer" / "styles" / "broadcast-investigative.yaml"
    )

    playbook = load_yaml(playbook_path)
    playbook_text = playbook_path.read_text(encoding="utf-8").lower()
    archive_snapshot_text = archive_snapshot_path.read_text(encoding="utf-8").lower()

    assert "asymmetric" not in playbook_text
    assert "modern archivist" not in playbook_text
    assert "failure ledger" not in playbook_text
    assert "e-girl" not in playbook_text
    assert "channel" not in playbook["identity"]["best_for"].lower()
    assert "investigative" in playbook["identity"]["best_for"].lower()

    # The legacy snapshot remains available as historical channel-specific production DNA.
    assert "asymmetric" in archive_snapshot_text
    assert "e-girl" in archive_snapshot_text
