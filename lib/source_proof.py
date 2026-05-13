"""Source/proof asset manifest shared by acquisition and render."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from schemas.artifacts import validate_artifact


MANIFEST_FILENAME = "source_proof_manifest.json"


class SourceProofError(RuntimeError):
    """Expected source/proof manifest failure."""


@dataclass(frozen=True)
class SourceProofAsset:
    id: str
    source_id: str
    asset_path: Path
    image_paths: tuple[Path, ...]
    sidecar_path: Path
    evidence_id: str | None = None
    capture_id: str | None = None
    claim_ids: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "asset_path": str(self.asset_path),
            "image_paths": [str(path) for path in self.image_paths],
            "sidecar_path": str(self.sidecar_path),
            "evidence_id": self.evidence_id,
            "capture_id": self.capture_id,
            "claim_ids": list(self.claim_ids),
        }

    def matches_segment(self, segment: dict[str, Any]) -> bool:
        names = {str(segment.get("id") or "")}
        names.update(str(item) for item in segment.get("evidence_ids") or [])
        if self.evidence_id and self.evidence_id in names:
            return True
        if self.capture_id and self.capture_id in names:
            return True
        return self.id in names

    def first_existing_image(self) -> Path | None:
        for path in self.image_paths:
            if path.is_file():
                return path
        return None


@dataclass(frozen=True)
class SourceProofManifest:
    assets: tuple[SourceProofAsset, ...]
    asset_format: str
    capture_timestamp: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SourceProofManifest":
        assets = []
        for raw in payload.get("assets") or []:
            if not isinstance(raw, dict):
                continue
            assets.append(
                SourceProofAsset(
                    id=str(raw.get("id") or raw.get("evidence_id") or raw.get("capture_id") or raw.get("source_id")),
                    source_id=str(raw.get("source_id") or ""),
                    asset_path=Path(str(raw.get("asset_path") or raw.get("asset") or "")),
                    image_paths=tuple(Path(str(path)) for path in raw.get("image_paths") or raw.get("images") or ()),
                    sidecar_path=Path(str(raw.get("sidecar_path") or raw.get("sidecar") or "")),
                    evidence_id=str(raw["evidence_id"]) if raw.get("evidence_id") else None,
                    capture_id=str(raw["capture_id"]) if raw.get("capture_id") else None,
                    claim_ids=tuple(str(item) for item in raw.get("claim_ids") or ()),
                )
            )
        return cls(
            assets=tuple(assets),
            asset_format=str(payload.get("asset_format") or "unknown"),
            capture_timestamp=str(payload.get("capture_timestamp") or ""),
        )

    @classmethod
    def load(cls, assets_dir: Path) -> "SourceProofManifest":
        path = assets_dir / MANIFEST_FILENAME
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SourceProofError(f"missing source proof manifest: {path}") from exc
        except json.JSONDecodeError as exc:
            raise SourceProofError(f"invalid source proof manifest: {exc}") from exc
        if not isinstance(payload, dict):
            raise SourceProofError(f"source proof manifest must be an object: {path}")
        return cls.from_payload(payload)

    def payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "asset_count": len(self.assets),
            "asset_format": self.asset_format,
            "capture_timestamp": self.capture_timestamp,
            "assets": [asset.payload() for asset in self.assets],
        }

    def write(self, assets_dir: Path) -> Path:
        path = assets_dir / MANIFEST_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.payload()
        validate_artifact("source_proof_manifest", payload)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def resolve_asset_for_segment(self, segment: dict[str, Any]) -> Path | None:
        for asset in self.assets:
            if not asset.matches_segment(segment):
                continue
            image = asset.first_existing_image()
            if image is not None:
                return image
        return None


def load_optional_source_proof_manifest(assets_dir: Path) -> SourceProofManifest | None:
    path = assets_dir / MANIFEST_FILENAME
    if not path.exists():
        return None
    manifest = SourceProofManifest.load(assets_dir)
    validate_artifact("source_proof_manifest", manifest.payload())
    return manifest
