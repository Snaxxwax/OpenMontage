from __future__ import annotations

import json
from pathlib import Path

from lib.artifact_bus import ArtifactBus
from lib.pipeline_contract import PipelineContract


def test_artifact_bus_uses_canonical_project_layout(tmp_path: Path) -> None:
    bus = ArtifactBus.for_project("episode_001", projects_dir=tmp_path)
    bus.ensure_dirs()

    assert bus.root == tmp_path / "episode_001"
    assert bus.artifacts.is_dir()
    assert bus.receipts.is_dir()
    assert bus.clips.is_dir()
    assert bus.audio.is_dir()
    assert bus.renders.is_dir()
    assert bus.qc.is_dir()
    assert bus.logs == bus.qc

    bus.write_artifact("example.json", {"ok": True})
    assert json.loads((bus.artifacts / "example.json").read_text(encoding="utf-8")) == {"ok": True}
    assert bus.load_artifact("example.json") == {"ok": True}


def test_asymmetric_pipeline_contract_derives_artifact_schemas() -> None:
    contract = PipelineContract.load("asymmetric-source-commentary")

    assert contract.pipeline_id == "asymmetric-source-commentary"
    assert contract.stage_names[:3] == ["greenlight", "source_discovery", "youtube_source_discovery"]
    assert contract.artifact_schemas["asymmetric_greenlight.json"].name == "asymmetric_greenlight.schema.json"
    assert contract.artifact_schemas["source_segment_approval_manifest.json"].name == (
        "source_segment_approval_manifest.schema.json"
    )
    assert not contract.missing_schemas()


def test_asymmetric_pipeline_contract_has_all_referenced_director_skills() -> None:
    contract = PipelineContract.load("asymmetric-source-commentary")

    assert not contract.missing_directors()
    assert not contract.validate_references()
