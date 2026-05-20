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
