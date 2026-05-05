"""YouTube metadata adapter for source discovery.

Collects metadata (title, channel, duration, transcript status) for YouTube videos.
Prohibits media download. Supports fixture mode for deterministic testing.
"""

from __future__ import annotations

import json
import os
import re
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


class YouTubeMetadataAdapter(BaseTool):
    name = "youtube_metadata_adapter"
    version = "1.0.0"
    tier = ToolTier.SOURCE
    capability = "source_discovery"
    provider = "yt-dlp"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.HYBRID

    dependencies = ["python:yt_dlp", "python:youtube_transcript_api"]
    install_instructions = (
        "Install dependencies: pip install yt-dlp youtube-transcript-api"
    )
    agent_skills = ["video-download"]

    capabilities = [
        "discover_sources",
        "extract_metadata",
    ]

    best_for = [
        "finding YouTube sources for commentary",
        "collecting video metadata without download",
        "checking transcript availability",
    ]

    not_good_for = [
        "downloading media (prohibited)",
        "non-YouTube platforms",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id"],
        "properties": {
            "project_id": {"type": "string", "description": "Project ID for the manifest"},
            "query": {"type": "string", "description": "Search query for YouTube"},
            "source_urls": {
                "type": "array",
                "items": {"type": "string", "format": "uri"},
                "description": "List of specific YouTube URLs to collect metadata for",
            },
            "max_results": {
                "type": "integer",
                "default": 5,
                "description": "Maximum number of results to return",
            },
            "fixture_path": {
                "type": "string",
                "description": "Optional path to a mock manifest for testing",
            },
            "fixture_project_override": {
                "type": "boolean",
                "default": False,
                "description": "If true, override project_id in fixture with input project_id",
            },
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/source_candidate_manifest.schema.json"
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=10,
        network_required=True,
    )
    idempotency_key_fields = ["query", "source_urls", "max_results"]
    side_effects = []
    user_visible_verification = [
        "Verify all results have metadata_only_collected=true",
        "Ensure no local_media_path is present",
    ]

    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        patterns = [
            r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url

    def _fetch_metadata(self, url_or_search: str, max_results: int = 1) -> tuple[list[dict], list[str]]:
        """Fetch metadata using yt-dlp without downloading.
        
        Returns (results, warnings).
        """
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",  # Fast extraction
            "force_generic_extractor": False,
        }

        results = []
        warnings = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_or_search, download=False)
                
                if not info:
                    warnings.append(f"No info found for {url_or_search}")
                    return [], warnings

                # Handle search results or single video
                entries = info.get("entries", [info]) if "entries" in info or "search" in url_or_search else [info]
                
                for entry in entries[:max_results]:
                    if not entry:
                        continue
                        
                    video_id = entry.get("id")
                    if not video_id:
                        warnings.append(f"Entry missing ID in {url_or_search}")
                        continue

                    source_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Check transcript availability
                    has_subs = bool(entry.get("subtitles")) or bool(entry.get("automatic_captions"))
                    
                    if not has_subs:
                        try:
                            from youtube_transcript_api import YouTubeTranscriptApi
                            YouTubeTranscriptApi.list_transcripts(video_id)
                            has_subs = True
                        except Exception:
                            has_subs = False
                    
                    results.append({
                        "source_id": f"yt-{video_id}",
                        "source_url": source_url,
                        "source_title": entry.get("title", "Unknown Title"),
                        "source_channel": entry.get("uploader", entry.get("channel", "Unknown Channel")),
                        "platform": "youtube",
                        "transcript_available": has_subs,
                        "metadata_only_collected": True,
                        "duration_seconds": entry.get("duration"),
                    })
        except Exception as e:
            warnings.append(f"Metadata fetch failed for {url_or_search}: {type(e).__name__}: {str(e)}")
            
        return results, warnings

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        query = inputs.get("query")
        source_urls = inputs.get("source_urls", [])
        max_results = inputs.get("max_results", 5)
        fixture_path = inputs.get("fixture_path")
        fixture_project_override = inputs.get("fixture_project_override", False)

        start_time = time.time()
        warnings = []

        # Mode 1: Fixture Mode
        if fixture_path:
            p = Path(fixture_path)
            if p.exists():
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                    
                    if fixture_project_override:
                        data["project_id"] = project_id
                        
                    # Safety: Force metadata_only_collected and no local_media_path
                    if "sources" in data:
                        for s in data["sources"]:
                            s["metadata_only_collected"] = True
                            if "local_media_path" in s:
                                del s["local_media_path"]
                                
                    return ToolResult(
                        success=True,
                        data=data,
                        duration_seconds=round(time.time() - start_time, 2),
                    )
                except Exception as e:
                    return ToolResult(success=False, error=f"Failed to load fixture: {e}")
            else:
                return ToolResult(success=False, error=f"Fixture path not found: {fixture_path}")

        # Mode 2 & 3: Live Discovery
        all_sources = []

        # Process specific URLs
        for url in source_urls:
            batch_results, batch_warnings = self._fetch_metadata(url, max_results=1)
            all_sources.extend(batch_results)
            warnings.extend(batch_warnings)

        # Process search query
        if query and len(all_sources) < max_results:
            search_url = f"ytsearch{max_results - len(all_sources)}:{query}"
            batch_results, batch_warnings = self._fetch_metadata(search_url, max_results=max_results - len(all_sources))
            all_sources.extend(batch_results)
            warnings.extend(batch_warnings)

        # Final manifest construction
        manifest = {
            "version": "1.0",
            "project_id": project_id,
            "sources": all_sources[:max_results],
        }

        # Safety: Double check no local_media_path
        for s in manifest["sources"]:
            if "local_media_path" in s:
                del s["local_media_path"]
            s["metadata_only_collected"] = True

        # If we failed to find anything and have warnings, report as failure
        if not all_sources and warnings:
            return ToolResult(
                success=False,
                error=f"Discovery failed: {warnings[0]}",
                data={"warnings": warnings},
                duration_seconds=round(time.time() - start_time, 2),
            )

        return ToolResult(
            success=True,
            data=manifest,
            duration_seconds=round(time.time() - start_time, 2),
        )
