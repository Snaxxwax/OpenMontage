"""Clip acquisition adapter for the source-commentary pipeline.

Coordinates VideoDownloader and VideoTrimmer to acquire approved clips.
Enforces that only receipts with status=approved are processed.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
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
from tools.analysis.video_downloader import VideoDownloader
from tools.video.video_trimmer import VideoTrimmer


class ClipAcquisitionAdapter(BaseTool):
    name = "clip_acquisition_adapter"
    version = "1.0.0"
    tier = ToolTier.SOURCE
    capability = "media_acquisition"
    provider = "openmontage"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:ffmpeg"]
    install_instructions = "Requires ffmpeg and yt-dlp"
    agent_skills = ["ffmpeg", "video-download"]

    capabilities = [
        "acquire_clips",
    ]

    best_for = [
        "extracting approved evidence segments",
        "enforcing edit-gate policies on media",
    ]

    not_good_for = [
        "arbitrary video downloading without receipts",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id", "output_dir"],
        "properties": {
            "project_id": {"type": "string", "description": "Project ID"},
            "clip_use_receipts": {
                "type": "object",
                "description": "Clip use receipts manifest"
            },
            "clip_use_receipts_path": {
                "type": "string",
                "description": "Path to clip_use_receipts.json"
            },
            "output_dir": {
                "type": "string",
                "description": "Directory to store extracted clips"
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "Validate receipts but do not perform IO"
            },
            "keep_temp": {
                "type": "boolean",
                "default": False,
                "description": "If true, keep temporary full-video downloads"
            },
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/extracted_clip_manifest.schema.json"
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=1024, vram_mb=0, disk_mb=5000,
        network_required=True,
    )
    idempotency_key_fields = ["project_id", "dry_run"]
    side_effects = ["downloads full sources", "extracts clips to disk"]
    user_visible_verification = [
        "Verify extracted clips match receipt timestamps",
        "Check clip SHA256 integrity",
    ]

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _is_safe_id(self, identifier: str) -> bool:
        """Check if an ID is alphanumeric/dash/underscore only (no path traversal)."""
        import re
        return bool(re.match(r"^[a-zA-Z0-9_\-]+$", identifier))

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        output_dir = Path(inputs["output_dir"]).resolve()
        dry_run = inputs.get("dry_run", True)
        keep_temp = inputs.get("keep_temp", False)

        start_time = time.time()

        # Load Receipts
        receipts_manifest = inputs.get("clip_use_receipts")
        if not receipts_manifest and inputs.get("clip_use_receipts_path"):
            try:
                with open(inputs["clip_use_receipts_path"], "r") as f:
                    receipts_manifest = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load receipts: {e}")

        if not receipts_manifest:
            return ToolResult(success=False, error="Missing clip_use_receipts or clip_use_receipts_path")

        receipts = receipts_manifest.get("receipts", [])
        
        # Policy Enforcement: Check for non-approved receipts
        invalid_receipts = []
        for r in receipts:
            if r.get("status") != "approved" or not r.get("approved_for_edit"):
                invalid_receipts.append(r.get("receipt_id", "unknown"))
        
        if invalid_receipts:
            return ToolResult(
                success=False, 
                error=f"Cannot acquire clips. Offending receipt_ids (not approved for edit): {invalid_receipts}"
            )

        # Validation of required fields and ID safety
        required_fields = ["receipt_id", "claim_id", "source_id", "source_url", "in_seconds", "out_seconds", "duration_seconds"]
        for r in receipts:
            for field in required_fields:
                if field not in r:
                    return ToolResult(success=False, error=f"Receipt {r.get('receipt_id', 'unknown')} missing required field: {field}")
            
            # Sanitize IDs
            if not self._is_safe_id(r["receipt_id"]):
                return ToolResult(success=False, error=f"Unsafe receipt_id: {r['receipt_id']}")
            if not self._is_safe_id(r["source_id"]):
                return ToolResult(success=False, error=f"Unsafe source_id: {r['source_id']}")

        if dry_run:
            return ToolResult(
                success=True,
                data={
                    "version": "1.0",
                    "project_id": project_id,
                    "clips": []
                },
                error=f"Dry run complete. Validated {len(receipts)} intended acquisitions.",
                duration_seconds=round(time.time() - start_time, 2)
            )

        # Actual Acquisition
        clips_dir = (output_dir / "clips").resolve()
        clips_dir.mkdir(parents=True, exist_ok=True)
        temp_root = (output_dir / ".temp_acquisition").resolve()
        temp_root.mkdir(parents=True, exist_ok=True)

        # Group by source_id AND source_url. Fail if conflicting.
        sources = {}
        source_url_map = {} # source_id -> url
        for r in receipts:
            sid = r["source_id"]
            url = r["source_url"]
            
            if sid in source_url_map and source_url_map[sid] != url:
                return ToolResult(success=False, error=f"Conflicting URLs for source_id {sid}: {source_url_map[sid]} vs {url}")
            
            source_url_map[sid] = url
            
            if sid not in sources:
                sources[sid] = {"url": url, "receipts": []}
            sources[sid]["receipts"].append(r)

        extracted_clips = []
        downloader = VideoDownloader()
        trimmer = VideoTrimmer()

        try:
            for sid, source_info in sources.items():
                source_temp_dir = (temp_root / sid).resolve()
                if not str(source_temp_dir).startswith(str(temp_root)):
                    return ToolResult(success=False, error=f"Path safety violation: {source_temp_dir} is outside {temp_root}")
                
                source_temp_dir.mkdir(parents=True, exist_ok=True)

                # Download full source
                dl_result = downloader.execute({
                    "url": source_info["url"],
                    "output_dir": str(source_temp_dir),
                    "format": "video",
                    "max_resolution": "720p"
                })

                if not dl_result.success:
                    return ToolResult(success=False, error=f"Failed to download source {sid}: {dl_result.error}")

                video_path_str = dl_result.data.get("video_path")
                if not video_path_str:
                    return ToolResult(success=False, error=f"Download successful but video_path missing for source {sid}")
                
                video_path = Path(video_path_str).resolve()
                if not video_path.exists():
                    return ToolResult(success=False, error=f"Video path does not exist: {video_path}")
                
                # Path safety check for downloaded file
                if not str(video_path).startswith(str(source_temp_dir)):
                     return ToolResult(success=False, error=f"Path safety violation: {video_path} is outside {source_temp_dir}")

                # Extract segments
                for r in source_info["receipts"]:
                    receipt_id = r["receipt_id"]
                    clip_path = (clips_dir / f"{receipt_id}.mp4").resolve()
                    
                    # Path safety check
                    if not str(clip_path).startswith(str(clips_dir)):
                         return ToolResult(success=False, error=f"Path safety violation: {clip_path} is outside {clips_dir}")

                    trim_result = trimmer.execute({
                        "operation": "cut",
                        "input_path": str(video_path),
                        "output_path": str(clip_path),
                        "start_seconds": r["in_seconds"],
                        "end_seconds": r["out_seconds"],
                        "codec": "libx264"
                    })

                    if not trim_result.success:
                        return ToolResult(success=False, error=f"Failed to trim clip for receipt {receipt_id}: {trim_result.error}")

                    checksum = self._calculate_sha256(clip_path)
                    
                    extracted_clips.append({
                        "receipt_id": receipt_id,
                        "local_clip_path": str(clip_path),
                        "source_id": sid,
                        "in_seconds": r["in_seconds"],
                        "out_seconds": r["out_seconds"],
                        "duration_seconds": r["duration_seconds"],
                        "checksum_sha256": checksum
                    })

                # Cleanup source temp unless keep_temp
                if not keep_temp:
                    shutil.rmtree(source_temp_dir)

        finally:
            # Cleanup temp_root if empty and not keep_temp
            if not keep_temp and temp_root.exists():
                try:
                    if not any(temp_root.iterdir()):
                        temp_root.rmdir()
                except OSError:
                    pass

        return ToolResult(
            success=True,
            data={
                "version": "1.0",
                "project_id": project_id,
                "clips": extracted_clips
            },
            duration_seconds=round(time.time() - start_time, 2)
        )
