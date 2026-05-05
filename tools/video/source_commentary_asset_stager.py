"""Asset stager for source-commentary pipeline.

Physically copies assets from the artifact bus into the Remotion public staging area.
Verifies integrity via SHA256 checksums and generates a staging receipt.
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


class SourceCommentaryAssetStager(BaseTool):
    name = "source_commentary_asset_stager"
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
        "stage_assets",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id", "asset_manifest"],
        "properties": {
            "project_id": {"type": "string"},
            "asset_manifest": {"type": "object"},
            "remotion_public_root": {
                "type": "string",
                "default": "remotion-composer/public"
            }
        },
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        asset_manifest = inputs["asset_manifest"]
        public_root = Path(inputs.get("remotion_public_root", "remotion-composer/public")).resolve()
        include_timestamp = inputs.get("include_timestamp", False)

        start_time = time.time()
        staged_assets = []
        
        assets = asset_manifest.get("assets", [])
        if not assets:
            return ToolResult(success=False, error="Asset manifest contains no assets to stage.")

        for asset in assets:
            asset_id = asset.get("id")
            asset_type = asset.get("type")
            local_path_str = asset.get("local_path")
            staged_public_path_str = asset.get("staged_public_path")

            # 1. Basic field validation
            if not all([asset_id, asset_type, local_path_str, staged_public_path_str]):
                return ToolResult(
                    success=False, 
                    error=f"Asset {asset_id} missing required fields (id, type, local_path, staged_public_path)"
                )

            # 2. Path traversal protection
            if os.path.isabs(staged_public_path_str):
                return ToolResult(success=False, error=f"staged_public_path must be relative: {staged_public_path_str}")
            
            # Reject .. or other traversal attempts
            if ".." in staged_public_path_str.split(os.sep):
                return ToolResult(success=False, error=f"Path traversal detected in staged_public_path: {staged_public_path_str}")

            local_path = Path(local_path_str)
            if not local_path.exists():
                return ToolResult(success=False, error=f"Source file not found: {local_path}")

            # 3. Secure destination calculation
            try:
                dest_path = (public_root / staged_public_path_str).resolve()
            except Exception as e:
                return ToolResult(success=False, error=f"Invalid staged_public_path {staged_public_path_str}: {e}")

            if not str(dest_path).startswith(str(public_root)):
                return ToolResult(
                    success=False, 
                    error=f"Destination path escapes public root: {dest_path}"
                )

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # 4. Physical copy with integrity check
            try:
                shutil.copy2(local_path, dest_path)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to copy {local_path} to {dest_path}: {e}")

            if not dest_path.exists():
                return ToolResult(success=False, error=f"Staged file missing after copy: {dest_path}")

            source_checksum = self._calculate_sha256(local_path)
            staged_checksum = self._calculate_sha256(dest_path)

            if source_checksum != staged_checksum:
                return ToolResult(
                    success=False, 
                    error=f"Checksum mismatch for asset {asset_id}.\nSource: {source_checksum}\nStaged: {staged_checksum}"
                )

            staged_assets.append({
                "asset_id": asset_id,
                "type": asset_type,
                "local_path": str(local_path.resolve()),
                "staged_public_path": staged_public_path_str,
                "staged_filesystem_path": str(dest_path.resolve()),
                "source_checksum_sha256": source_checksum,
                "staged_checksum_sha256": staged_checksum,
                "staged": True
            })

        receipt = {
            "version": "1.0",
            "project_id": project_id,
            "staged_assets": staged_assets,
            "staging_root": str(public_root),
            "success": True
        }
        
        if include_timestamp:
            receipt["timestamp"] = time.time()

        return ToolResult(
            success=True,
            data=receipt,
            duration_seconds=round(time.time() - start_time, 2)
        )

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
