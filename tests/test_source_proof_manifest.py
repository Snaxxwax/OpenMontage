from __future__ import annotations

from pathlib import Path

from lib.source_proof import SourceProofManifest
from schemas.artifacts import load_schema, validate_artifact


def test_source_proof_manifest_schema_exists() -> None:
    schema = load_schema("source_proof_manifest")
    assert schema["title"] == "SourceProofManifest"


def test_source_proof_manifest_payload_validates(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "proof.ppm").write_text("ppm", encoding="utf-8")
    (assets_dir / "source.ppm").write_text("ppm", encoding="utf-8")

    manifest = SourceProofManifest.from_payload(
        {
            "ok": True,
            "asset_count": 1,
            "asset_format": "html",
            "capture_timestamp": "2026-05-13T12:00:00Z",
            "assets": [
                {
                    "id": "ev-proof",
                    "source_id": "src-proof",
                    "asset_path": str(assets_dir / "proof.html"),
                    "image_paths": [str(assets_dir / "proof.ppm")],
                    "sidecar_path": str(assets_dir / "proof.json"),
                    "evidence_id": "ev-proof",
                    "capture_id": None,
                    "claim_ids": ["claim-1"],
                }
            ],
        }
    )

    validate_artifact("source_proof_manifest", manifest.payload())


def test_source_proof_manifest_round_trip(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "proof.ppm").write_text("ppm", encoding="utf-8")

    manifest = SourceProofManifest.from_payload(
        {
            "ok": True,
            "asset_count": 1,
            "asset_format": "txt",
            "capture_timestamp": "2026-05-13T12:00:00Z",
            "assets": [
                {
                    "id": "ev-proof",
                    "source_id": "src-proof",
                    "asset_path": str(assets_dir / "proof.txt"),
                    "image_paths": [str(assets_dir / "proof.ppm")],
                    "sidecar_path": str(assets_dir / "proof.json"),
                    "evidence_id": "ev-proof",
                    "capture_id": "cap-proof",
                    "claim_ids": ["claim-1"],
                }
            ],
        }
    )

    manifest.write(assets_dir)
    loaded = SourceProofManifest.load(assets_dir)
    assert loaded.asset_format == "txt"
    assert loaded.assets[0].evidence_id == "ev-proof"
