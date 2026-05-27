from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_PUBLIC = ROOT / "channels" / "modern-archivist" / "remotion" / "public"
COMPOSER_PUBLIC = ROOT / "remotion-composer" / "public" / "modern-archivist"

MANIFEST_V2_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "modern_archivist_puppet_manifest.json"
LEGACY_MANIFEST_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "puppet_manifest.json"
SCHEMA_V2_PATH = ROOT / "channels" / "modern-archivist" / "schemas" / "puppet_manifest.schema.json"
REMOTION_TYPES_PATH = ROOT / "channels" / "modern-archivist" / "remotion" / "src" / "types.ts"
ASSET_INVENTORY_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "asset-inventory.md"
CHARACTER_README_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "README.md"
SVG_LAYER_PREVIEW_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "svg_layers" / "preview.html"
RIG_SPEC_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "rig" / "rig_spec.json"
ACTION_LIBRARY_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "rig" / "action_library.json"
VISEME_LIBRARY_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "rig" / "viseme_library.json"
EXPRESSION_LIBRARY_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "rig" / "expression_library.json"
TIMELINE_SCHEMA_PATH = ROOT / "channels" / "modern-archivist" / "schemas" / "puppet_action_timeline.schema.json"
SAMPLE_TIMELINE_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "character" / "rig" / "sample_action_timeline.json"
SVG_LAYER_MUG_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "svg_layers" / "mug_code.png"
SVG_LAYER_HAND_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "svg_layers" / "hand_mug.png"
SVG_LAYER_SHADOW_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "svg_layers" / "shadow.png"
SVG_LAYER_REFERENCE_PATH = ROOT / "channels" / "modern-archivist" / "assets" / "svg_layers" / "reference_mug_pose.png"


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
    required = {
        "id",
        "src",
        "group",
        "z",
        "status",
        "coordinate_mode",
        "anchor",
        "pivot",
        "bounds_required",
    }
    for layer in manifest["layers"]:
        missing = required - layer.keys()
        assert not missing, f"layer {layer.get('id', '<unknown>')} missing fields: {sorted(missing)}"
        assert layer["coordinate_mode"] in {"canvas_registered", "anchored_overlay"}


def test_legacy_manifest_is_not_the_production_v2_contract() -> None:
    legacy = json.loads(LEGACY_MANIFEST_PATH.read_text())
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    assert manifest["version"].startswith("2."), "modern_archivist_puppet_manifest.json is the production v2 contract"
    assert legacy["version"].startswith("1."), "puppet_manifest.json should remain explicitly legacy"
    assert "rig_contract" not in legacy, "legacy puppet_manifest.json must not masquerade as the v2 rig contract"


def test_remotion_types_match_v2_manifest_contract() -> None:
    types = REMOTION_TYPES_PATH.read_text()
    assert "layers_v2" not in types, "TypeScript contract must use v2 layers[], not layers_v2"
    assert "export interface LegacyPuppetManifest" in types
    assert "layers: PuppetLayerEntry[]" in types
    assert "coordinate_mode: PuppetCoordinateMode" in types


def test_v2_manifest_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    schema = json.loads(SCHEMA_V2_PATH.read_text())
    jsonschema.validate(manifest, schema)


REMOTION_PUBLIC = ROOT / "remotion-composer" / "public"


def _resolve_layer_path(src: str) -> Path:
    """Resolve a manifest src path to an absolute filesystem path."""
    return REMOTION_PUBLIC / src


def test_production_layers_are_rgba() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    for layer in manifest["layers"]:
        if layer.get("status") != "production":
            continue
        path = _resolve_layer_path(layer["src"])
        assert path.exists(), f"production layer missing: {layer['id']} -> {path}"
        img = Image.open(path)
        assert img.mode == "RGBA", f"layer {layer['id']} is not RGBA (got {img.mode})"


