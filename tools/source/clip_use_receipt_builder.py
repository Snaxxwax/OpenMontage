"""Clip use receipt builder for source commentary pipeline.

Maps evidence candidates to clip use receipts, gatekeeping acquisition and edit.
Does not download media. Ensures source metadata is correctly preserved.
"""

from __future__ import annotations

import json
import time
import uuid
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


class ClipUseReceiptBuilder(BaseTool):
    name = "clip_use_receipt_builder"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "evidence_matching"
    provider = "openmontage"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = ""
    agent_skills = []

    capabilities = [
        "build_receipts",
    ]

    best_for = [
        "locking evidence choices before clip acquisition",
        "applying approval policies to source clips",
    ]

    not_good_for = [
        "downloading media (prohibited)",
        "extracting actual clips",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id"],
        "properties": {
            "project_id": {"type": "string", "description": "Project ID for the receipts"},
            "evidence_candidate_manifest": {
                "type": "object",
                "description": "Evidence candidate manifest object"
            },
            "evidence_candidate_manifest_path": {
                "type": "string",
                "description": "Path to evidence_candidate_manifest.json"
            },
            "source_candidate_manifest": {
                "type": "object",
                "description": "Source candidate manifest object"
            },
            "source_candidate_manifest_path": {
                "type": "string",
                "description": "Path to source_candidate_manifest.json"
            },
            "auto_approve": {
                "type": "boolean",
                "default": False,
                "description": "If true, mark receipts as approved immediately"
            },
            "max_duration_seconds": {
                "type": "number",
                "default": 12.0,
                "description": "Reject or flag candidates longer than this duration"
            },
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/clip_use_receipts.schema.json"
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=10,
        network_required=False,
    )
    idempotency_key_fields = ["project_id", "auto_approve", "max_duration_seconds"]
    side_effects = []
    user_visible_verification = [
        "Ensure all receipts correctly reference existing source metadata",
        "Verify audio_use matches clip_role policy",
    ]

    def _map_audio_use(self, clip_role: str) -> str:
        """Map clip_role to original_audio_use enum."""
        if clip_role == "quote_support":
            return "quote_audio"
        if clip_role == "primary_evidence":
            return "ducked"
        return "muted"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        auto_approve = inputs.get("auto_approve", False)
        max_duration = inputs.get("max_duration_seconds", 12.0)

        start_time = time.time()
        warnings = []

        # Load Evidence Candidate Manifest
        evidence_manifest = inputs.get("evidence_candidate_manifest")
        if not evidence_manifest and inputs.get("evidence_candidate_manifest_path"):
            try:
                with open(inputs["evidence_candidate_manifest_path"], "r") as f:
                    evidence_manifest = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load evidence manifest: {e}")

        # Load Source Candidate Manifest
        source_manifest = inputs.get("source_candidate_manifest")
        if not source_manifest and inputs.get("source_candidate_manifest_path"):
            try:
                with open(inputs["source_candidate_manifest_path"], "r") as f:
                    source_manifest = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load source manifest: {e}")

        if not evidence_manifest or not source_manifest:
            return ToolResult(success=False, error="Missing evidence_candidate_manifest or source_candidate_manifest")

        # Map sources for fast lookup
        source_map = {s["source_id"]: s for s in source_manifest.get("sources", [])}
        candidates = evidence_manifest.get("candidates", [])

        receipts = []
        for cand in candidates:
            source_id = cand["source_id"]
            if source_id not in source_map:
                return ToolResult(success=False, error=f"Candidate {cand['candidate_id']} references missing source {source_id}")

            source = source_map[source_id]
            duration = cand["duration_seconds"]
            
            status = "pending"
            approved_for_edit = False
            
            if duration > max_duration:
                status = "flagged"
                warnings.append(f"Candidate {cand['candidate_id']} exceeds max duration ({duration:.2f}s > {max_duration}s)")
            elif auto_approve:
                status = "approved"
                approved_for_edit = True

            # Deterministic receipt_id based on project and candidate
            receipt_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{project_id}:{cand['candidate_id']}"))
            receipt = {
                "version": "1.0",
                "project_id": project_id,
                "receipt_id": receipt_id,
                "claim_id": cand["claim_id"],
                "source_id": source_id,
                "source_url": source["source_url"],
                "source_title": source["source_title"],
                "source_channel": source["source_channel"],
                "clip_role": cand["clip_role"],
                "in_seconds": cand["in_seconds"],
                "out_seconds": cand["out_seconds"],
                "duration_seconds": duration,
                "rationale": cand["rationale"],
                "why_this_clip_is_needed": f"Matches claim {cand['claim_id']} with relevance {cand.get('relevance_score', 0):.2f}",
                "commentary_attached": True,
                "source_label_required": True,
                "decorative_broll": False,
                "original_audio_use": self._map_audio_use(cand["clip_role"]),
                "approved_for_edit": approved_for_edit,
                "status": status,
            }
            receipts.append(receipt)

        # Final receipts collection
        receipts_collection = {
            "version": "1.0",
            "project_id": project_id,
            "receipts": receipts
        }

        # Expose warnings via error field on success
        error_msg = None
        if warnings:
            error_msg = "Warnings:\n" + "\n".join(f"  • {w}" for w in warnings)

        return ToolResult(
            success=True,
            data=receipts_collection,
            error=error_msg,
            duration_seconds=round(time.time() - start_time, 2)
        )
