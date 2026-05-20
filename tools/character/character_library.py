"""Character library — save, load, and list reusable character assets."""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolTier,
)

_DEFAULT_LIBRARY = Path("character_library")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class CharacterLibrary(BaseTool):
    name = "character_library"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "character_animation"
    provider = "openmontage"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=32, vram_mb=0, disk_mb=0)
    capabilities = ["list_characters", "load_character", "save_character"]
    best_for = ["reusing characters across multiple videos for visual consistency"]
    input_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action":       {"type": "string", "enum": ["list", "load", "save"]},
            "character_id": {"type": "string"},
            "asset_spec":   {"type": "object"},
            "svg_content":  {"type": "string"},
            "rig_manifest": {"type": "object"},
            "pose_library": {"type": "object"},
            "source_dir":   {"type": "string",
                             "description": "Copy preview.html from this directory (output_dir from SvgCharacterWriter)"},
            "library_path": {"type": "string",
                             "description": "Override library root. Default: character_library/"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "characters":   {"type": "array"},
            "character_id": {"type": "string"},
            "asset_spec":   {"type": "object"},
            "svg_content":  {"type": "string"},
            "rig_manifest": {"type": "object"},
            "pose_library": {"type": "object"},
            "preview_path": {"type": "string"},
            "saved_to":     {"type": "string"},
        },
    }
    side_effects = ["writes files to character_library/<slug>/ when action=save"]

    def _root(self, inputs: dict) -> Path:
        return Path(inputs["library_path"]) if inputs.get("library_path") else _DEFAULT_LIBRARY

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        action = inputs.get("action")
        if action == "list":
            return self._list(inputs, start)
        if action == "load":
            return self._load(inputs, start)
        if action == "save":
            return self._save(inputs, start)
        return ToolResult(success=False, error=f"Unknown action: {action!r}")

    def _list(self, inputs: dict, start: float) -> ToolResult:
        root = self._root(inputs)
        if not root.exists():
            return ToolResult(success=True, data={"characters": []},
                              duration_seconds=round(time.time() - start, 3))
        characters = []
        for char_dir in sorted(root.iterdir()):
            spec_path = char_dir / "asset_spec.json"
            if not (char_dir.is_dir() and spec_path.exists()):
                continue
            spec = json.loads(spec_path.read_text())
            characters.append({
                "id":           spec["id"],
                "name":         spec.get("name", spec["id"]),
                "style":        spec.get("style", ""),
                "description":  spec.get("description", ""),
                "preview_path": str(char_dir / "preview.html"),
                "svg_path":     str(char_dir / "character.svg"),
            })
        return ToolResult(success=True, data={"characters": characters},
                          duration_seconds=round(time.time() - start, 3))

    def _load(self, inputs: dict, start: float) -> ToolResult:
        character_id = inputs.get("character_id")
        if not character_id:
            return ToolResult(success=False, error="character_id is required for action=load")
        root = self._root(inputs)
        char_dir = root / _slug(character_id)
        if not char_dir.exists():
            return ToolResult(
                success=False,
                error=f"Character '{character_id}' not found in library at {root}",
            )
        return ToolResult(
            success=True,
            data={
                "character_id": character_id,
                "asset_spec":   json.loads((char_dir / "asset_spec.json").read_text()),
                "svg_content":  (char_dir / "character.svg").read_text(encoding="utf-8"),
                "rig_manifest": json.loads((char_dir / "rig_manifest.json").read_text()),
                "pose_library": json.loads((char_dir / "pose_library.json").read_text()),
                "preview_path": str(char_dir / "preview.html"),
            },
            duration_seconds=round(time.time() - start, 3),
        )

    def _save(self, inputs: dict, start: float) -> ToolResult:
        required = ["asset_spec", "svg_content", "rig_manifest", "pose_library"]
        missing = [k for k in required if not inputs.get(k)]
        if missing:
            return ToolResult(success=False,
                              error=f"Missing required fields for action=save: {missing}")
        spec = inputs["asset_spec"]
        character_id = spec["id"]
        root = self._root(inputs)
        char_dir = root / _slug(character_id)
        char_dir.mkdir(parents=True, exist_ok=True)

        (char_dir / "asset_spec.json").write_text(
            json.dumps(spec, indent=2), encoding="utf-8")
        (char_dir / "character.svg").write_text(
            inputs["svg_content"], encoding="utf-8")
        (char_dir / "rig_manifest.json").write_text(
            json.dumps(inputs["rig_manifest"], indent=2), encoding="utf-8")
        (char_dir / "pose_library.json").write_text(
            json.dumps(inputs["pose_library"], indent=2), encoding="utf-8")

        if inputs.get("source_dir"):
            preview_src = Path(inputs["source_dir"]) / "preview.html"
            if preview_src.exists():
                shutil.copy(preview_src, char_dir / "preview.html")

        return ToolResult(
            success=True,
            data={"character_id": character_id, "saved_to": str(char_dir)},
            duration_seconds=round(time.time() - start, 3),
        )
