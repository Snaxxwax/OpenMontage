"""Transcript index builder for source commentary pipeline.

Extracts transcripts from YouTube sources listed in a source_candidate_manifest.
Does not download media. Supports fixture mode for deterministic testing.
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


class TranscriptIndexBuilder(BaseTool):
    name = "transcript_index_builder"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "transcript_indexing"
    provider = "youtube-transcript-api"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.HYBRID

    dependencies = ["python:youtube_transcript_api"]
    install_instructions = (
        "Install dependencies: pip install youtube-transcript-api"
    )
    agent_skills = []

    capabilities = [
        "index_transcripts",
    ]

    best_for = [
        "building a searchable transcript index from YouTube sources",
        "normalizing timestamps for commentary pipelines",
    ]

    not_good_for = [
        "downloading media (prohibited)",
        "non-YouTube platforms (unless provided via fixture)",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id"],
        "properties": {
            "project_id": {"type": "string", "description": "Project ID for the index"},
            "source_candidate_manifest": {
                "type": "object",
                "description": "The manifest object containing sources to index"
            },
            "source_candidate_manifest_path": {
                "type": "string",
                "description": "Path to the source_candidate_manifest.json file"
            },
            "transcript_fixture_path": {
                "type": "string",
                "description": "Optional path to a mock transcript index for testing"
            },
            "max_segments_per_source": {
                "type": "integer",
                "description": "Limit segments per source to keep index manageable"
            },
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/transcript_index.schema.json"
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=10,
        network_required=True,
    )
    idempotency_key_fields = ["project_id", "source_candidate_manifest_path"]
    side_effects = []
    user_visible_verification = [
        "Check that all segments have valid source_ids from the manifest",
        "Verify timestamps are numeric and represent seconds",
    ]

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        import re
        patterns = [
            r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _fetch_youtube_transcript(self, source_id: str, url: str, max_segments: Optional[int]) -> tuple[list[dict], Optional[str]]:
        """Fetch transcript segments for a single YouTube video."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return [], f"Could not extract video ID from URL: {url}"

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Using the instance-based API (v1.0+)
            ytt = YouTubeTranscriptApi()
            transcript_result = ytt.fetch(video_id, languages=['en', 'en-US'])
            
            segments = []
            for i, snippet in enumerate(transcript_result.snippets):
                if max_segments and i >= max_segments:
                    break
                
                start = snippet.start
                duration = snippet.duration
                segments.append({
                    "source_id": source_id,
                    "segment_id": f"{source_id}-seg-{i:04d}",
                    "start_seconds": round(float(start), 3),
                    "end_seconds": round(float(start + duration), 3),
                    "text": snippet.text.replace('\n', ' ').strip()
                })
            return segments, None
        except Exception as e:
            return [], f"Failed to fetch transcript for {video_id}: {type(e).__name__}: {str(e)}"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        manifest = inputs.get("source_candidate_manifest")
        manifest_path = inputs.get("source_candidate_manifest_path")
        fixture_path = inputs.get("transcript_fixture_path")
        max_segments = inputs.get("max_segments_per_source")

        start_time = time.time()
        warnings = []

        # Mode 1: Fixture Mode
        if fixture_path:
            p = Path(fixture_path)
            if p.exists():
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                    
                    # Ensure project_id consistency
                    data["project_id"] = project_id
                    
                    return ToolResult(
                        success=True,
                        data=data,
                        duration_seconds=round(time.time() - start_time, 2),
                    )
                except Exception as e:
                    return ToolResult(success=False, error=f"Failed to load fixture: {e}")
            else:
                return ToolResult(success=False, error=f"Fixture path not found: {fixture_path}")

        # Load manifest if path provided
        if not manifest and manifest_path:
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load manifest from {manifest_path}: {e}")

        if not manifest:
            return ToolResult(success=False, error="No source_candidate_manifest or path provided")

        # Mode 2: Live Indexing
        all_segments = []
        sources = manifest.get("sources", [])

        if not sources:
            return ToolResult(
                success=True,
                data={
                    "version": "1.0",
                    "project_id": project_id,
                    "source_segments": []
                },
                duration_seconds=round(time.time() - start_time, 2)
            )

        for source in sources:
            source_id = source.get("source_id")
            source_url = source.get("source_url")
            platform = source.get("platform")

            if platform != "youtube":
                warnings.append(f"Skipping source {source_id}: non-YouTube platform {platform} not supported for live indexing")
                continue

            segments, error = self._fetch_youtube_transcript(source_id, source_url, max_segments)
            if error:
                warnings.append(f"Source {source_id}: {error}")
            else:
                all_segments.extend(segments)

        # Final index construction
        index = {
            "version": "1.0",
            "project_id": project_id,
            "source_segments": all_segments,
        }

        # If we failed to find any segments and have warnings, but we have sources, it's a failure
        if not all_segments and warnings and sources:
             return ToolResult(
                success=False,
                error=f"Indexing failed: {warnings[0]}",
                data={"warnings": warnings},
                duration_seconds=round(time.time() - start_time, 2),
            )

        return ToolResult(
            success=True,
            data=index,
            duration_seconds=round(time.time() - start_time, 2),
        )
