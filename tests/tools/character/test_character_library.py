"""Tests for CharacterLibrary tool."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.character.character_library import CharacterLibrary

SPEC = {
    "id": "wizard_cat",
    "name": "Wizard Cat",
    "description": "A cat in a wizard hat",
    "style": "Flat Vector",
    "colors": {"body": "#9c44cc", "skin": "#f0c090"},
}
SVG = '<svg viewBox="0 0 512 512"><g id="body"/><g id="head"/></svg>'
RIG = {"version": "1.0", "assetId": "wizard_cat",
       "parts": [{"id": "body", "parent": None, "pivot": {"x": 256, "y": 400}, "depth": 0},
                 {"id": "head", "parent": "body", "pivot": {"x": 256, "y": 200}, "depth": 1}]}
POSES = {"assetId": "wizard_cat",
         "poses": [{"id": "idle", "name": "Idle", "transforms": {}}]}


class TestCharacterLibraryList:
    def test_returns_empty_list_when_library_absent(self, tmp_path):
        tool = CharacterLibrary()
        result = tool.execute({"action": "list", "library_path": str(tmp_path / "lib")})
        assert result.success
        assert result.data["characters"] == []

    def test_lists_saved_characters(self, tmp_path):
        tool = CharacterLibrary()
        lib = str(tmp_path / "lib")
        tool.execute({"action": "save", "library_path": lib,
                      "asset_spec": SPEC, "svg_content": SVG,
                      "rig_manifest": RIG, "pose_library": POSES})
        result = tool.execute({"action": "list", "library_path": lib})
        assert result.success
        assert len(result.data["characters"]) == 1
        assert result.data["characters"][0]["id"] == "wizard_cat"
        assert result.data["characters"][0]["name"] == "Wizard Cat"


class TestCharacterLibrarySave:
    def test_writes_all_required_files(self, tmp_path):
        tool = CharacterLibrary()
        lib = str(tmp_path / "lib")
        result = tool.execute({"action": "save", "library_path": lib,
                               "asset_spec": SPEC, "svg_content": SVG,
                               "rig_manifest": RIG, "pose_library": POSES})
        assert result.success
        char_dir = Path(lib) / "wizard-cat"
        for fname in ["asset_spec.json", "character.svg", "rig_manifest.json", "pose_library.json"]:
            assert (char_dir / fname).exists(), f"Missing: {fname}"

    def test_save_uses_slug_of_character_id(self, tmp_path):
        tool = CharacterLibrary()
        lib = str(tmp_path / "lib")
        tool.execute({"action": "save", "library_path": lib,
                      "asset_spec": SPEC, "svg_content": SVG,
                      "rig_manifest": RIG, "pose_library": POSES})
        assert (Path(lib) / "wizard-cat").is_dir()

    def test_fails_when_required_fields_missing(self, tmp_path):
        tool = CharacterLibrary()
        result = tool.execute({"action": "save", "library_path": str(tmp_path),
                               "asset_spec": SPEC})
        assert not result.success
        assert "svg_content" in result.error

    def test_copies_preview_html_when_source_dir_provided(self, tmp_path):
        # Write a fake preview.html in source_dir
        src = tmp_path / "src"
        src.mkdir()
        (src / "preview.html").write_text("<html>preview</html>")
        tool = CharacterLibrary()
        lib = str(tmp_path / "lib")
        result = tool.execute({"action": "save", "library_path": lib,
                               "asset_spec": SPEC, "svg_content": SVG,
                               "rig_manifest": RIG, "pose_library": POSES,
                               "source_dir": str(src)})
        assert result.success
        assert (Path(lib) / "wizard-cat" / "preview.html").exists()


class TestCharacterLibraryLoad:
    def test_loads_saved_character(self, tmp_path):
        tool = CharacterLibrary()
        lib = str(tmp_path / "lib")
        tool.execute({"action": "save", "library_path": lib,
                      "asset_spec": SPEC, "svg_content": SVG,
                      "rig_manifest": RIG, "pose_library": POSES})
        result = tool.execute({"action": "load", "library_path": lib,
                               "character_id": "wizard_cat"})
        assert result.success
        assert result.data["asset_spec"]["name"] == "Wizard Cat"
        assert result.data["svg_content"] == SVG

    def test_fails_when_character_not_found(self, tmp_path):
        tool = CharacterLibrary()
        result = tool.execute({"action": "load", "library_path": str(tmp_path),
                               "character_id": "nonexistent"})
        assert not result.success
        assert "nonexistent" in result.error

    def test_fails_when_character_id_missing(self, tmp_path):
        tool = CharacterLibrary()
        result = tool.execute({"action": "load", "library_path": str(tmp_path)})
        assert not result.success