def test_canvas_registered_production_layers_match_declared_canvas() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    canvas_size = (manifest["canvas"]["width"], manifest["canvas"]["height"])
    for layer in manifest["layers"]:
        if layer.get("status") != "production" or layer.get("coordinate_mode") != "canvas_registered":
            continue
        path = _resolve_layer_path(layer["src"])
        img = Image.open(path)
        assert img.size == canvas_size, f"canvas layer {layer['id']} has size {img.size}, expected {canvas_size}"


def test_anchored_overlay_production_layers_do_not_claim_canvas_registration() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    canvas_size = (manifest["canvas"]["width"], manifest["canvas"]["height"])
    for layer in manifest["layers"]:
        if layer.get("status") != "production" or layer.get("coordinate_mode") != "anchored_overlay":
            continue
        path = _resolve_layer_path(layer["src"])
        img = Image.open(path)
        assert img.width > 0 and img.height > 0
        assert img.size != canvas_size, f"anchored overlay {layer['id']} is full-canvas; mark it canvas_registered instead"


def test_body_layer_preserves_full_body_bounds() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    canvas_height = manifest["canvas"]["height"]
    body = next(layer for layer in manifest["layers"] if layer["id"] == "body")
    assert body["coordinate_mode"] == "canvas_registered"
    path = _resolve_layer_path(body["src"])
    img = Image.open(path).convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    assert bbox is not None
    body_height = bbox[3] - bbox[1]
    # Body source is torso_hoodie.png (canvas-registered with head_neutral).
    # The torso spans the lower ~48% of the canvas; 0.40 guards against
    # accidentally using a small cropped torso or a misaligned source.
    assert body_height > 0.40 * canvas_height, f"body layer height {body_height}px is too short (expected torso to cover >40% of canvas height)"


def test_production_layers_have_valid_alpha_bbox() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    for layer in manifest["layers"]:
        if layer.get("status") != "production":
            continue
        path = _resolve_layer_path(layer["src"])
        img = Image.open(path).convert("RGBA")
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()
        assert bbox is not None, f"layer {layer['id']} has fully transparent alpha"
        assert bbox != (0, 0, img.width, img.height), f"layer {layer['id']} alpha fills entire canvas (no transparency)"


def test_production_layers_have_sufficient_transparency() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    for layer in manifest["layers"]:
        if layer.get("status") != "production":
            continue
        path = _resolve_layer_path(layer["src"])
        img = Image.open(path).convert("RGBA")
        alpha = img.getchannel("A")
        hist = alpha.histogram()
        transparent_ratio = sum(hist[:10]) / (img.width * img.height)
        assert transparent_ratio > 0.20, (
            f"layer {layer['id']} has insufficient transparency: {transparent_ratio:.2f}"
        )


def test_asset_inventory_covers_every_manifest_layer() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    inventory = ASSET_INVENTORY_PATH.read_text()
    for layer in manifest["layers"]:
        assert f"| `{layer['id']}` |" in inventory, f"asset inventory missing row for {layer['id']}"


def test_asset_inventory_records_provenance_and_next_actions() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    inventory = ASSET_INVENTORY_PATH.read_text()
    for layer in manifest["layers"]:
        row_prefix = f"| `{layer['id']}` |"
        row = next((line for line in inventory.splitlines() if line.startswith(row_prefix)), "")
        assert row, f"asset inventory missing row for {layer['id']}"
        assert "TBD" not in row, f"asset inventory row for {layer['id']} must not leave provenance/action as TBD"
        if layer["status"] == "production":
            assert "production" in row
            assert "source" not in row.lower() or "unknown" not in row.lower(), f"production row for {layer['id']} needs concrete provenance"
        if layer["status"] == "placeholder":
            assert "placeholder" in row
            assert "generate" in row.lower() or "replace" in row.lower() or "promote" in row.lower(), (
                f"placeholder row for {layer['id']} needs an explicit next action"
            )


def test_character_readme_documents_promotion_rubric() -> None:
    readme = CHARACTER_README_PATH.read_text().lower()
    required_phrases = [
        "coordinate modes",
        "canvas_registered",
        "anchored_overlay",
        "promotion process",
        "preview-only",
        "hard alpha",
        "flat palette",
        "no head-only",
    ]
    for phrase in required_phrases:
        assert phrase in readme, f"character README missing rubric phrase: {phrase}"


