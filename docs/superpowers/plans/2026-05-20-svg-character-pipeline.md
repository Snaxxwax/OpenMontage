# SVG Character Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the OpenMontage agent to generate real styled SVG characters, preview them, save them to a persistent library, and render them into MP4 videos using the `svg-character` pipeline.

**Architecture:** The agent generates SVG + rig manifest + pose library inline (guided by `svg-character-animation` and `character-rigging` Layer 3 skills). `SvgCharacterWriter` validates part-ID consistency and writes files. `CharacterLibrary` persists characters for cross-project reuse. `CharacterRigRenderer` is upgraded to accept real SVG instead of generating placeholder blobs. A new `svg-character` pipeline replaces the two-stage `character_design → rig_plan` sequence with a single `character_generation` stage.

**Tech Stack:** Python 3.11, `tools/base_tool.py` BaseTool pattern, pytest, JSON schema validation via `schemas/artifacts/`, YAML pipeline manifests, GSAP 3.12 (CDN in preview HTML)

---

## File Map

**New files:**
- `tools/character/svg_character_writer.py` — `SvgCharacterWriter` BaseTool: validates SVG/rig consistency, writes character files, returns OpenMontage artifacts
- `tools/character/character_library.py` — `CharacterLibrary` BaseTool: save/load/list persistent characters
- `tests/tools/character/__init__.py` — test package marker
- `tests/tools/character/test_svg_character_writer.py` — TDD tests for SvgCharacterWriter
- `tests/tools/character/test_character_library.py` — TDD tests for CharacterLibrary
- `pipeline_defs/svg-character.yaml` — new pipeline manifest
- `skills/pipelines/svg-character/character-generation-director.md` — main new director skill
- `skills/pipelines/svg-character/research-director.md` — delegates to character-animation
- `skills/pipelines/svg-character/proposal-director.md` — adds library check
- `skills/pipelines/svg-character/script-director.md` — delegates
- `skills/pipelines/svg-character/scene-director.md` — delegates
- `skills/pipelines/svg-character/asset-director.md` — delegates, notes char assets pre-built
- `skills/pipelines/svg-character/edit-director.md` — delegates
- `skills/pipelines/svg-character/compose-director.md` — delegates
- `skills/pipelines/svg-character/publish-director.md` — delegates
- `character_library/.gitkeep` — seeds the gitignored library directory

**Modified files:**
- `tools/character/character_animation.py` — upgrade `CharacterRigRenderer` to accept `svg_content`/`svg_path` inputs
- `.gitignore` — add `character_library/` (keep `.gitkeep`)

---

## Task 1: SvgCharacterWriter — TDD

**Files:**
- Create: `tools/character/svg_character_writer.py`
- Create: `tests/tools/character/__init__.py`
- Create: `tests/tools/character/test_svg_character_writer.py`

- [ ] **Step 1: Create test package**

```bash
mkdir -p tests/tools/character
touch tests/tools/character/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `tests/tools/character/test_svg_character_writer.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /home/pop/repos/openmontage-asymmetric
python -m pytest tests/tools/character/test_svg_character_writer.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` for `tools.character.svg_character_writer`

- [ ] **Step 4: Implement SvgCharacterWriter**

Create `tools/character/svg_character_writer.py`:

```python
"""SVG character writer — validates and persists agent-generated character assets."""

from __future__ import annotations

import json
import re
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


def _extract_group_ids(svg_content: str) -> set[str]:
    """Return all <g id="..."> IDs from SVG markup."""
    return set(re.findall(r'<g[^>]+\bid="([^"]+)"', svg_content))


def _to_rig_plan(asset_spec: dict, rig_manifest: dict, pose_library: dict) -> dict:
    """Convert VectorForge rig_manifest → OpenMontage rig_plan artifact."""
    character_id = asset_spec["id"]
    parts = []
    joints: dict[str, Any] = {}
    for part in rig_manifest.get("parts", []):
        entry: dict[str, Any] = {
            "id": part["id"],
            "kind": part.get("kind", "body"),
            "layer": part.get("depth", 0),
        }
        if part.get("parent") is not None:
            entry["parent"] = part["parent"]
        parts.append(entry)
        joints[part["id"]] = {"pivot": [part["pivot"]["x"], part["pivot"]["y"]]}

    depths = sorted({part.get("depth", 0) for part in rig_manifest.get("parts", [])})
    layers = [f"layer_{d}" for d in depths] or ["default"]
    pose_ids = [p["id"] for p in pose_library.get("poses", [])]

    return {
        "version": "1.0",
        "characters": [{
            "character_id": character_id,
            "rig_type": "svg_rig",
            "parts": parts,
            "joints": joints,
            "layers": layers,
            "required_poses": pose_ids,
        }],
        "metadata": {"source": "svg_character_writer"},
    }


def _to_pose_library(asset_spec: dict, pose_library: dict) -> dict:
    """Convert VectorForge pose_library → OpenMontage pose_library artifact."""
    character_id = asset_spec["id"]
    poses: dict[str, Any] = {}
    for pose in pose_library.get("poses", []):
        poses[pose["id"]] = {
            "description": pose.get("name", pose["id"]),
            "parts": dict(pose.get("transforms", {})),
        }
    return {
        "version": "1.0",
        "characters": [{"character_id": character_id, "poses": poses}],
        "metadata": {"source": "svg_character_writer"},
    }


