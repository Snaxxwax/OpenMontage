from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_PUBLIC = ROOT / "channels" / "modern-archivist" / "remotion" / "public"
COMPOSER_PUBLIC = ROOT / "remotion-composer" / "public" / "modern-archivist"

MANIFEST_V2_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "modern_archivist_puppet_manifest.json"
SCHEMA_V2_PATH = ROOT / "channels" / "modern-archivist" / "schemas" / "puppet_manifest.schema.json"


def _alpha_stats(path: Path) -> tuple[float, tuple[int, int, int, int] | None]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    hist = alpha.histogram()
    transparent_ratio = sum(hist[:10]) / (image.width * image.height)
    return transparent_ratio, alpha.getbbox()


def test_public_archivist_body_has_hard_alpha_not_white_square() -> None:
    for root in [CHANNEL_PUBLIC, COMPOSER_PUBLIC]:
        transparent_ratio, bbox = _alpha_stats(root / "archivist-body.png")
        assert transparent_ratio > 0.25
        assert bbox is not None
        assert bbox != (0, 0, 1254, 1254)


def test_public_archivist_mug_has_hard_alpha_not_white_square() -> None:
    for root in [CHANNEL_PUBLIC, COMPOSER_PUBLIC]:
        transparent_ratio, bbox = _alpha_stats(root / "archivist-mug.png")
        assert transparent_ratio > 0.45
        assert bbox is not None
        assert bbox != (0, 0, 1254, 1254)


def test_v2_manifest_exists() -> None:
    assert MANIFEST_V2_PATH.exists(), "modern_archivist_puppet_manifest.json must exist"


def test_v2_manifest_rig_contract() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    assert manifest["rig_contract"] == "full_body_layered"
    assert manifest["canvas"] == {"width": 1254, "height": 1254}


def test_v2_manifest_layer_groups() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    for group in ["body", "head", "eyes", "brows", "mouths", "glasses", "arms", "props"]:
        assert group in manifest["layer_groups"], f"missing layer_group: {group}"


def test_v2_manifest_layer_fields() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    for layer in manifest["layers"]:
        assert "id" in layer
        assert "group" in layer
        assert "z" in layer


def test_v2_manifest_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    schema = json.loads(SCHEMA_V2_PATH.read_text())
    jsonschema.validate(manifest, schema)
