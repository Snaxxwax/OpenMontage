"""Google Veo video generation via the Gemini API (direct Google access).

Uses the generativelanguage.googleapis.com endpoint -- no fal.ai or third-party
gateway. Auth via GOOGLE_API_KEY or GEMINI_API_KEY (same key used for Imagen).

Supported operations:
  text_to_video         -- generate from a text prompt
  image_to_video        -- animate a start frame
  first_last_frame      -- interpolate between a start and end frame
  reference_to_video    -- generate with style/subject reference images

Models (model_variant parameter):
  veo-3.1-generate-preview       -- latest, highest quality
  veo-3.1-fast-generate-preview  -- faster, lower cost
  veo-3.0-generate-preview       -- Veo 3 stable
"""

from __future__ import annotations

import base64
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_POLL_INTERVAL = 10  # seconds between status checks
_MAX_WAIT = 600      # 10 minutes


def _file_to_inline_data(path_str: str) -> dict[str, str]:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return {
        "mimeType": mime_type,
        "data": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


class VeoGoogleVideo(BaseTool):
    """Google Veo video generation via the Gemini generativelanguage API."""

    name = "veo_google_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "veo_google"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set GOOGLE_API_KEY (or GEMINI_API_KEY) to your Google AI API key.\n"
        "  Get one at https://aistudio.google.com/app/apikey\n"
        "This is the same key used for Google Imagen -- no additional setup needed."
    )
    agent_skills = ["ai-video-gen"]

    capabilities = [
        "text_to_video",
        "image_to_video",
        "first_last_frame_to_video",
        "reference_to_video",
    ]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "first_last_frame_to_video": True,
        "reference_to_video": True,
        "native_audio": True,
        "no_gateway_fee": True,
    }
    best_for = [
        "direct Google API access without fal.ai or third-party gateway",
        "reusing an existing GOOGLE_API_KEY (same key as Imagen)",
        "cutting-edge quality from Google DeepMind",
        "image-to-video and first/last-frame interpolation",
    ]
    not_good_for = [
        "budget projects (premium pricing per second)",
        "offline generation",
        "very fast iteration -- generation takes 2-5 minutes",
    ]
    fallback_tools = ["veo_video", "kling_video", "runway_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text description of the video to generate.",
            },
            "operation": {
                "type": "string",
                "enum": [
                    "text_to_video",
                    "image_to_video",
                    "first_last_frame_to_video",
                    "reference_to_video",
                ],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": [
                    "veo-3.1-generate-preview",
                    "veo-3.1-fast-generate-preview",
                    "veo-3.0-generate-preview",
                ],
                "default": "veo-3.1-generate-preview",
                "description": (
                    "veo-3.1-generate-preview -- latest, highest quality. "
                    "veo-3.1-fast-generate-preview -- faster, lower cost. "
                    "veo-3.0-generate-preview -- Veo 3 stable."
                ),
            },
            "duration_seconds": {
                "type": "string",
                "enum": ["4", "6", "8"],
                "default": "8",
                "description": "Video duration. Veo 3.1 supports 4, 6, or 8 seconds.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16"],
                "default": "16:9",
            },
            "resolution": {
                "type": "string",
                "enum": ["720p", "1080p", "4k"],
                "default": "1080p",
            },
            "person_generation": {
                "type": "string",
                "enum": ["allow_all", "allow_adult"],
                "default": "allow_all",
                "description": "Whether to allow person generation in outputs.",
            },
            "image_url": {
                "type": "string",
                "description": "Public URL of start-frame image (image_to_video / first_last_frame_to_video).",
            },
            "image_path": {
                "type": "string",
                "description": "Local path to start-frame image (image_to_video / first_last_frame_to_video).",
            },
            "last_frame_url": {
                "type": "string",
                "description": "Public URL of end-frame image (first_last_frame_to_video).",
            },
            "last_frame_path": {
                "type": "string",
                "description": "Local path to end-frame image (first_last_frame_to_video).",
            },
            "reference_image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local paths to reference images (reference_to_video).",
            },
            "reference_image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Public URLs of reference images (reference_to_video).",
            },
            "output_path": {
                "type": "string",
                "description": "Output file path (.mp4). Defaults to veo_google_output.mp4.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model_variant", "operation", "duration_seconds"]
    side_effects = [
        "writes video file to output_path",
        "calls Google generativelanguage API",
    ]
    user_visible_verification = [
        "Watch generated clip for visual quality and motion",
        "Check audio synchronization if native audio was generated",
    ]

    def _get_api_key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "veo-3.1-generate-preview")
        duration = int(inputs.get("duration_seconds", "8"))
        if "fast" in variant:
            return 0.10 * duration
        return 0.35 * duration

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "veo-3.1-generate-preview")
        return 90.0 if "fast" in variant else 180.0

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

    def _fetch_url_as_inline_data(self, url: str) -> dict[str, str]:
        import requests
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "application/octet-stream").split(";")[0]
        return {
            "mimeType": content_type,
            "data": base64.b64encode(resp.content).decode("ascii"),
        }

    def _resolve_inline_data(
        self, url_value: str | None, path_value: str | None
    ) -> dict[str, str] | None:
        if path_value:
            return _file_to_inline_data(path_value)
        if url_value:
            return self._fetch_url_as_inline_data(url_value)
        return None

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        import requests

        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="GOOGLE_API_KEY / GEMINI_API_KEY not set. " + self.install_instructions,
            )

        start = time.time()
        operation = inputs.get("operation", "text_to_video")
        model = inputs.get("model_variant", "veo-3.1-generate-preview")

        instance: dict[str, Any] = {"prompt": inputs["prompt"]}

        if operation == "image_to_video":
            inline = self._resolve_inline_data(
                inputs.get("image_url"), inputs.get("image_path")
            )
            if not inline:
                return ToolResult(
                    success=False,
                    error="image_to_video requires image_url or image_path",
                )
            instance["image"] = {"inlineData": inline}

        elif operation == "first_last_frame_to_video":
            first_inline = self._resolve_inline_data(
                inputs.get("image_url"), inputs.get("image_path")
            )
            last_inline = self._resolve_inline_data(
                inputs.get("last_frame_url"), inputs.get("last_frame_path")
            )
            if not first_inline or not last_inline:
                return ToolResult(
                    success=False,
                    error=(
                        "first_last_frame_to_video requires "
                        "image_url/image_path (first frame) and "
                        "last_frame_url/last_frame_path (last frame)"
                    ),
                )
            instance["image"] = {"inlineData": first_inline}
            instance["lastFrame"] = {"inlineData": last_inline}

        elif operation == "reference_to_video":
            ref_images = []
            for path in (inputs.get("reference_image_paths") or []):
                ref_images.append({
                    "image": {"inlineData": _file_to_inline_data(path)},
                    "referenceType": "asset",
                })
            for url in (inputs.get("reference_image_urls") or []):
                ref_images.append({
                    "image": {"inlineData": self._fetch_url_as_inline_data(url)},
                    "referenceType": "asset",
                })
            if not ref_images:
                return ToolResult(
                    success=False,
                    error="reference_to_video requires reference_image_paths or reference_image_urls",
                )
            instance["referenceImages"] = ref_images

        parameters: dict[str, Any] = {
            "aspectRatio": inputs.get("aspect_ratio", "16:9"),
            "durationSeconds": str(inputs.get("duration_seconds", "8")),
            "resolution": inputs.get("resolution", "1080p"),
            "personGeneration": inputs.get("person_generation", "allow_all"),
        }

        payload = {"instances": [instance], "parameters": parameters}
        submit_url = f"{_BASE_URL}/models/{model}:predictLongRunning"

        try:
            submit_resp = requests.post(
                submit_url,
                headers=self._headers(api_key),
                json=payload,
                timeout=30,
            )
            if not submit_resp.ok:
                return ToolResult(
                    success=False,
                    error=f"Veo submit failed ({submit_resp.status_code}): {submit_resp.text[:500]}",
                )
            operation_name = submit_resp.json().get("name")
            if not operation_name:
                return ToolResult(
                    success=False,
                    error=f"No operation name in response: {submit_resp.text[:300]}",
                )

            # Poll until done
            poll_url = f"{_BASE_URL}/{operation_name}"
            elapsed = 0
            while elapsed < _MAX_WAIT:
                time.sleep(_POLL_INTERVAL)
                elapsed += _POLL_INTERVAL
                poll_resp = requests.get(
                    poll_url, headers=self._headers(api_key), timeout=30
                )
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
                if poll_data.get("done"):
                    break
                if poll_data.get("error"):
                    return ToolResult(
                        success=False,
                        error=f"Veo generation failed: {poll_data['error']}",
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"Veo generation timed out after {_MAX_WAIT}s",
                )

            # Extract video URI from completed operation
            samples = (
                poll_data.get("response", {})
                .get("generateVideoResponse", {})
                .get("generatedSamples", [])
            )
            if not samples:
                return ToolResult(
                    success=False,
                    error=f"No samples in completed response: {poll_data}",
                )
            video_uri = samples[0].get("video", {}).get("uri")
            if not video_uri:
                return ToolResult(
                    success=False,
                    error=f"No video URI in sample: {samples[0]}",
                )

            # Download the video (auth header required)
            video_resp = requests.get(
                video_uri,
                headers={"x-goog-api-key": api_key},
                timeout=120,
            )
            video_resp.raise_for_status()

            output_path = Path(inputs.get("output_path", "veo_google_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(video_resp.content)

        except Exception as e:
            return ToolResult(success=False, error=f"Veo Google API call failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "veo_google",
                "model": model,
                "operation": operation,
                "prompt": inputs["prompt"],
                "duration_seconds": inputs.get("duration_seconds", "8"),
                "resolution": parameters["resolution"],
                "aspect_ratio": parameters["aspectRatio"],
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