def _build_preview_html(
    asset_spec: dict,
    svg_content: str,
    rig_manifest: dict,
    pose_library: dict,
) -> str:
    name = asset_spec.get("name", "Character")
    rig_json = json.dumps(rig_manifest)
    pose_json = json.dumps(pose_library)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Preview: {name}</title>
<style>
  body {{ background: #0f172a; display: flex; flex-direction: column; align-items: center;
         justify-content: center; min-height: 100vh; margin: 0; font-family: system-ui, sans-serif; }}
  .canvas {{ width: 512px; height: 512px; border: 1px solid #334155; border-radius: 12px; overflow: hidden; }}
  .canvas svg {{ width: 100%; height: 100%; }}
  .controls {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
               padding: 16px; max-width: 560px; }}
  button {{ padding: 8px 16px; background: #1e293b; color: #cbd5e1; border: 1px solid #334155;
            border-radius: 6px; cursor: pointer; font-size: 13px; transition: background 0.15s; }}
  button:hover, button.active {{ background: #0ea5e9; color: #fff; border-color: #0ea5e9; }}
  h2 {{ color: #f1f5f9; font-size: 16px; margin: 24px 0 8px; font-weight: 600; }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
</head>
<body>
  <h2>{name}</h2>
  <div class="canvas">{svg_content}</div>
  <div class="controls" id="pose-controls"></div>
  <script>
    const rigManifest = {rig_json};
    const poseLibrary = {pose_json};

    rigManifest.parts.forEach(part => {{
      const el = document.getElementById(part.id);
      if (el) gsap.set(el, {{ svgOrigin: `${{part.pivot.x}} ${{part.pivot.y}}` }});
    }});

    function applyPose(poseId) {{
      const pose = poseLibrary.poses.find(p => p.id === poseId);
      if (!pose) return;
      document.querySelectorAll('.controls button').forEach(b =>
        b.classList.toggle('active', b.dataset.pose === poseId));
      if (pose.id === 'blink') {{
        const open = document.getElementById('eyes-open');
        const closed = document.getElementById('eyes-closed');
        if (open && closed) {{
          gsap.set(open, {{ display: 'none' }});
          gsap.set(closed, {{ display: 'block' }});
          setTimeout(() => {{
            gsap.set(open, {{ display: 'block' }});
            gsap.set(closed, {{ display: 'none' }});
          }}, 150);
        }}
        return;
      }}
      const idlePose = poseLibrary.poses.find(p => p.id === 'idle');
      rigManifest.parts.forEach(part => {{
        const el = document.getElementById(part.id);
        if (!el) return;
        const idle = idlePose?.transforms?.[part.id] || {{}};
        const tx   = pose.transforms?.[part.id]  || {{}};
        gsap.to(el, {{
          rotation: tx.rotation  ?? idle.rotation  ?? 0,
          x:        tx.x         ?? idle.x         ?? 0,
          y:        tx.y         ?? idle.y         ?? 0,
          scaleX:   tx.scaleX    ?? idle.scaleX    ?? 1,
          scaleY:   tx.scaleY    ?? idle.scaleY    ?? 1,
          duration: 0.4, ease: 'power2.out',
        }});
      }});
    }}

    const controls = document.getElementById('pose-controls');
    poseLibrary.poses.forEach(pose => {{
      const btn = document.createElement('button');
      btn.textContent = pose.name;
      btn.dataset.pose = pose.id;
      btn.onclick = () => applyPose(pose.id);
      controls.appendChild(btn);
    }});
    applyPose('idle');
  </script>
</body>
</html>"""


class SvgCharacterWriter(BaseTool):
    name = "svg_character_writer"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "character_animation"
    provider = "openmontage"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=64, vram_mb=0, disk_mb=10)
    agent_skills = ["svg-character-animation", "character-rigging"]
    capabilities = ["validate_svg_rig_consistency", "write_character_assets",
                    "convert_to_openmontage_artifacts"]
    best_for = ["validating and persisting agent-generated SVG character bundles"]
    input_schema = {
        "type": "object",
        "required": ["svg_content", "rig_manifest", "pose_library", "asset_spec"],
        "properties": {
            "svg_content":  {"type": "string", "description": "Raw SVG markup"},
            "rig_manifest": {"type": "object", "description": "VectorForge-style rig manifest"},
            "pose_library": {"type": "object", "description": "VectorForge-style pose library"},
            "asset_spec":   {"type": "object", "description": "Character metadata (id, name, style, colors)"},
            "output_dir":   {"type": "string",
                             "description": "Directory to write files. Default: projects/character-assets/<id>/"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "svg_path":     {"type": "string"},
            "preview_path": {"type": "string"},
            "output_dir":   {"type": "string"},
            "rig_plan":     {"type": "object", "description": "OpenMontage rig_plan artifact"},
            "pose_library": {"type": "object", "description": "OpenMontage pose_library artifact"},
        },
    }
    side_effects = [
        "writes character.svg, rig_manifest.json, pose_library.json, "
        "asset_spec.json, preview.html to output_dir",
    ]
    user_visible_verification = ["Open preview.html in a browser and confirm the character renders"]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        svg_content: str = inputs["svg_content"]
        rig_manifest: dict = inputs["rig_manifest"]
        pose_library_in: dict = inputs["pose_library"]
        asset_spec: dict = inputs["asset_spec"]
        character_id = asset_spec["id"]
        output_dir = Path(
            inputs.get("output_dir") or f"projects/character-assets/{character_id}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        # Validate: every rig part ID must exist as a <g id="..."> in the SVG
        svg_ids = _extract_group_ids(svg_content)
        rig_ids = {part["id"] for part in rig_manifest.get("parts", [])}
        missing = rig_ids - svg_ids
        if missing:
            return ToolResult(
                success=False,
                error=(
                    f"SVG is missing <g> elements for rig parts: {sorted(missing)}. "
                    f"IDs found in SVG: {sorted(svg_ids)}"
                ),
            )

        # Write raw files
        (output_dir / "character.svg").write_text(svg_content, encoding="utf-8")
        (output_dir / "rig_manifest.json").write_text(
            json.dumps(rig_manifest, indent=2), encoding="utf-8"
        )
        (output_dir / "pose_library.json").write_text(
            json.dumps(pose_library_in, indent=2), encoding="utf-8"
        )
        (output_dir / "asset_spec.json").write_text(
            json.dumps(asset_spec, indent=2), encoding="utf-8"
        )

        # Write preview HTML
        preview_html = _build_preview_html(
            asset_spec, svg_content, rig_manifest, pose_library_in
        )
        preview_path = output_dir / "preview.html"
        preview_path.write_text(preview_html, encoding="utf-8")

        # Convert to OpenMontage artifact schemas
        om_rig_plan = _to_rig_plan(asset_spec, rig_manifest, pose_library_in)
        om_pose_library = _to_pose_library(asset_spec, pose_library_in)

        return ToolResult(
            success=True,
            data={
                "svg_path":     str(output_dir / "character.svg"),
                "preview_path": str(preview_path),
                "output_dir":   str(output_dir),
                "rig_plan":     om_rig_plan,
                "pose_library": om_pose_library,
            },
            artifacts=[str(output_dir / "character.svg"), str(preview_path)],
            duration_seconds=round(time.time() - start, 3),
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/tools/character/test_svg_character_writer.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add tools/character/svg_character_writer.py \
        tests/tools/character/__init__.py \
        tests/tools/character/test_svg_character_writer.py
git commit -m "feat(tools): add SvgCharacterWriter — validates SVG/rig consistency, writes character assets"
```

---

## Task 2: CharacterLibrary — TDD

**Files:**
- Create: `tools/character/character_library.py`
- Create: `tests/tools/character/test_character_library.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/character/test_character_library.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/tools/character/test_character_library.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError` for `tools.character.character_library`

- [ ] **Step 3: Implement CharacterLibrary**

Create `tools/character/character_library.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/tools/character/test_character_library.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/character/character_library.py \
        tests/tools/character/test_character_library.py
git commit -m "feat(tools): add CharacterLibrary — save/load/list persistent character assets"
```

---

## Task 3: Upgrade CharacterRigRenderer to accept real SVG

**Files:**
- Modify: `tools/character/character_animation.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/tools/character/test_svg_character_writer.py` (append after existing tests):

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/tools/character/test_svg_character_writer.py::TestCharacterRigRendererRealSvg -v
```

Expected: FAIL — `svg_content` input not handled yet

- [ ] **Step 3: Add helper function and upgrade CharacterRigRenderer**

In `tools/character/character_animation.py`, add this helper after the existing `_normalize_style` function (around line 54):

```python
def _unwrap_svg(svg_content: str) -> tuple[str, str]:
    """Strip outer <svg> wrapper, returning (inner_markup, viewbox_value)."""
    vb = re.search(r'viewBox=["\']([^"\']+)["\']', svg_content)
    viewbox = vb.group(1) if vb else "0 0 512 512"
    inner = re.sub(r"<svg[^>]*>", "", svg_content, count=1, flags=re.DOTALL)
    inner = re.sub(r"</svg>\s*$", "", inner.strip(), flags=re.DOTALL)
    return inner.strip(), viewbox
```

Add `import re` to the imports at the top of `character_animation.py` if not already present.

In `CharacterRigRenderer.input_schema["properties"]`, add:

```python
"svg_content": {"type": "string", "description": "Real SVG markup from SvgCharacterWriter. Overrides placeholder generation."},
"svg_path":    {"type": "string", "description": "Path to character.svg written by SvgCharacterWriter."},
```

In `CharacterRigRenderer.execute()`, insert this block immediately **after** the line `rig_characters = (inputs.get("rig_plan") or {}).get("characters", [])` and **before** the `if not rig_characters:` block:

```python
        # Real SVG support: use agent-generated character instead of placeholder blobs
        real_svg_content: str | None = None
        if inputs.get("svg_content"):
            real_svg_content = inputs["svg_content"]
        elif inputs.get("svg_path"):
            svg_p = Path(inputs["svg_path"])
            if svg_p.exists():
                real_svg_content = svg_p.read_text(encoding="utf-8")
```

Then replace the existing placeholder-generation block (from `count = len(rig_characters)` through the end of the `character_svgs` append loop) with:

```python
        if real_svg_content:
            inner_svg, viewbox = _unwrap_svg(real_svg_content)
            cid = _slug(
                rig_characters[0].get("character_id", "character-0")
                if rig_characters else "character-0"
            )
            viewbox_attr = viewbox
            character_svgs = [
                f'<g class="character" id="character_{cid}" data-character="{cid}">'
                f"{inner_svg}</g>"
            ]
        else:
            count = len(rig_characters)
            spacing = 620 / max(count, 1)
            viewbox_attr = "0 0 640 640"
            character_svgs = []
            for index, character in enumerate(rig_characters):
                cid = _slug(character.get("character_id", f"character-{index + 1}"))
                x = 110 + spacing * index if count > 1 else 320
                scale = 0.82 if count > 1 else 1
                body_fill, head_fill = _character_color(index)
                character_svgs.append(
                    f"""
      <g class=\"character\" id=\"character_{cid}\" data-character=\"{cid}\" transform=\"translate({x - 320:.1f} 0) scale({scale})\">
        <ellipse class=\"shadow\" cx=\"320\" cy=\"560\" rx=\"120\" ry=\"22\" fill=\"rgba(0,0,0,.18)\" />
        <ellipse class=\"body outline\" cx=\"320\" cy=\"400\" rx=\"80\" ry=\"120\" fill=\"{body_fill}\" />
        <circle class=\"head outline\" cx=\"320\" cy=\"230\" r=\"90\" fill=\"{head_fill}\" />
        <ellipse class=\"eye eye-left outline\" cx=\"285\" cy=\"215\" rx=\"18\" ry=\"26\" fill=\"white\" />
        <ellipse class=\"eye eye-right outline\" cx=\"355\" cy=\"215\" rx=\"18\" ry=\"26\" fill=\"white\" />
        <circle class=\"pupil pupil-left\" cx=\"289\" cy=\"218\" r=\"8\" fill=\"#202632\" />
        <circle class=\"pupil pupil-right\" cx=\"359\" cy=\"218\" r=\"8\" fill=\"#202632\" />
        <path class=\"mouth outline\" d=\"M285 275 Q320 305 355 275\" fill=\"none\" />
        <path class=\"arm arm-left outline\" d=\"M255 360 C210 380 190 420 180 455\" fill=\"none\" />
        <path class=\"arm arm-right outline\" d=\"M385 360 C440 330 465 290 475 240\" fill=\"none\" />
      </g>"""
                )
```

Finally, update both SVG `viewBox` attributes in the `html` and `composition_html` f-strings — change the hardcoded `viewBox=\"0 0 640 640\"` to `viewBox=\"{viewbox_attr}\"`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/tools/character/test_svg_character_writer.py -v
```

Expected: all tests PASS including the new `TestCharacterRigRendererRealSvg` class

- [ ] **Step 5: Commit**

```bash
git add tools/character/character_animation.py \
        tests/tools/character/test_svg_character_writer.py
git commit -m "feat(tools): upgrade CharacterRigRenderer to accept real SVG from SvgCharacterWriter"
```

---

## Task 4: `svg-character` pipeline YAML + contract test

**Files:**
- Create: `pipeline_defs/svg-character.yaml`
- Modify: `tests/contracts/test_phase0_contracts.py`

- [ ] **Step 1: Write the contract test first**

Add to `tests/contracts/test_phase0_contracts.py`, inside the existing `TestPipelineManifests` class (find it by `grep -n "class TestPipeline" tests/contracts/test_phase0_contracts.py`):

```python
    def test_svg_character_manifest_loads(self):
        manifest = load_pipeline("svg-character")
        assert manifest["name"] == "svg-character"
        stages = get_stage_order(manifest)
        assert "character_generation" in stages
        assert "character_design" not in stages
        assert "rig_plan" not in stages

    def test_svg_character_listed(self):
        assert "svg-character" in list_pipelines()

    def test_svg_character_generation_stage_tools(self):
        manifest = load_pipeline("svg-character")
        stage = next(s for s in manifest["stages"] if s["name"] == "character_generation")
        assert "svg_character_writer" in stage.get("tools_available", [])
        assert "character_library" in stage.get("tools_available", [])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/contracts/test_phase0_contracts.py -k "svg_character" -v
```

Expected: FAIL — `svg-character` pipeline file not found

- [ ] **Step 3: Create the pipeline manifest**

Create `pipeline_defs/svg-character.yaml`:

```yaml
name: svg-character
version: "0.1"
description: >
  SVG character video pipeline. The agent generates styled, rigged SVG characters
  directly from text prompts guided by svg-character-animation and character-rigging
  Layer 3 skills. Characters are animated to script-driven poses and audio using
  HyperFrames or Remotion, then rendered to MP4. Supports a persistent character
  library for cross-project visual consistency.
category: animation
stability: beta
default_checkpoint_policy: guided

reference_input:
  supported: true
  analysis_depth: standard
  analysis_tools:
    - video_analyzer
    - transcript_fetcher
    - scene_detect
    - frame_sampler

orchestration:
  mode: executive-producer
  skill: pipelines/character-animation/executive-producer
  budget_default_usd: 2.00
  max_revisions_per_stage: 3
  max_send_backs: 3
  max_wall_time_minutes: 20

compatible_playbooks:
  recommended:
    - flat-motion-graphics
  also_works:
    - clean-professional
    - minimalist-diagram
  custom_allowed: true

stages:
  - name: research
    skill: pipelines/svg-character/research-director
    produces:
      - research_brief
    tools_available: []
    checkpoint_required: false
    human_approval_default: false
    review_focus:
      - Reference style and character-animation technique are researched when a reference exists
      - At least 3 comparable character-animation examples are summarized
    success_criteria:
      - Schema-valid research_brief

  - name: proposal
    skill: pipelines/svg-character/proposal-director
    required_artifacts_in:
      - research_brief
    produces:
      - proposal_packet
      - decision_log
    tools_available:
      - character_library
    checkpoint_required: true
    human_approval_default: true
    review_focus:
      - Character library was checked before proposing new generation
      - Concepts are differentiated and not a carbon copy of any reference
      - Render runtime selection presents HyperFrames and Remotion when both available
    success_criteria:
      - Schema-valid proposal_packet
      - User approval recorded before character generation begins

  - name: script
    skill: pipelines/svg-character/script-director
    required_artifacts_in:
      - proposal_packet
    produces:
      - script
    tools_available:
      - transcriber
    checkpoint_required: true
    human_approval_default: true
    review_focus:
      - Script is written as action beats, not only narration
      - Every emotional turn can be expressed with poses
    success_criteria:
      - Schema-valid script

  - name: character_generation
    skill: pipelines/svg-character/character-generation-director
    required_artifacts_in:
      - script
      - proposal_packet
    produces:
      - character_design
      - rig_plan
      - pose_library
    tools_available:
      - svg_character_writer
      - character_library
    checkpoint_required: true
    human_approval_default: true
    review_focus:
      - SVG part IDs match rig manifest exactly — SvgCharacterWriter must report success
      - Required poses include idle, blink, talk_open, talk_closed, and at least one expression
      - Character style matches the approved concept
      - Character offered for library save after approval
    success_criteria:
      - Schema-valid character_design
      - Schema-valid rig_plan
      - Schema-valid pose_library
      - character.svg written to projects/<name>/assets/characters/
      - SvgCharacterWriter reports success with no validation errors

  - name: scene_plan
    skill: pipelines/svg-character/scene-director
    required_artifacts_in:
      - script
      - character_design
      - rig_plan
      - pose_library
    produces:
      - scene_plan
    tools_available: []
    checkpoint_required: true
    human_approval_default: true
    review_focus:
      - Scenes use character_scene or animation types with timed actions
      - Each scene maps actions to poses from the pose library
    success_criteria:
      - Schema-valid scene_plan

  - name: assets
    skill: pipelines/svg-character/asset-director
    required_artifacts_in:
      - character_design
      - rig_plan
      - pose_library
      - scene_plan
    produces:
      - asset_manifest
    tools_available:
      - image_selector
      - tts_selector
      - music_gen
      - character_rig_renderer
    checkpoint_required: true
    human_approval_default: false
    review_focus:
      - Character assets come from character_generation — do not regenerate them
      - TTS and music are generated or sourced as planned
      - svg_path from character_generation is passed to character_rig_renderer
    success_criteria:
      - Schema-valid asset_manifest

  - name: edit
    skill: pipelines/svg-character/edit-director
    required_artifacts_in:
      - scene_plan
      - asset_manifest
      - pose_library
    produces:
      - edit_decisions
      - action_timeline
    tools_available:
      - action_timeline_compiler
    checkpoint_required: true
    human_approval_default: false
    review_focus:
      - Action timeline preserves acting beats and emotional readability
      - render_runtime carried from proposal unchanged
    success_criteria:
      - Schema-valid edit_decisions
      - Schema-valid action_timeline

  - name: compose
    skill: pipelines/svg-character/compose-director
    required_artifacts_in:
      - edit_decisions
      - action_timeline
      - asset_manifest
    produces:
      - render_report
      - final_review
      - character_qa_report
    tools_available:
      - character_rig_renderer
      - character_animation_reviewer
      - video_compose
      - audio_mixer
    checkpoint_required: true
    human_approval_default: false
    review_focus:
      - Runtime chosen in proposal is the runtime actually used
      - Final MP4 passes ffprobe and character QA
    success_criteria:
      - Schema-valid render_report
      - Output exists and passes technical validation

  - name: publish
    skill: pipelines/svg-character/publish-director
    required_artifacts_in:
      - render_report
      - final_review
      - character_qa_report
    produces:
      - publish_log
    tools_available: []
    checkpoint_required: true
    human_approval_default: true
    review_focus:
      - Metadata describes the character-animation style honestly
    success_criteria:
      - Schema-valid publish_log
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/contracts/test_phase0_contracts.py -k "svg_character" -v
```

Expected: all 3 new tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline_defs/svg-character.yaml tests/contracts/test_phase0_contracts.py
git commit -m "feat(pipeline): add svg-character pipeline with character_generation stage"
```

---

## Task 5: `character-generation-director` skill

**Files:**
- Create: `skills/pipelines/svg-character/character-generation-director.md`

- [ ] **Step 1: Create the skills directory**

```bash
mkdir -p skills/pipelines/svg-character
```

- [ ] **Step 2: Write the skill**

Create `skills/pipelines/svg-character/character-generation-director.md`:

````markdown
# Character Generation Director

You are running the `character_generation` stage of the `svg-character` pipeline.
This stage replaces the two-stage `character_design → rig_plan` sequence with a
single coherent pass: you generate the SVG, rig manifest, and pose library yourself,
then validate and persist them with `SvgCharacterWriter`.

## Step 0 — Read Layer 3 skills first

Before generating anything, read these two skills:

1. `.agents/skills/hyperframes/SKILL.md` — for HyperFrames SVG animation conventions
2. The `svg-character-animation` and `character-rigging` skills referenced in
   `SvgCharacterWriter.agent_skills`

These contain the SVG structure requirements, part naming conventions, and pivot
point guidance you need. Do not skip this step.

## Step 1 — Check the character library

Call `CharacterLibrary` with `action=list`.

If any character matches the brief (similar style, role, or description), present
the user with three options:

> "I found a saved character — **[Name]** — that matches this brief.
> A) Reuse it as-is  B) Load it as a starting reference  C) Generate a new character"

- **A (reuse):** load the saved character bundle, skip to Step 5.
- **B (reference):** load the SVG and note the style, then proceed with generation
  using the existing character as a visual reference.
- **C (new):** proceed directly.

## Step 2 — Generate the SVG character

Using the approved concept from `proposal_packet` and the character role from
`script`, generate a complete SVG character inline.

### Required SVG structure

The SVG **must** use `viewBox="0 0 512 512"` and include a `<style>` block with
idle CSS animations. Every anatomical group **must** have an `id` attribute that
exactly matches a part in the rig manifest you will generate in Step 3.

**Mandatory `<g>` IDs (always present):**
- `body` — torso, shoulders, background attire. `transform-origin: bottom center`
- `head` — skull, hair, face shape. `transform-origin: bottom center`
- `eyes-open` — primary visible eyes
- `eyes-closed` — hidden by default (`style="display:none"`)
- `mouth-neutral` — resting mouth
- `mouth-open` — talking mouth, hidden by default (`style="display:none"`)

**Additional IDs as needed by the character type** (include in rig manifest):
- `arm-left`, `arm-right` — for humanoid characters
- `leg-left`, `leg-right` — if legs are visible and animated
- `tail`, `ears`, `hat`, `prop` — for non-humanoid features

**CSS animations to include:**
- Idle sway on `#body` and `#head`: subtle rotation ±2–4°, 3–5s `ease-in-out infinite`
- Blink on `#eyes-open`/`#eyes-closed`: `@keyframes blink` that toggles visibility
  every 3–5s for ~0.15s
- All animations use `transform-origin: bottom center` on body/head groups

**Style guidance** (from the approved concept):
- Flat Vector: bold solid fills, geometric shapes, clean paths
- Hand-Drawn: organic paths, irregular strokes, slightly imperfect geometry
- Cyberpunk: neon fills, glow effects via `<filter>`, high-contrast outlines

**Do not use:**
- `Math.random()` or dynamic JS in the SVG
- External image references
- Fonts that require loading

## Step 3 — Generate the rig manifest

Generate a VectorForge-style rig manifest. Every `id` in `parts` **must** exactly
match a `<g id="...">` in the SVG you generated in Step 2.

```json
{
  "version": "1.0",
  "assetId": "<character_id>",
  "parts": [
    { "id": "body",        "parent": null,   "pivot": {"x": 256, "y": 420}, "depth": 0 },
    { "id": "head",        "parent": "body", "pivot": {"x": 256, "y": 200}, "depth": 1 },
    { "id": "eyes-open",   "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2 },
    { "id": "eyes-closed", "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2 },
    { "id": "mouth-neutral","parent":"head", "pivot": {"x": 256, "y": 240}, "depth": 2 },
    { "id": "mouth-open",  "parent": "head", "pivot": {"x": 256, "y": 248}, "depth": 2 }
  ]
}
```

**Pivot point rules:**
- Pivot is the center of rotation in SVG viewbox coordinates (0–512 range)
- Body pivot: center-bottom of the torso (where it meets the ground)
- Head pivot: chin/neck junction
- Eyes/mouth: their own center
- Arms: shoulder joint
- Legs: hip joint

## Step 4 — Generate the pose library

Generate a VectorForge-style pose library. Required poses:

| id | name | What it expresses |
|----|------|-------------------|
| `idle` | Idle | Neutral standing, slight weight |
| `blink` | Blink | Eyes closed (handled by CSS, transforms empty) |
| `talk_open` | Talk (Open) | Mouth open, slight head tilt |
| `talk_closed` | Talk (Closed) | Mouth neutral, slight head forward |
| `surprised` | Surprised | Head back, eyes wide (scaleY > 1 on eyes-open) |
| `point_left` | Point Left | Arm extended left (if arm parts exist) |
| `point_right` | Point Right | Arm extended right (if arm parts exist) |

Each pose's `transforms` maps `part_id → {rotation?, x?, y?, scaleX?, scaleY?}`.
Only include parts that actually change. Idle transforms should all be 0/1 (rest pose).

## Step 5 — Construct the asset_spec

```json
{
  "id": "<slug derived from character name>",
  "name": "<character display name>",
  "description": "<one sentence describing the character>",
  "style": "<visual style from proposal>",
  "colors": {
    "body": "#hex",
    "skin": "#hex",
    "<other key colors>": "#hex"
  }
}
```

## Step 6 — Call SvgCharacterWriter

```python
result = svg_character_writer.execute({
    "svg_content":  "<the SVG you generated>",
    "rig_manifest": { ... },
    "pose_library": { ... },
    "asset_spec":   { ... },
    "output_dir": "projects/<project_name>/assets/characters/<character_id>/",
})
```

If `result.success` is False, read `result.error`. It will list specific `<g>` IDs
that are missing from the SVG. Fix the SVG (add the missing groups) and retry.
Maximum 3 attempts before escalating to the user.

If `result.success` is True:
- `result.data["rig_plan"]` is the schema-valid OpenMontage `rig_plan` artifact
- `result.data["pose_library"]` is the schema-valid OpenMontage `pose_library` artifact
- `result.data["svg_path"]` is the path to `character.svg`
- `result.data["preview_path"]` is the path to `preview.html`

## Step 7 — Preview prompt

Ask the user:

> "Character generated. Want to preview it before continuing? (yes / no)"

**If yes:**
1. Try to open `result.data["preview_path"]` using Playwright or Chrome DevTools MCP.
   Navigate to the file URL, wait 2s for GSAP to initialize, take a screenshot.
   Describe what you see: character name, colors, visible pose buttons.
2. If no MCP browser is available, output:
   `Open in your browser: file://<preview_path>`
3. Ask: "Does this character look right? (approve / regenerate / adjust description)"
   - **approve** → proceed to Step 8
   - **regenerate** → repeat from Step 2 with the same prompt (counts as one revision)
   - **adjust** → user provides updated description, repeat from Step 2

**If no:** proceed directly to Step 8.

## Step 8 — Save to library prompt

Ask the user:

> "Save this character to your library for reuse in future videos? (yes / no)"

**If yes:**
```python
character_library.execute({
    "action": "save",
    "asset_spec":   asset_spec,
    "svg_content":  svg_content,
    "rig_manifest": rig_manifest,
    "pose_library": pose_library,
    "source_dir":   result.data["output_dir"],
})
```

**If no:** continue.

## Step 9 — Write stage artifacts

Write three JSON artifacts to `projects/<project_name>/artifacts/`:

**`character_design.json`** — construct from asset_spec + script/proposal context:
```json
{
  "version": "1.0",
  "style": {
    "visual_style": "<from proposal>",
    "palette": ["<hex colors from asset_spec.colors>"],
    "line_style": "outline"
  },
  "characters": [{
    "id": "<asset_spec.id>",
    "display_name": "<asset_spec.name>",
    "role": "main",
    "body_type": "<humanoid / animal / robot / abstract>",
    "style": "<asset_spec.style>",
    "required_emotions": ["neutral", "happy", "surprised", "focused"],
    "required_actions": ["idle", "talk", "point", "react"]
  }]
}
```

**`rig_plan.json`** — write `result.data["rig_plan"]` directly.

**`pose_library.json`** — write `result.data["pose_library"]` directly.

Validate each against its schema before checkpointing:
```python
validate_artifact(character_design, "character_design")
validate_artifact(rig_plan, "rig_plan")
validate_artifact(pose_library, "pose_library")
```

## Step 10 — Checkpoint

Stage complete. Present to user:
- Character name, style, and saved path
- Pose library summary (list of pose IDs)
- Whether character was saved to library
- Preview path (if generated)

Wait for human approval before advancing to `scene_plan`.
````

- [ ] **Step 3: Commit**

```bash
git add skills/pipelines/svg-character/character-generation-director.md
git commit -m "feat(skills): add character-generation-director for svg-character pipeline"
```

---

## Task 6: Thin director skills + gitignore + library

**Files:**
- Create: 8 director skill files in `skills/pipelines/svg-character/`
- Modify: `.gitignore`
- Create: `character_library/.gitkeep`

- [ ] **Step 1: Write all thin director skills**

Create `skills/pipelines/svg-character/research-director.md`:
```markdown
# Research Director (svg-character)

Read `skills/pipelines/character-animation/research-director.md` and follow it exactly.
No changes for this pipeline.
```

Create `skills/pipelines/svg-character/proposal-director.md`:
```markdown
# Proposal Director (svg-character)

Read `skills/pipelines/character-animation/proposal-director.md` and follow it, with
one addition before presenting concepts:

**Library check (mandatory):**
Call `CharacterLibrary` with `action=list`. If any saved character matches the brief,
include it as an option alongside new concept directions:

> "EXISTING CHARACTER: [Name] — [style/description]. Would you like to reuse this,
>  use it as a reference, or start fresh?"

If the user selects reuse, the `character_generation` stage will load rather than
generate. Record this decision in `decision_log`.
```

Create `skills/pipelines/svg-character/script-director.md`:
```markdown
# Script Director (svg-character)

Read `skills/pipelines/character-animation/script-director.md` and follow it exactly.
No changes for this pipeline.
```

Create `skills/pipelines/svg-character/scene-director.md`:
```markdown
# Scene Director (svg-character)

Read `skills/pipelines/character-animation/scene-director.md` and follow it exactly.
```

Create `skills/pipelines/svg-character/asset-director.md`:
```markdown
# Asset Director (svg-character)

Read `skills/pipelines/character-animation/asset-director.md` and follow it, with
one important change:

**Character assets are already built.** The `character_generation` stage has already
written `character.svg`, `rig_manifest.json`, and `pose_library.json` to
`projects/<name>/assets/characters/<id>/`. Do not regenerate the character.

Your job in this stage is backgrounds, props, TTS audio, and music only:
- Use `image_selector` for scene backgrounds and props
- Use `tts_selector` for narration (if script has VO)
- Use `music_gen` or `music_library/` for background music
- Call `character_rig_renderer` with `svg_path` pointing to the already-written
  `character.svg` to build the HyperFrames composition package

Pass `svg_path: projects/<name>/assets/characters/<id>/character.svg` to
`character_rig_renderer`. Do not omit this — without it the renderer uses placeholders.
```

Create `skills/pipelines/svg-character/edit-director.md`:
```markdown
# Edit Director (svg-character)

Read `skills/pipelines/character-animation/edit-director.md` and follow it exactly.
```

Create `skills/pipelines/svg-character/compose-director.md`:
```markdown
# Compose Director (svg-character)

Read `skills/pipelines/character-animation/compose-director.md` and follow it exactly.
```

Create `skills/pipelines/svg-character/publish-director.md`:
```markdown
# Publish Director (svg-character)

Read `skills/pipelines/character-animation/publish-director.md` and follow it exactly.
```

- [ ] **Step 2: Add character_library to .gitignore**

Open `.gitignore` and add this block after the `music_library/` entry (or at the end):
```
# Character library — generated assets, not committed (keep .gitkeep)
character_library/*
!character_library/.gitkeep
```

- [ ] **Step 3: Create the library seed file**

```bash
mkdir -p character_library
touch character_library/.gitkeep
```

- [ ] **Step 4: Verify registry discovers the new tools**

```bash
python -c "
from tools.tool_registry import registry
registry.discover()
tools = registry.list_all()
assert 'svg_character_writer' in tools, f'svg_character_writer not found in {tools}'
assert 'character_library' in tools, f'character_library not found in {tools}'
print('Registry check passed:', [t for t in tools if 'character' in t or 'svg' in t])
"
```

Expected output includes `svg_character_writer` and `character_library`.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all existing tests still pass; new tests pass.

- [ ] **Step 6: Commit everything**

```bash
git add skills/pipelines/svg-character/ \
        character_library/.gitkeep \
        .gitignore
git commit -m "feat(skills,config): add svg-character director skills, character_library dir, and gitignore"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by task |
|-----------------|-----------------|
| `SvgCharacterWriter` — validates SVG/rig consistency | Task 1 |
| `SvgCharacterWriter` — writes 5 files including preview.html | Task 1 |
| `SvgCharacterWriter` — returns `rig_plan` and `pose_library` in OpenMontage format | Task 1 |
| `CharacterLibrary` — list/load/save operations | Task 2 |
| `CharacterLibrary` — `character_library/` directory | Task 6 |
| `CharacterLibrary` — copies `preview.html` via `source_dir` | Task 2 |
| `CharacterRigRenderer` — `svg_content` / `svg_path` inputs | Task 3 |
| `CharacterRigRenderer` — backward compatible fallback | Task 3 |
| `svg-character` pipeline YAML with `character_generation` stage | Task 4 |
| `character-generation-director` skill with full generation workflow | Task 5 |
| Library check at proposal stage | Task 6 (proposal-director.md) |
| Preview prompt (Playwright MCP → HTML fallback) | Task 5 (skill step 7) |
| Save to library prompt | Task 5 (skill step 8) |
| 8 thin director skills | Task 6 |
| `.gitignore` entry | Task 6 |

**Type consistency check:** `_to_rig_plan` takes `(asset_spec, rig_manifest, pose_library)` — tests call it with 3 args. ✓ `_to_pose_library` takes `(asset_spec, pose_library)` — tests call with 2 args. ✓ `CharacterLibrary._root()` uses `inputs["library_path"]` — same key used in all test calls. ✓

**No placeholders:** All code blocks are complete. All commands include expected output. ✓
