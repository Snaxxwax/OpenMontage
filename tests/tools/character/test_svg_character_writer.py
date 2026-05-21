"""Tests for SvgCharacterWriter tool."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.character.svg_character_writer import (
    SvgCharacterWriter,
    _extract_group_ids,
    _to_rig_plan,
    _to_pose_library,
)

MINIMAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <style>@keyframes sway { 0%,100% { transform: rotate(-2deg); } 50% { transform: rotate(2deg); } }
  #head { animation: sway 3s ease-in-out infinite; transform-origin: bottom center; }</style>
  <g id="body"><rect x="156" y="280" width="200" height="200" fill="#4a9eff"/></g>
  <g id="head"><circle cx="256" cy="200" r="90" fill="#ffcc88"/></g>
  <g id="eyes-open"><circle cx="225" cy="185" r="12" fill="#333"/><circle cx="287" cy="185" r="12" fill="#333"/></g>
  <g id="eyes-closed" style="display:none"><line x1="213" y1="185" x2="237" y2="185" stroke="#333" stroke-width="4"/></g>
  <g id="mouth-neutral"><path d="M225 240 Q256 265 287 240" fill="none" stroke="#333" stroke-width="4"/></g>
  <g id="mouth-open" style="display:none"><ellipse cx="256" cy="248" rx="22" ry="14" fill="#c44"/></g>
</svg>"""

