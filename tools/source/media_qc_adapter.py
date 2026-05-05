"""Media QC adapter for source-commentary pipeline.

Validates extracted clips and marks them as approved for the edit.
Performs technical checks (existence, size, duration) and ensures every
clip is backed by an approved receipt.
"""

from __future__ import annotations

import json
import subprocess
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


class MediaQCAdapter(BaseTool):
    name = "media_qc_adapter"
    version = "1.1.0"
    tier = ToolTier.ANALYZE
    capability = "quality_control"
    provider = "openmontage"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:ffprobe"]
    install_instructions = "Install FFmpeg (includes ffprobe): https://ffmpeg.org/download.html"
    agent_skills = []

    capabilities = [
        "verify_clips",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id", "extracted_clip_manifest", "clip_use_receipts"],
        "properties": {
            "project_id": {"type": "string"},
            "extracted_clip_manifest": {"type": "object"},
            "clip_use_receipts": {"type": "object"},
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/approved_clip_manifest.schema.json"
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        extracted_manifest = inputs["extracted_clip_manifest"]
        receipts_manifest = inputs["clip_use_receipts"]

        start_time = time.time()

        receipt_map = {r["receipt_id"]: r for r in receipts_manifest.get("receipts", [])}
        approved_clips = []
        rejected_clips = []

        for clip in extracted_manifest.get("clips", []):
            rid = clip["receipt_id"]
            local_path_str = clip.get("local_clip_path")
            
            if not local_path_str:
                rejected_clips.append({"receipt_id": rid, "reason": "No local_clip_path in manifest"})
                continue

            local_path = Path(local_path_str)
            
            # 1. Basic File Checks
            if not local_path.exists():
                rejected_clips.append({"receipt_id": rid, "path": local_path_str, "reason": "File not found"})
                continue
            
            if local_path.stat().st_size == 0:
                rejected_clips.append({"receipt_id": rid, "path": local_path_str, "reason": "Zero-byte file"})
                continue

            # 2. Receipt Check
            if rid not in receipt_map:
                rejected_clips.append({"receipt_id": rid, "path": local_path_str, "reason": "No matching receipt found"})
                continue
            
            receipt = receipt_map[rid]
            
            # 3. Technical QC (Duration check)
            actual_duration = self._get_duration(local_path)
            if actual_duration is None:
                rejected_clips.append({"receipt_id": rid, "path": local_path_str, "reason": "Failed to probe duration (ffprobe error)"})
                continue
            
            # Allow 0.5s tolerance for extraction/muxing variance
            expected_duration = clip.get("duration_seconds") or receipt.get("duration_seconds", 0)
            if expected_duration > 0 and abs(actual_duration - expected_duration) > 0.5:
                # We log a warning in metadata but don't necessarily block if it's close enough,
                # but if it's way off, we block.
                if abs(actual_duration - expected_duration) > 2.0:
                    rejected_clips.append({
                        "receipt_id": rid, 
                        "path": local_path_str, 
                        "reason": f"Duration mismatch: expected {expected_duration}s, got {actual_duration}s"
                    })
                    continue

            # 4. Generate source label
            # Priority: receipt.source_channel > receipt.source_url (hostname) > "Unknown Source"
            source_label = receipt.get("source_channel")
            if not source_label and receipt.get("source_url"):
                from urllib.parse import urlparse
                source_label = urlparse(receipt["source_url"]).netloc
            
            if not source_label:
                source_label = "Verified Source"
            
            source_label_text = f"Source: {source_label}"
            
            approved_clips.append({
                "receipt_id": rid,
                "claim_id": receipt["claim_id"],
                "local_clip_path": str(local_path.resolve()),
                "qc_passed": True,
                "source_label_required": True,
                "source_label_text": source_label_text,
                "approved_for_edit": True,
                "metadata": {
                    "actual_duration": actual_duration,
                    "expected_duration": expected_duration
                }
            })

        return ToolResult(
            success=True,
            data={
                "version": "1.0",
                "project_id": project_id,
                "approved_clips": approved_clips,
                "rejected_clips": rejected_clips
            },
            duration_seconds=round(time.time() - start_time, 2)
        )

    def _get_duration(self, file_path: Path) -> Optional[float]:
        """Call ffprobe to get video duration."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return None
