"""Recraft image generation via the official Recraft API.

Supports Recraft V4 raster + vector generation using RECRAFT_API_TOKEN and
falls back to the older fal.ai route when only FAL_KEY is configured.
"""

from __future__ import annotations

import os
import time
import base64
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


class RecraftImage(BaseTool):
    name = "recraft_image"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "recraft"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set RECRAFT_API_TOKEN to your Recraft API token.\n"
        "  Optionally, FAL_KEY can be used for the legacy fal.ai fallback path."
    )
    agent_skills = []

    capabilities = [
        "generate_image",
        "generate_logo",
        "generate_vector",
        "text_to_image",
    ]
    supports = {
        "svg_output": True,
        "text_rendering": True,
        "color_palette": True,
        "custom_size": True,
    }
    best_for = [
        "logos and brand assets",
        "SVG vector output",
        "images with accurate text rendering",
        "clean professional graphics",
    ]
    not_good_for = ["photorealistic images", "offline generation"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "negative_prompt": {"type": "string"},
            "model": {
                "type": "string",
                "enum": [
                    "v4",
                    "v4-pro",
                    "v4-vector",
                    "v4-pro-vector",
                    "recraftv4",
                    "recraftv4_pro",
                    "recraftv4_vector",
                    "recraftv4_pro_vector",
                ],
                "default": "v4",
            },
            "image_size": {
                "type": "string",
                "enum": [
                    "square", "square_hd",
                    "landscape_4_3", "landscape_16_9",
                    "portrait_4_3", "portrait_16_9",
                ],
                "default": "square_hd",
            },
            "size": {
                "type": "string",
                "description": "Recraft size string, e.g. '16:9', '1:1', or an explicit supported size like '1344x768'.",
            },
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 1024},
            "style": {
                "type": "string",
                "enum": [
                    "any", "realistic_image", "digital_illustration",
                    "vector_illustration", "icon",
                ],
                "default": "any",
            },
            "style_id": {
                "type": "string",
                "description": "Reserved for future V3 style support. Not supported on V4.",
            },
            "colors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Color palette as hex strings, e.g. ['#FF5733', '#2E86C1']",
            },
            "output_format": {
                "type": "string",
                "enum": ["png", "svg", "jpg", "webp", "pdf", "tiff", "lottie"],
                "default": "png",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "style", "image_size", "size", "width", "height"]
    side_effects = ["writes image file to output_path", "calls Recraft API or fal.ai fallback"]
    user_visible_verification = ["Inspect generated image for brand accuracy and text readability"]

    _IMAGE_SIZE_TO_SIZE = {
        "square": "1:1",
        "square_hd": "1:1",
        "landscape_4_3": "4:3",
        "landscape_16_9": "16:9",
        "portrait_4_3": "3:4",
        "portrait_16_9": "9:16",
    }

    _SUPPORTED_V4_SIZES = {
        "1:1": "1024x1024",
        "2:1": "1536x768",
        "1:2": "768x1536",
        "3:2": "1280x832",
        "2:3": "832x1280",
        "4:3": "1216x896",
        "3:4": "896x1216",
        "5:4": "1152x896",
        "4:5": "896x1152",
        "6:10": "832x1344",
        "14:10": "1280x896",
        "10:14": "896x1280",
        "16:9": "1344x768",
        "9:16": "768x1344",
    }

    _SUPPORTED_V4_PRO_SIZES = {
        "1:1": "2048x2048",
        "2:1": "3072x1536",
        "1:2": "1536x3072",
        "3:2": "2560x1664",
        "2:3": "1664x2560",
        "4:3": "2432x1792",
        "3:4": "1792x2432",
        "5:4": "2304x1792",
        "4:5": "1792x2304",
        "6:10": "1664x2688",
        "14:10": "2560x1792",
        "10:14": "1792x2560",
        "16:9": "2688x1536",
        "9:16": "1536x2688",
    }

    def _get_recraft_api_key(self) -> str | None:
        return os.environ.get("RECRAFT_API_TOKEN")

    def _get_fal_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_recraft_api_key() or self._get_fal_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "v4")
        if "pro" in model:
            return 0.25
        return 0.04

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        recraft_api_key = self._get_recraft_api_key()
        fal_api_key = self._get_fal_api_key()
        if not recraft_api_key and not fal_api_key:
            return ToolResult(
                success=False,
                error="No Recraft API key found. " + self.install_instructions,
            )

        start = time.time()
        model = inputs.get("model", "v4")
        prompt = inputs["prompt"]
        try:
            if recraft_api_key:
                result = self._execute_direct(inputs, recraft_api_key)
            else:
                result = self._execute_fal(inputs, fal_api_key)
        except Exception as e:
            return ToolResult(success=False, error=f"Recraft generation failed: {e}")

        result.cost_usd = self.estimate_cost(inputs)
        result.duration_seconds = round(time.time() - start, 2)
        result.data.setdefault("provider", "recraft")
        result.data.setdefault("prompt", prompt)
        result.data.setdefault("model", model)
        return result

    def _execute_direct(self, inputs: dict[str, Any], api_key: str) -> ToolResult:
        import requests

        resolved_model = self._resolve_direct_model(inputs)
        requested_width = int(inputs.get("width", 1024))
        requested_height = int(inputs.get("height", 1024))
        size = self._resolve_direct_size(inputs, resolved_model)
        output_format = self._resolve_output_format(inputs, resolved_model)

        payload: dict[str, Any] = {
            "prompt": self._build_prompt(inputs, resolved_model),
            "model": resolved_model,
            "size": size,
            "response_format": "b64_json",
        }
        if resolved_model.endswith("_vector"):
            if output_format != "svg":
                payload["response_format"] = "url"
            if output_format in {"pdf", "lottie"}:
                payload["image_format"] = output_format
        else:
            payload["image_format"] = output_format
            if inputs.get("negative_prompt"):
                payload["negative_prompt"] = inputs["negative_prompt"]

        response = requests.post(
            "https://external.api.recraft.ai/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=240,
        )
        if not response.ok:
            raise RuntimeError(f"{response.status_code} {response.text}")
        data = response.json()
        item = data["data"][0]

        if payload["response_format"] == "b64_json":
            raw = base64.b64decode(item["b64_json"])
        else:
            asset_response = requests.get(item["url"], timeout=120)
            asset_response.raise_for_status()
            raw = asset_response.content

        ext = self._output_extension(output_format, resolved_model)
        output_path = Path(inputs.get("output_path", f"generated_image.{ext}"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(raw)

        resized = False
        actual_size = self._actual_generated_size(size, resolved_model)
        if not resolved_model.endswith("_vector") and (
            requested_width,
            requested_height,
        ) != actual_size:
            resized = self._resize_raster(output_path, requested_width, requested_height)

        model_label = f"recraft:{resolved_model}"
        return ToolResult(
            success=True,
            data={
                "provider": "recraft",
                "model": resolved_model,
                "prompt": inputs["prompt"],
                "output": str(output_path),
                "image_id": item.get("image_id"),
                "requested_size": f"{requested_width}x{requested_height}",
                "recraft_size": size,
                "generated_size": f"{actual_size[0]}x{actual_size[1]}",
                "resized_to_requested": resized,
                "transport": "direct_api",
            },
            artifacts=[str(output_path)],
            model=model_label,
        )

    def _execute_fal(self, inputs: dict[str, Any], api_key: str | None) -> ToolResult:
        import requests

        if not api_key:
            raise RuntimeError("FAL_KEY not set for legacy fallback path.")

        model = inputs.get("model", "v4")
        prompt = self._build_prompt(inputs, model)
        model_path = "recraft/v4/text-to-image"
        if "pro" in model:
            model_path = "recraft/v4/pro/text-to-image"

        payload: dict[str, Any] = {"prompt": prompt}
        if inputs.get("image_size"):
            payload["image_size"] = inputs["image_size"]
        if inputs.get("colors"):
            payload["colors"] = inputs["colors"]

        response = requests.post(
            f"https://fal.run/fal-ai/{model_path}",
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        if not response.ok:
            raise RuntimeError(f"{response.status_code} {response.text}")
        data = response.json()
        image_url = data["images"][0]["url"]
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()

        ext = "svg" if inputs.get("style") == "vector_illustration" else "png"
        output_path = Path(inputs.get("output_path", f"generated_image.{ext}"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_response.content)

        return ToolResult(
            success=True,
            data={
                "provider": "recraft",
                "model": model,
                "prompt": inputs["prompt"],
                "output": str(output_path),
                "transport": "fal_fallback",
            },
            artifacts=[str(output_path)],
            model=f"fal-ai/{model_path}",
        )

    def _resolve_direct_model(self, inputs: dict[str, Any]) -> str:
        style = inputs.get("style", "any")
        raw_model = inputs.get("model", "v4")
        model_aliases = {
            "v4": "recraftv4",
            "v4-pro": "recraftv4_pro",
            "v4-vector": "recraftv4_vector",
            "v4-pro-vector": "recraftv4_pro_vector",
            "recraftv4": "recraftv4",
            "recraftv4_pro": "recraftv4_pro",
            "recraftv4_vector": "recraftv4_vector",
            "recraftv4_pro_vector": "recraftv4_pro_vector",
        }
        resolved = model_aliases.get(raw_model, "recraftv4")
        if style in {"vector_illustration", "icon"} and not resolved.endswith("_vector"):
            resolved = f"{resolved}_vector" if not resolved.endswith("_pro") else f"{resolved}_vector"
        if inputs.get("style_id"):
            raise ValueError("style_id is not supported for Recraft V4 models in this tool yet.")
        return resolved

    def _resolve_direct_size(self, inputs: dict[str, Any], resolved_model: str) -> str:
        if inputs.get("size"):
            return str(inputs["size"])

        width = int(inputs.get("width", 1024))
        height = int(inputs.get("height", 1024))
        explicit = f"{width}x{height}"
        size_table = self._SUPPORTED_V4_PRO_SIZES if "_pro" in resolved_model else self._SUPPORTED_V4_SIZES
        if explicit in size_table.values():
            return explicit

        ratio = self._ratio_label(width, height)
        if ratio in size_table:
            return ratio

        image_size = inputs.get("image_size")
        if image_size in self._IMAGE_SIZE_TO_SIZE:
            return self._IMAGE_SIZE_TO_SIZE[image_size]

        return "1:1"

    def _resolve_output_format(self, inputs: dict[str, Any], resolved_model: str) -> str:
        explicit = inputs.get("output_format")
        if explicit:
            return explicit
        output_path = inputs.get("output_path", "")
        if output_path:
            suffix = Path(output_path).suffix.lower().lstrip(".")
            if suffix:
                return suffix
        if resolved_model.endswith("_vector"):
            return "svg"
        return "png"

    def _build_prompt(self, inputs: dict[str, Any], resolved_model: str) -> str:
        prompt = inputs["prompt"].strip()
        style = inputs.get("style", "any")
        style_prefix = {
            "realistic_image": "photorealistic design render",
            "digital_illustration": "digital illustration",
            "vector_illustration": "clean vector illustration",
            "icon": "minimal vector icon",
        }.get(style)
        if style_prefix and style != "any" and style_prefix.lower() not in prompt.lower():
            prompt = f"{style_prefix}, {prompt}"
        colors = inputs.get("colors") or []
        if colors:
            palette = ", ".join(colors)
            prompt = f"{prompt}. Use this color palette: {palette}."
        if resolved_model.endswith("_vector") and "svg" not in prompt.lower():
            prompt = f"{prompt}. Crisp vector shapes, clean edges, no raster texture."
        return prompt

    @staticmethod
    def _ratio_label(width: int, height: int) -> str:
        from math import gcd

        divisor = gcd(width, height)
        return f"{width // divisor}:{height // divisor}"

    def _actual_generated_size(self, size: str, resolved_model: str) -> tuple[int, int]:
        if "x" in size:
            width, height = size.lower().split("x", 1)
            return int(width), int(height)
        size_table = self._SUPPORTED_V4_PRO_SIZES if "_pro" in resolved_model else self._SUPPORTED_V4_SIZES
        explicit = size_table.get(size, "1024x1024")
        width, height = explicit.split("x", 1)
        return int(width), int(height)

    @staticmethod
    def _output_extension(output_format: str, resolved_model: str) -> str:
        if output_format in {"jpg", "jpeg"}:
            return "jpg"
        if output_format == "tiff":
            return "tiff"
        if resolved_model.endswith("_vector") and output_format not in {"svg", "pdf", "lottie"}:
            return "svg"
        return output_format

    @staticmethod
    def _resize_raster(path: Path, width: int, height: int) -> bool:
        try:
            from PIL import Image

            with Image.open(path) as img:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                resized.save(path)
            return True
        except Exception:
            return False