MINIMAL_RIG = {
    "version": "1.0",
    "assetId": "test_char",
    "parts": [
        {"id": "body",         "parent": None,   "pivot": {"x": 256, "y": 400}, "depth": 0},
        {"id": "head",         "parent": "body", "pivot": {"x": 256, "y": 200}, "depth": 1},
        {"id": "eyes-open",    "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2},
        {"id": "eyes-closed",  "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2},
        {"id": "mouth-neutral","parent": "head", "pivot": {"x": 256, "y": 240}, "depth": 2},
        {"id": "mouth-open",   "parent": "head", "pivot": {"x": 256, "y": 248}, "depth": 2},
    ],
}

MINIMAL_POSES = {
    "assetId": "test_char",
    "poses": [
        {"id": "idle",       "name": "Idle",        "transforms": {"head": {"rotation": 0}}},
        {"id": "blink",      "name": "Blink",       "transforms": {}},
        {"id": "talk_open",  "name": "Talk (Open)", "transforms": {"mouth-neutral": {"scaleY": 0}, "mouth-open": {"scaleY": 1}}},
        {"id": "surprised",  "name": "Surprised",   "transforms": {"head": {"scaleX": 1.1, "scaleY": 1.1}}},
    ],
}

MINIMAL_SPEC = {
    "id": "test_char",
    "name": "Test Character",
    "description": "A minimal test character",
    "style": "Flat Vector",
    "colors": {"body": "#4a9eff", "skin": "#ffcc88"},
}


class TestExtractGroupIds:
    def test_extracts_ids_from_svg(self):
        ids = _extract_group_ids(MINIMAL_SVG)
        assert ids == {"body", "head", "eyes-open", "eyes-closed", "mouth-neutral", "mouth-open"}

    def test_returns_empty_set_for_svg_without_g_elements(self):
        assert _extract_group_ids("<svg><rect id='r'/></svg>") == set()

    def test_ignores_non_g_element_ids(self):
        svg = '<svg><rect id="foo"/><g id="bar"><circle id="baz"/></g></svg>'
        assert _extract_group_ids(svg) == {"bar"}


class TestToRigPlan:
    def test_produces_valid_openmontage_structure(self):
        result = _to_rig_plan(MINIMAL_SPEC, MINIMAL_RIG, MINIMAL_POSES)
        assert result["version"] == "1.0"
        char = result["characters"][0]
        assert char["character_id"] == "test_char"
        assert char["rig_type"] == "svg_rig"
        assert any(p["id"] == "body" for p in char["parts"])

    def test_joints_use_pivot_coords(self):
        result = _to_rig_plan(MINIMAL_SPEC, MINIMAL_RIG, MINIMAL_POSES)
        char = result["characters"][0]
        assert char["joints"]["body"]["pivot"] == [256, 400]
        assert char["joints"]["head"]["pivot"] == [256, 200]

    def test_layers_derived_from_depth(self):
        result = _to_rig_plan(MINIMAL_SPEC, MINIMAL_RIG, MINIMAL_POSES)
        assert "layer_0" in result["characters"][0]["layers"]
        assert "layer_1" in result["characters"][0]["layers"]

    def test_required_poses_backfilled_from_pose_library(self):
        result = _to_rig_plan(MINIMAL_SPEC, MINIMAL_RIG, MINIMAL_POSES)
        poses = result["characters"][0]["required_poses"]
        assert "idle" in poses
        assert "talk_open" in poses


class TestToPoseLibrary:
    def test_produces_valid_openmontage_structure(self):
        result = _to_pose_library(MINIMAL_SPEC, MINIMAL_POSES)
        assert result["version"] == "1.0"
        char = result["characters"][0]
        assert char["character_id"] == "test_char"
        assert "idle" in char["poses"]

    def test_description_mapped_from_name(self):
        result = _to_pose_library(MINIMAL_SPEC, MINIMAL_POSES)
        assert result["characters"][0]["poses"]["idle"]["description"] == "Idle"

    def test_transforms_preserved(self):
        result = _to_pose_library(MINIMAL_SPEC, MINIMAL_POSES)
        talk = result["characters"][0]["poses"]["talk_open"]
        assert "mouth-neutral" in talk["parts"]


class TestSvgCharacterWriter:
    def test_writes_all_five_files(self, tmp_path):
        tool = SvgCharacterWriter()
        result = tool.execute({
            "svg_content": MINIMAL_SVG,
            "rig_manifest": MINIMAL_RIG,
            "pose_library": MINIMAL_POSES,
            "asset_spec": MINIMAL_SPEC,
            "output_dir": str(tmp_path),
        })
        assert result.success
        for fname in ["character.svg", "rig_manifest.json", "pose_library.json",
                      "asset_spec.json", "preview.html"]:
            assert (tmp_path / fname).exists(), f"Missing: {fname}"

    def test_returns_openmontage_rig_plan_and_pose_library(self, tmp_path):
        tool = SvgCharacterWriter()
        result = tool.execute({
            "svg_content": MINIMAL_SVG, "rig_manifest": MINIMAL_RIG,
            "pose_library": MINIMAL_POSES, "asset_spec": MINIMAL_SPEC,
            "output_dir": str(tmp_path),
        })
        assert result.success
        assert result.data["rig_plan"]["version"] == "1.0"
        assert result.data["pose_library"]["version"] == "1.0"
        assert result.data["rig_plan"]["characters"][0]["character_id"] == "test_char"

    def test_fails_when_rig_part_missing_from_svg(self, tmp_path):
        bad_rig = {**MINIMAL_RIG, "parts": [
            *MINIMAL_RIG["parts"],
            {"id": "arm_left", "parent": "body", "pivot": {"x": 180, "y": 350}, "depth": 1},
        ]}
        tool = SvgCharacterWriter()
        result = tool.execute({
            "svg_content": MINIMAL_SVG, "rig_manifest": bad_rig,
            "pose_library": MINIMAL_POSES, "asset_spec": MINIMAL_SPEC,
            "output_dir": str(tmp_path),
        })
        assert not result.success
        assert "arm_left" in result.error

    def test_preview_html_contains_svg_and_gsap(self, tmp_path):
        tool = SvgCharacterWriter()
        tool.execute({
            "svg_content": MINIMAL_SVG, "rig_manifest": MINIMAL_RIG,
            "pose_library": MINIMAL_POSES, "asset_spec": MINIMAL_SPEC,
            "output_dir": str(tmp_path),
        })
        html = (tmp_path / "preview.html").read_text()
        assert "<svg" in html
        assert "gsap" in html.lower()
        assert "idle" in html.lower()

    def test_svg_path_in_artifacts(self, tmp_path):
        tool = SvgCharacterWriter()
        result = tool.execute({
            "svg_content": MINIMAL_SVG, "rig_manifest": MINIMAL_RIG,
            "pose_library": MINIMAL_POSES, "asset_spec": MINIMAL_SPEC,
            "output_dir": str(tmp_path),
        })
        assert str(tmp_path / "character.svg") in result.artifacts

    def test_default_output_dir_uses_character_id(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        tool = SvgCharacterWriter()
        result = tool.execute({
            "svg_content": MINIMAL_SVG, "rig_manifest": MINIMAL_RIG,
            "pose_library": MINIMAL_POSES, "asset_spec": MINIMAL_SPEC,
        })
        assert result.success
        assert Path(result.data["svg_path"]).exists()
        assert "test_char" in result.data["svg_path"]


# --- CharacterRigRenderer upgrade tests ---

from tools.character.character_animation import CharacterRigRenderer

MINIMAL_TIMELINE = {
    "version": "1.0",
    "scenes": [{"id": "s1", "start_seconds": 0, "end_seconds": 3,
                "actions": [{"character_id": "test_char", "pose": "idle"}]}],
}

class TestCharacterRigRendererRealSvg:
    def test_preview_html_contains_real_svg_when_svg_content_provided(self, tmp_path):
        tool = CharacterRigRenderer()
        result = tool.execute({
            "action_timeline": MINIMAL_TIMELINE,
            "svg_content": MINIMAL_SVG,
            "output_path": str(tmp_path / "preview.html"),
        })
        assert result.success
        html = (tmp_path / "preview.html").read_text()
        # Real SVG contains the character's actual IDs, not placeholder ellipses
        assert 'id="body"' in html
        assert 'id="head"' in html
        # No placeholder geometry
        assert "rgba(0,0,0,.18)" not in html

    def test_falls_back_to_placeholder_when_no_svg_provided(self, tmp_path):
        tool = CharacterRigRenderer()
        result = tool.execute({
            "action_timeline": MINIMAL_TIMELINE,
            "output_path": str(tmp_path / "preview.html"),
        })
        assert result.success
        html = (tmp_path / "preview.html").read_text()
        # Placeholder geometry still present
        assert "rgba(0,0,0,.18)" in html

    def test_accepts_svg_path_input(self, tmp_path):
        svg_file = tmp_path / "char.svg"
        svg_file.write_text(MINIMAL_SVG, encoding="utf-8")
        tool = CharacterRigRenderer()
        result = tool.execute({
            "action_timeline": MINIMAL_TIMELINE,
            "svg_path": str(svg_file),
            "output_path": str(tmp_path / "preview.html"),
        })
        assert result.success
        html = (tmp_path / "preview.html").read_text()
        assert 'id="body"' in html


# ── Hierarchical SVG fixture ──────────────────────────────────────────────────

HIERARCHICAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <g id="body"><rect x="156" y="280" width="200" height="200" fill="#4a9eff"/></g>
  <g id="head">
    <g id="head-art"><circle cx="256" cy="200" r="90" fill="#ffcc88"/></g>
    <g id="eyes-open-joint">
      <g id="eyes-open-art">
        <circle cx="225" cy="185" r="12" fill="#333"/>
        <circle cx="287" cy="185" r="12" fill="#333"/>
      </g>
    </g>
    <g id="mouth-neutral-joint">
      <g id="mouth-neutral-art">
        <path d="M225 240 Q256 265 287 240" fill="none" stroke="#333" stroke-width="4"/>
      </g>
    </g>
  </g>
  <g id="upper-arm-l-joint" transform="translate(156,300)">
    <g id="upper-arm-l-art"><rect x="-15" y="0" width="30" height="80" fill="#4a9eff"/></g>
    <g id="forearm-l-joint" transform="translate(0,80)">
      <g id="forearm-l-art"><rect x="-12" y="0" width="24" height="70" fill="#4a9eff"/></g>
    </g>
  </g>
</svg>"""

HIERARCHICAL_RIG = {
    "version": "1.0",
    "assetId": "test_hierarchical",
    "parts": [
        {"id": "body",              "parentId": None,               "pivot": {"x": 256, "y": 400}},
        {"id": "head",              "parentId": None,               "pivot": {"x": 256, "y": 200}},
        {"id": "head-art",          "parentId": "head",             "pivot": {"x": 0, "y": 0}},
        {"id": "eyes-open-joint",   "parentId": "head",             "pivot": {"x": 0, "y": 0}},
        {"id": "eyes-open-art",     "parentId": "eyes-open-joint",  "pivot": {"x": 0, "y": 0}},
        {"id": "mouth-neutral-joint","parentId": "head",            "pivot": {"x": 0, "y": 0}},
        {"id": "mouth-neutral-art", "parentId": "mouth-neutral-joint","pivot": {"x": 0, "y": 0}},
        {"id": "upper-arm-l-joint", "parentId": None,               "pivot": {"x": 0, "y": 0}},
        {"id": "upper-arm-l-art",   "parentId": "upper-arm-l-joint","pivot": {"x": 0, "y": 0}},
        {"id": "forearm-l-joint",   "parentId": "upper-arm-l-joint","pivot": {"x": 0, "y": 0}},
        {"id": "forearm-l-art",     "parentId": "forearm-l-joint",  "pivot": {"x": 0, "y": 0}},
    ],
}

HIERARCHICAL_POSES = {
    "assetId": "test_hierarchical",
    "poses": [
        {"id": "idle", "name": "Idle", "transforms": {"head": {"rotation": 0}}},
        {"id": "talk_open", "name": "Talk Open",
         "transforms": {"mouth-neutral-joint": {"scaleY": 0}, "eyes-open-joint": {"scaleY": 1}}},
    ],
}

HIERARCHICAL_ASSET_SPEC = {
    "id": "test_hierarchical",
    "name": "Hierarchical Test Character",
    "style": "test",
    "description": "Test character with hierarchical rig",
    "viewBox": "0 0 512 512",
}


def test_hierarchical_rig_valid(tmp_path):
    """Valid hierarchical SVG with matching parentId passes."""
    writer = SvgCharacterWriter()
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": HIERARCHICAL_RIG,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert result.success, result.error


def test_nesting_mismatch_fails(tmp_path):
    """parentId in manifest that doesn't match SVG nesting fails validation."""
    bad_rig = {
        **HIERARCHICAL_RIG,
        "parts": [
            *HIERARCHICAL_RIG["parts"][:2],
            # forearm-l-joint claims parent is body, but SVG has it inside upper-arm-l-joint
            {"id": "forearm-l-joint", "parentId": "body", "pivot": {"x": 0, "y": 0}},
        ],
    }
    writer = SvgCharacterWriter()
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": bad_rig,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert not result.success
    assert "forearm-l-joint" in result.error
    assert "nesting" in result.error.lower() or "parent" in result.error.lower()


def test_parentid_none_at_svg_root_passes(tmp_path):
    """Part with parentId=None that is a top-level SVG group passes."""
    writer = SvgCharacterWriter()
    rig = {
        "version": "1.0",
        "assetId": "test_hierarchical",
        "parts": [
            {"id": "body", "parentId": None, "pivot": {"x": 256, "y": 400}},
            {"id": "head", "parentId": None, "pivot": {"x": 256, "y": 200}},
        ],
    }
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": rig,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert result.success, result.error
