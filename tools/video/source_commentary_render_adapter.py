"""Adapter to convert source_commentary_edit_plan into OpenMontage render contract.

Produces edit_decisions and asset_manifest artifacts compatible with video_compose.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolStatus,
    ToolTier,
    ToolRuntime,
)


class SourceCommentaryRenderAdapter(BaseTool):
    name = "source_commentary_render_adapter"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "openmontage"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = ""
    agent_skills = ["video-editing"]

    capabilities = [
        "adapt_edit_plan",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id", "source_commentary_edit_plan"],
        "properties": {
            "project_id": {"type": "string"},
            "source_commentary_edit_plan": {
                "oneOf": [
                    {"type": "object"},
                    {"type": "string", "description": "Path to the edit plan JSON file"}
                ]
            },
            "render_runtime": {
                "type": "string",
                "enum": ["remotion", "hyperframes", "ffmpeg"],
                "default": "remotion"
            },
            "renderer_family": {
                "type": "string",
                "default": "explainer-data"
            }
        },
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        plan_input = inputs["source_commentary_edit_plan"]
        render_runtime = inputs.get("render_runtime", "remotion")
        renderer_family = inputs.get("renderer_family", "explainer-data")

        if isinstance(plan_input, str):
            plan_path = Path(plan_input)
            if not plan_path.exists():
                return ToolResult(success=False, error=f"Plan file not found: {plan_path}")
            with open(plan_path, "r", encoding="utf-8") as f:
                edit_plan = json.load(f)
        else:
            edit_plan = plan_input

        start_time = time.time()

        cuts = []
        overlays = []
        assets = []
        
        current_time = 0.0
        narration_segments = []
        
        # Deterministic staging dir (relative to remotion-composer/public/)
        staging_root = f"source-commentary/{project_id}"

        timeline = edit_plan.get("timeline", [])
        for i, item in enumerate(timeline):
            clip_type = item.get("clip_type")
            
            # Duration is required for the timeline calculation
            duration = item.get("duration_seconds", 0.0)
            
            if clip_type == "source_clip":
                local_path = item.get("local_clip_path")
                if not local_path:
                    continue
                
                # Determine staging path
                filename = Path(local_path).name
                staged_path = f"{staging_root}/{filename}"
                
                asset_id = f"source-clip-{i}"
                assets.append({
                    "id": asset_id,
                    "type": "video",
                    "local_path": str(Path(local_path).resolve()),
                    "staged_public_path": staged_path,
                    "source_tool": "source_commentary_pipeline",
                    "scene_id": item.get("claim_id", f"scene-{i}")
                })
                
                cuts.append({
                    "id": f"cut-{i}",
                    "source": staged_path,
                    "in_seconds": current_time,
                    "out_seconds": current_time + duration,
                    "layer": "primary"
                })
                
                # Map source label to SectionTitle overlay
                label_plan = item.get("source_label_plan", {})
                if label_plan.get("text"):
                    overlays.append({
                        "type": "section_title",
                        "text": label_plan["text"],
                        "in_seconds": current_time,
                        "out_seconds": current_time + duration,
                        "position": self._map_position(label_plan.get("position", "bottom-left"))
                    })
                
                current_time += duration
            
            elif clip_type == "narration":
                # Support external narration audio paths
                audio_path = item.get("metadata", {}).get("audio_path")
                if audio_path:
                    # Determine staging path
                    filename = Path(audio_path).name
                    staged_audio_path = f"{staging_root}/{filename}"

                    asset_id = f"narration-clip-{i}"
                    assets.append({
                        "id": asset_id,
                        "type": "audio",
                        "local_path": str(Path(audio_path).resolve()),
                        "staged_public_path": staged_audio_path,
                        "role": "narration",
                        "claim_id": item.get("claim_id")
                    })
                    narration_segments.append({
                        "asset_id": asset_id,
                        "path": staged_audio_path,
                        "start_seconds": current_time,
                        "end_seconds": current_time + duration
                    })
                
                current_time += duration
            
            else:
                # Handle other types as placeholders if they have duration
                current_time += duration

        # Map narration to the single-src format Remotion Explainer expects.
        # If there are multiple segments, this adapter expects them to be 
        # pre-concatenated or it will just pick the first one as a debug fallback.
        narration_src = None
        if narration_segments:
            narration_src = narration_segments[0]["path"]

        edit_decisions = {
            "version": "1.0",
            "render_runtime": render_runtime,
            "renderer_family": renderer_family,
            "cuts": cuts,
            "overlays": overlays,
            "audio": {
                "narration": {
                    "src": narration_src,
                    "segments": narration_segments
                }
            },
            "metadata": {
                "project_id": project_id,
                "generated_by": "source_commentary_render_adapter",
                "staging_dir": staging_root
            }
        }
        
        asset_manifest = {
            "version": "1.0",
            "assets": assets,
            "metadata": {
                "project_id": project_id
            }
        }

        return ToolResult(
            success=True,
            data={
                "edit_decisions": edit_decisions,
                "asset_manifest": asset_manifest
            },
            duration_seconds=round(time.time() - start_time, 2)
        )

    def _map_position(self, pos: str) -> str:
        """Map edit-plan positions to Remotion SectionTitle supported positions."""
        mapping = {
            "top-left": "top-left",
            "bottom-left": "bottom-left",
            "center": "center",
            "top-right": "top-left", # Fallback for SectionTitle which lacks top-right
            "bottom-right": "bottom-left" # Fallback for SectionTitle which lacks bottom-right
        }
        return mapping.get(pos, "top-left")
