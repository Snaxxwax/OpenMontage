from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "channels" / "modern-archivist" / "scripts" / "content_asset_staging.py"
spec = spec_from_file_location("content_asset_staging", MODULE_PATH)
assert spec and spec.loader
content_asset_staging = module_from_spec(spec)
spec.loader.exec_module(content_asset_staging)
stage_content_collection_assets = content_asset_staging.stage_content_collection_assets
validate_content_opportunity_refs = content_asset_staging.validate_content_opportunity_refs


def test_stage_content_collection_assets_copies_local_inputs_deterministically(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "demo frame.png"
    source.parent.mkdir()
    source.write_bytes(b"nikola-demo-frame")
    project_dir = tmp_path / "project"
    collection = {
        "episode_id": "nikola-fake-truck",
        "opportunities": [
            {
                "id": "opp_001",
                "kind": "source_footage",
                "title": "Truck demo frame",
                "local_path": str(source),
                "rights_status": "needs_review",
                "runtime_affinity": "remotion",
                "visual_mode": "source_montage",
                "evidence_refs": ["source_001"],
            }
        ],
    }

    first = stage_content_collection_assets(collection, project_dir)
    second = stage_content_collection_assets(collection, project_dir)

    assert first == second
    assert first["assets"][0]["id"] == "content_opp_001"
    assert first["assets"][0]["path"] == "assets/content_collection/opp_001/0af7c010-demo-frame.png"
    staged = project_dir / first["assets"][0]["path"]
    assert staged.read_bytes() == b"nikola-demo-frame"
    assert first["metadata"]["content_collection_staging"]["staged_count"] == 1
    assert first["metadata"]["content_collection_staging"]["staged_assets"][0]["sha256"].startswith("0af7c010")
    asset_schema = json.loads((ROOT / "schemas" / "artifacts" / "asset_manifest.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(asset_schema).validate(first)


def test_validate_content_opportunity_refs_detects_episode_and_media_misses() -> None:
    collection = {"opportunities": [{"id": "opp_001"}, {"id": "opp_002"}]}
    episode = {
        "sections": [
            {"id": "s01", "content_opportunity_refs": ["opp_001"]},
            {"id": "s02", "media_overlay": {"kind": "source_montage", "content_opportunity_refs": ["opp_missing_episode"]}},
        ]
    }
    media_manifest = {
        "items": [
            {"id": "media_001", "content_opportunity_refs": ["opp_002"]},
            {"id": "media_002", "content_opportunity_refs": ["opp_missing_media"]},
        ]
    }

    result = validate_content_opportunity_refs(collection, episode, media_manifest)

    assert result["valid"] is False
    assert result["unresolved_refs"] == [
        {"artifact": "episode", "path": "sections[1].media_overlay.content_opportunity_refs[0]", "ref": "opp_missing_episode"},
        {"artifact": "media_manifest", "path": "items[1].content_opportunity_refs[0]", "ref": "opp_missing_media"},
    ]


def test_validate_content_opportunity_refs_passes_when_all_refs_resolve() -> None:
    collection = {"opportunities": [{"id": "opp_001"}]}
    episode = {"sections": [{"id": "s01", "content_opportunity_refs": ["opp_001"]}]}
    media_manifest = {"items": [{"id": "media_001", "content_opportunity_refs": ["opp_001"]}]}

    result = validate_content_opportunity_refs(collection, episode, media_manifest)

    assert result == {"valid": True, "available_opportunity_ids": ["opp_001"], "unresolved_refs": []}
