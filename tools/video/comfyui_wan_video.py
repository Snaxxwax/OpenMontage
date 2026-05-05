"""WAN video generation via a local ComfyUI server.

This tool is meant for setups where WAN weights are already installed inside
the ComfyUI container (common on GPU workstations) and OpenMontage should avoid
re-downloading model weights for diffusers-based local generation.
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests

from tools._comfyui.client import ComfyUIClient, ComfyUIError
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


_DEFAULT_BASE_URL = "http://127.0.0.1:8188"

_MODEL_VARIANTS: dict[str, dict[str, str]] = {
    # This ComfyUI install ships a TI2V weight; quality is best with image_to_video.
    "wan2.2-ti2v-5b": {
        "model": "wan2.2_ti2v_5B_fp16.safetensors",
        "vae": "wan2.2_vae.safetensors",
        "base_precision": "fp16",
        "quantization": "disabled",
    },
}


class ComfyUIWanVideo(BaseTool):
    name = "comfyui_wan_video"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "comfyui_wan"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Start a local ComfyUI server with WAN models installed and accessible.\n"
        "  If ComfyUI is running on a non-default host/port, set COMFYUI_SERVER_URL (or legacy COMFYUI_BASE_URL).\n"
        f"  Default: COMFYUI_SERVER_URL={_DEFAULT_BASE_URL}"
    )
    fallback_tools = ["wan_video", "hunyuan_video", "ltx_video_local", "cogvideo_video", "image_selector"]

    capabilities = ["text_to_video", "image_to_video", "model_selection"]
    supports = {
        "reference_image": True,
        "offline": True,
        "native_audio": False,
        "local_gpu": True,
        "text_to_video": False,
        "image_to_video": True,
        "custom_workflow": False,
        "legacy_provider": True,
    }
    best_for = [
        "GPU workstations that already run ComfyUI with WAN weights installed",
        "avoiding duplicate model downloads (reuse ComfyUI's model store)",
        "image-to-video workflows (TI2V weights) that need clean, stable frames",
    ]
    not_good_for = ["machines without ComfyUI running", "CPU-only machines"]
    provider_matrix = {
        key: {"tool": "comfyui_wan_video", **value, "mode": "comfyui_local"} for key, value in _MODEL_VARIANTS.items()
    }

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video"],
                "default": "image_to_video",
                "description": (
                    "This ComfyUI WAN install uses a TI2V model; image_to_video is recommended "
                    "for clear results. text_to_video may produce degraded outputs without a reference image."
                ),
            },
            "negative_prompt": {"type": "string", "default": "blurry, low quality, watermark, text, logo"},
            "model_variant": {"type": "string", "enum": sorted(_MODEL_VARIANTS), "default": "wan2.2-ti2v-5b"},
            "reference_image_url": {"type": "string"},
            "reference_image_path": {"type": "string"},
            "width": {"type": "integer", "default": 832},
            "height": {"type": "integer", "default": 480},
            "num_frames": {"type": "integer", "default": 24},
            "fps": {"type": "integer", "default": 8},
            "num_inference_steps": {"type": "integer", "default": 30},
            "cfg": {"type": "number", "default": 6.0},
            "shift": {"type": "number", "default": 5.0},
            "seed": {"type": "integer", "default": 0},
            "scheduler": {"type": "string", "default": "flowmatch_pusa"},
            "image_resize_crop": {"type": "string", "enum": ["disabled", "center"], "default": "center"},
            "latent_strength": {"type": "number", "default": 1.0, "description": "WanVideoEncode latent strength (image_to_video)"},
            "noise_aug_strength": {"type": "number", "default": 0.0, "description": "WanVideoEncode noise augmentation (image_to_video)"},
            "t5_model_name": {"type": "string", "default": "umt5-xxl-enc-bf16.safetensors"},
            "t5_precision": {"type": "string", "enum": ["fp32", "bf16"], "default": "bf16"},
            "vae_precision": {"type": "string", "enum": ["fp32", "bf16"], "default": "bf16"},
            "server_url": {"type": "string", "description": "Override COMFYUI_SERVER_URL for this call"},
            "comfyui_base_url": {"type": "string", "description": "Override legacy COMFYUI_BASE_URL for this call"},
            "wait_for_queue": {"type": "boolean", "default": False},
            "queue_timeout_seconds": {"type": "integer", "default": 60},
            "require_free_vram_mb": {"type": "integer"},
            "require_free_ram_mb": {"type": "integer"},
            "resource_timeout_seconds": {"type": "integer", "default": 60},
            "timeout_seconds": {"type": "integer", "default": 600},
            "poll_interval_seconds": {"type": "number", "default": 5},
            "output_path": {"type": "string"},
            "filename_prefix": {"type": "string", "description": "ComfyUI output filename prefix override"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=16000, vram_mb=12000, disk_mb=4000, network_required=True)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout", "connection"])
    idempotency_key_fields = ["prompt", "model_variant", "seed", "width", "height", "num_frames", "num_inference_steps"]
    side_effects = ["writes video file to output_path", "submits a prompt to local ComfyUI"]
    user_visible_verification = ["Watch generated clip for motion coherence and artifacts"]

    def get_status(self) -> ToolStatus:
        client = ComfyUIClient(capability=self.capability)
        return ToolStatus.AVAILABLE if client.is_available() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        # Highly variable across GPUs and model variant; return a conservative guess.
        variant = inputs.get("model_variant", "wan2.2-ti2v-5b")
        if variant != "wan2.2-ti2v-5b":
            return 120.0
        return 90.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        explicit_server_url = (
            inputs.get("server_url")
            or inputs.get("comfyui_base_url")
            or os.environ.get("COMFYUI_VIDEO_SERVER_URL")
            or os.environ.get("COMFYUI_SERVER_URL")
            or os.environ.get("COMFYUI_BASE_URL")
            or _DEFAULT_BASE_URL
        )
        client = ComfyUIClient(explicit_server_url, capability=self.capability)
        if not client.is_available():
            return ToolResult(success=False, error=client.unavailable_reason())

        variant_key = inputs.get("model_variant", "wan2.2-ti2v-5b")
        variant = _MODEL_VARIANTS.get(variant_key, _MODEL_VARIANTS["wan2.2-ti2v-5b"])

        operation = inputs.get("operation", "image_to_video")
        width = int(inputs.get("width", 832))
        height = int(inputs.get("height", 480))
        num_frames = int(inputs.get("num_frames", 24))
        fps = int(inputs.get("fps", 8))
        steps = int(inputs.get("num_inference_steps", 30))
        cfg = float(inputs.get("cfg", 6.0))
        shift = float(inputs.get("shift", 5.0))
        seed = int(inputs.get("seed", 0))
        scheduler = str(inputs.get("scheduler", "flowmatch_pusa"))

        filename_prefix = (
            inputs.get("filename_prefix")
            or f"openmontage_wan_{variant_key.replace('.', '_').replace('-', '_')}_{uuid.uuid4().hex[:8]}"
        )

        upload_name: str | None = None
        if operation == "image_to_video":
            try:
                local_ref = self._resolve_reference_image(inputs, seed)
                upload_name = client.upload_image(local_path=local_ref, name=f"om_wan_ref_{seed}.png")
            except (ComfyUIError, requests.RequestException, OSError, ValueError) as exc:
                return ToolResult(success=False, error=f"reference_image required for image_to_video: {exc}")

        workflow: dict[str, Any] = {
            "1": {
                "class_type": "WanVideoModelLoader",
                "inputs": {
                    "model": variant["model"],
                    "base_precision": variant.get("base_precision", "bf16"),
                    "quantization": variant.get("quantization", "disabled"),
                    "load_device": "offload_device",
                    "attention_mode": "comfy",
                },
            },
            "2": {
                "class_type": "WanVideoVAELoader",
                "inputs": {
                    "model_name": variant["vae"],
                    # Object info claims this is optional, but some builds
                    # behave as if it is required; always pass it.
                    "precision": inputs.get("vae_precision", "bf16"),
                },
            },
            "3": {
                "class_type": "LoadWanVideoT5TextEncoder",
                "inputs": {
                    "model_name": inputs.get("t5_model_name", "umt5-xxl-enc-bf16.safetensors"),
                    "precision": inputs.get("t5_precision", "bf16"),
                },
            },
            "4": {
                "class_type": "WanVideoTextEncode",
                "inputs": {
                    "positive_prompt": inputs["prompt"],
                    "negative_prompt": inputs.get("negative_prompt", "blurry, low quality, watermark, text, logo"),
                    "t5": ["3", 0],
                },
            },
            "5": {
                "class_type": "WanVideoEmptyEmbeds",
                "inputs": {"width": width, "height": height, "num_frames": num_frames},
            },
            "6": {
                "class_type": "WanVideoSampler",
                "inputs": {
                    "model": ["1", 0],
                    "image_embeds": ["5", 0],
                    "text_embeds": ["4", 0],
                    "steps": steps,
                    "cfg": cfg,
                    "shift": shift,
                    "seed": seed,
                    "force_offload": True,
                    "scheduler": scheduler,
                    "riflex_freq_index": 0,
                },
            },
            "7": {
                "class_type": "WanVideoDecode",
                "inputs": {
                    "vae": ["2", 0],
                    "samples": ["6", 0],
                    "enable_vae_tiling": False,
                    "tile_x": 256,
                    "tile_y": 256,
                    "tile_stride_x": 128,
                    "tile_stride_y": 128,
                },
            },
            "8": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["7", 0],
                    "frame_rate": float(fps),
                    "loop_count": 0,
                    "filename_prefix": filename_prefix,
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }

        # For TI2V, inject the reference image as extra_latents (mirrors the upstream example workflow).
        if operation == "image_to_video" and upload_name:
            workflow["9"] = {"class_type": "LoadImage", "inputs": {"image": upload_name}}
            workflow["10"] = {
                "class_type": "ImageScale",
                "inputs": {
                    "image": ["9", 0],
                    "upscale_method": "lanczos",
                    "width": width,
                    "height": height,
                    "crop": inputs.get("image_resize_crop", "center"),
                },
            }
            workflow["11"] = {
                "class_type": "WanVideoEncode",
                "inputs": {
                    "vae": ["2", 0],
                    "image": ["10", 0],
                    "enable_vae_tiling": False,
                    "tile_x": 272,
                    "tile_y": 272,
                    "tile_stride_x": 144,
                    "tile_stride_y": 128,
                    "noise_aug_strength": float(inputs.get("noise_aug_strength", 0.0)),
                    "latent_strength": float(inputs.get("latent_strength", 1.0)),
                },
            }
            workflow["5"]["inputs"]["extra_latents"] = ["11", 0]

        out_path = Path(inputs.get("output_path") or f"shared_studio/projects/_smoke/assets/video/{filename_prefix}.mp4").expanduser()
        start = time.time()

        timeout_s = int(inputs.get("timeout_seconds", 600))
        poll_interval_s = float(inputs.get("poll_interval_seconds", 5))
        wait_for_queue = bool(inputs.get("wait_for_queue", False))
        queue_timeout_s = int(inputs.get("queue_timeout_seconds", 60))
        min_vram_free_mb = inputs.get("require_free_vram_mb")
        min_ram_free_mb = inputs.get("require_free_ram_mb")
        resource_timeout_s = int(inputs.get("resource_timeout_seconds", 60))

        try:
            run = client.run_workflow(
                workflow,
                dest=out_path,
                output_node="8",
                timeout_s=timeout_s,
                poll_interval_s=poll_interval_s,
                wait_for_queue=wait_for_queue,
                queue_timeout_s=queue_timeout_s,
                min_vram_free_mb=int(min_vram_free_mb) if min_vram_free_mb is not None else None,
                min_ram_free_mb=int(min_ram_free_mb) if min_ram_free_mb is not None else None,
                resource_timeout_s=resource_timeout_s,
            )
        except ComfyUIError as exc:
            return ToolResult(success=False, error=f"ComfyUI generation failed: {exc}")

        artifacts = [a.get("local_path") for a in run.get("artifacts", []) if a.get("local_path")]
        output_path = artifacts[0] if artifacts else str(out_path)
        output_filename = ""
        if run.get("artifacts"):
            output_filename = str(run["artifacts"][0].get("filename", ""))

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui_wan",
                "model": variant_key,
                "output_path": output_path,
                "output_paths": artifacts,
                "prompt_id": run.get("prompt_id"),
                "comfyui_server_url": client.server_url,
                "comfyui_base_url": client.server_url,  # legacy field kept for compatibility
                "comfyui_filename": output_filename,
                "operation": operation,
            },
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=variant_key,
        )

    @staticmethod
    def _resolve_reference_image(inputs: dict[str, Any], seed: int) -> Path:
        ref_path = inputs.get("reference_image_path")
        ref_url = inputs.get("reference_image_url")
        if ref_path:
            path = Path(ref_path).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"reference_image_path not found: {path}")
            return path
        if ref_url:
            r = requests.get(ref_url, timeout=30)
            r.raise_for_status()
            tmp = Path(f"shared_studio/projects/_smoke/assets/images/comfyui_wan_ref_{seed}.png").expanduser()
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(r.content)
            return tmp
        raise ValueError("Provide reference_image_path or reference_image_url")