def test_phase3_semantic_hand_mug_shadow_layers_are_promoted() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    layers = {layer["id"]: layer for layer in manifest["layers"]}

    for layer_id in ["hand_mug", "shadow"]:
        assert layers[layer_id]["status"] == "production", f"{layer_id} must be promoted in Phase 3"
        assert layers[layer_id]["coordinate_mode"] == "canvas_registered"
        path = _resolve_layer_path(layers[layer_id]["src"])
        assert path.exists(), f"{layer_id} render asset missing: {path}"
        img = Image.open(path).convert("RGBA")
        assert img.size == (manifest["canvas"]["width"], manifest["canvas"]["height"])
        assert img.getchannel("A").getbbox() is not None

    assert layers["hand_mug"]["z"] > layers["mug"]["z"], "hand/grip must overlay mug, not sit behind it"


def test_preview_is_manifest_driven() -> None:
    """Preview must load layers from the manifest, not hard-code them."""
    preview = SVG_LAYER_PREVIEW_PATH.read_text()
    assert "fetch(" in preview, "preview must use fetch() to load manifest data"
    assert "modern_archivist_puppet_manifest.json" in preview, "preview must reference the v2 manifest JSON"
    assert "reference_mug_pose.png" in preview, "preview must still reference the mug-pose reference image"
    # Must NOT have hard-coded layer img paths
    for forbidden in ['src="mug_code.png"', 'src="torso_hoodie.svg"', 'src="head_neutral.svg"',
                      'scale(0.82)', 'scale(0.94)', 'scale(0.96)']:
        assert forbidden not in preview, f"preview must not contain hard-coded: {forbidden}"


def test_preview_layer_strip_references_manifest_data() -> None:
    """Preview layer strip must be dynamically built from manifest, not duplicated."""
    preview = SVG_LAYER_PREVIEW_PATH.read_text()
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    # The preview generates layers dynamically; verify it doesn't hard-code layer IDs
    # by checking that manifest layer IDs are NOT sprinkled as literal src= attributes
    for layer in manifest["layers"]:
        layer_id = layer["id"]
        # The layer ID must not appear as a hard-coded img src (it can appear in JS data or comments)
        assert f'src="{layer_id}.png"' not in preview, (
            f"layer {layer_id} must not be hard-coded as src=; must come from manifest JSON"
        )
        assert f'src="{layer_id}.svg"' not in preview, (
            f"layer {layer_id} must not be hard-coded as src=; must come from manifest JSON"
        )


def test_rig_spec_exists_and_is_valid() -> None:
    assert RIG_SPEC_PATH.exists(), "rig_spec.json must exist"
    spec = json.loads(RIG_SPEC_PATH.read_text())
    assert spec["version"].startswith("3."), "rig_spec must be version 3.x"
    assert spec["canvas"] == {"width": 1254, "height": 1254}
    assert "parts" in spec, "rig_spec must have a parts dict"
    assert "states" in spec, "rig_spec must have a states dict"
    for state_key in ["expression", "eyes", "mouth", "action"]:
        assert state_key in spec["states"], f"rig_spec states must include {state_key}"


def test_rig_spec_arm_hierarchy() -> None:
    spec = json.loads(RIG_SPEC_PATH.read_text())
    parts = spec["parts"]
    assert "upper_arm_r" in parts, "rig_spec must define upper_arm_r"
    assert "forearm_r" in parts, "rig_spec must define forearm_r"
    assert "hand_r" in parts, "rig_spec must define hand_r"
    assert "mug" in parts, "rig_spec must define mug part"
    assert parts["forearm_r"]["parent"] == "upper_arm_r"
    assert parts["hand_r"]["parent"] == "forearm_r"
    assert parts["mug"]["parent"] == "hand_r"


