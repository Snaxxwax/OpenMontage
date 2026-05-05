"""Edit plan builder for the source-commentary pipeline.

Consumes approved clips and the claim map to produce a structural edit plan.
Aligns source evidence with narration claims.
"""

from __future__ import annotations

import json
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


class SourceCommentaryEditPlanBuilder(BaseTool):
    name = "source_commentary_edit_plan_builder"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "edit_planning"
    provider = "openmontage"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = ""
    agent_skills = []

    capabilities = [
        "build_edit_plan",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id", "approved_clip_manifest", "narration_claim_map"],
        "properties": {
            "project_id": {"type": "string"},
            "approved_clip_manifest": {"type": "object"},
            "narration_claim_map": {"type": "object"},
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/source_commentary_edit_plan.schema.json"
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        approved_manifest = inputs["approved_clip_manifest"]
        claim_map = inputs["narration_claim_map"]

        start_time = time.time()

        # Map approved clips by claim_id for quick alignment
        clip_map = {}
        for clip in approved_manifest.get("approved_clips", []):
            cid = clip["claim_id"]
            if cid not in clip_map:
                clip_map[cid] = []
            clip_map[cid].append(clip)

        timeline = []
        
        # Build timeline by iterating through claims (logical order)
        for claim in claim_map.get("claims", []):
            cid = claim["claim_id"]
            
            # 1. Add Narration for the claim
            timeline.append({
                "clip_type": "narration",
                "claim_id": cid,
                "metadata": {"text": claim["narration_text"]}
            })
            
            # 2. Add matched Source Clips
            if cid in clip_map:
                for clip in clip_map[cid]:
                    timeline.append({
                        "clip_type": "source_clip",
                        "receipt_id": clip["receipt_id"],
                        "claim_id": cid,
                        "local_clip_path": clip["local_clip_path"],
                        "source_label_plan": {
                            "text": clip["source_label_text"],
                            "position": "bottom-right"
                        }
                    })

        return ToolResult(
            success=True,
            data={
                "version": "1.0",
                "project_id": project_id,
                "timeline": timeline
            },
            duration_seconds=round(time.time() - start_time, 2)
        )