def test_action_library_exists_and_valid() -> None:
    assert ACTION_LIBRARY_PATH.exists(), "action_library.json must exist"
    lib = json.loads(ACTION_LIBRARY_PATH.read_text())
    assert "actions" in lib
    assert "idle" in lib["actions"], "action_library must have idle action"
    assert "mug_sip" in lib["actions"], "action_library must have mug_sip action"
    sip = lib["actions"]["mug_sip"]
    assert sip["duration_frames"] == 42
    assert len(sip["keyframes"]) >= 3, "mug_sip must have at least 3 keyframes"
    assert "occlusion" in sip, "mug_sip must define occlusion rules"


def test_action_timeline_schema_exists() -> None:
    assert TIMELINE_SCHEMA_PATH.exists(), "puppet_action_timeline.schema.json must exist"
    schema = json.loads(TIMELINE_SCHEMA_PATH.read_text())
    assert "properties" in schema
    assert "tracks" in schema["properties"]


def test_sample_timeline_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(TIMELINE_SCHEMA_PATH.read_text())
    timeline = json.loads(SAMPLE_TIMELINE_PATH.read_text())
    jsonschema.validate(timeline, schema)
    # Check all track values are valid rig states
    spec = json.loads(RIG_SPEC_PATH.read_text())
    for track in timeline["tracks"]:
        track_type = track["type"]
        if track_type in spec["states"]:
            assert track["value"] in spec["states"][track_type], (
                f"timeline track {track_type}={track['value']} not in rig_spec states"
            )


def test_viseme_library_exists_and_valid() -> None:
    assert VISEME_LIBRARY_PATH.exists(), "viseme_library.json must exist"
    lib = json.loads(VISEME_LIBRARY_PATH.read_text())
    assert lib["version"].startswith("1.")
    assert lib["character_id"] == "modern_archivist"
    assert "mapping" in lib
    # Every mapped mouth must exist in the manifest
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    production_mouths = {l["id"] for l in manifest["layers"] if l["group"] == "mouths"}
    for phoneme, mouth_id in lib["mapping"].items():
        assert mouth_id in production_mouths, f"viseme {phoneme} maps to unknown mouth: {mouth_id}"
    # Must cover silence
    assert "SIL" in lib["mapping"]
    # Must have at least 30 phoneme entries
    assert len(lib["mapping"]) >= 30, "viseme_library must cover at least 30 phonemes"


def test_phase3_arm_and_hand_no_longer_have_white_outline() -> None:
    manifest = json.loads(MANIFEST_V2_PATH.read_text())
    layers = {layer["id"]: layer for layer in manifest["layers"]}
    for layer_id in ["arm_right_idle", "hand_mug"]:
        path = _resolve_layer_path(layers[layer_id]["src"])
        img = Image.open(path).convert("RGBA")
        near_white = 0
        foreground = 0
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]  # type: ignore[index,misc]
                if a <= 10:
                    continue
                foreground += 1
                if r >= 188 and g >= 188 and b >= 178 and max(r, g, b) - min(r, g, b) <= 55:
                    near_white += 1
        assert foreground > 0
        assert near_white == 0, f"{layer_id} still has near-white outline pixels"


def test_expression_library_exists_and_valid() -> None:
    assert EXPRESSION_LIBRARY_PATH.exists(), "expression_library.json must exist"
    lib = json.loads(EXPRESSION_LIBRARY_PATH.read_text())
    assert lib["version"].startswith("1.")
    assert lib["character_id"] == "modern_archivist"
    assert "expressions" in lib
    spec = json.loads(RIG_SPEC_PATH.read_text())
    for expr_name in spec["states"]["expression"]:
        assert expr_name in lib["expressions"], f"expression_library missing: {expr_name}"
    # Each expression must have eyes, brows, mouth_default
    for name, expr in lib["expressions"].items():
        assert "eyes" in expr, f"expression {name} missing eyes"
        assert "brows" in expr, f"expression {name} missing brows"
        assert "mouth_default" in expr, f"expression {name} missing mouth_default"
