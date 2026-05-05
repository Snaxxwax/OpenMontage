"""Wan 2.2 video generation via ComfyUI + n8n.

Uses Wan 2.2 14B FP8 or 5B FP16 models already loaded in local ComfyUI.
Routes through n8n webhook (comfyui-wan22) or calls ComfyUI directly.

Key differences from LTX-2 (comfyui_video.py):
  - Uses UNETLoader + CLIPLoader + VAELoader (separate model components)
  - UMT5-XXL text encoder (longer text understanding than T5)
  - WanImageToVideo conditioning node (T2V: no start_image; I2V: pass start_image)
  - Standard KSampler with euler/beta schedule
  - 16fps native cadence (vs 25fps for LTX-2)
  - 81 frames = 5.06s default (vs 97 frames for LTX-2)

Models in ComfyUI:
  wan22-14b-fp8   Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors   ~20GB VRAM
  wan22-5b-fp16   wan2.2_ti2v_5B_fp16.safetensors                         ~12GB VRAM

Env vars:
    COMFYUI_BASE_URL            http://localhost:8188
    N8N_COMFYUI_WAN22_WEBHOOK   http://localhost:5678/webhook/comfyui-wan22
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json

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

_COMFYUI_URL = os.environ.get("COMFYUI_BASE_URL", "http://localhost:8188")
_N8N_WAN22_WEBHOOK = os.environ.get(
    "N8N_COMFYUI_WAN22_WEBHOOK", "http://localhost:5678/webhook/comfyui-wan22"
)

WAN22_MODELS = {
    "wan22-14b-fp8": "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
    "wan22-5b-fp16": "wan2.2_ti2v_5B_fp16.safetensors",
}
WAN22_CLIP = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
WAN22_VAE = "wan2.2_vae.safetensors"

# Common frame counts at 16fps
WAN22_FRAME_COUNTS = {1: 17, 2: 33, 3: 49, 4: 65, 5: 81, 6: 97, 7: 113, 8: 129}


def _http_json(url: str, body: dict | None = None, timeout: int = 30) -> Any:
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    req = Request(url, data=data, headers=headers, method="POST" if body else "GET")
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _http_download(url: str, timeout: int = 120) -> bytes:
    with urlopen(url, timeout=timeout) as resp:
        return resp.read()


def _comfyui_reachable() -> bool:
    try:
        _http_json(f"{_COMFYUI_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


def _submit_direct(workflow: dict) -> str:
    resp = _http_json(f"{_COMFYUI_URL}/prompt", {"prompt": workflow})
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return prompt_id: {resp}")
    return prompt_id


def _poll_direct(prompt_id: str, timeout_s: int = 1800) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(2)
        history = _http_json(f"{_COMFYUI_URL}/history/{prompt_id}", timeout=10)
        result = history.get(prompt_id)
        if not result:
            continue
        status = result.get("status", {})
        if status.get("status_str") == "error":
            msgs = status.get("messages", [])
            err = next((m[1] for m in msgs if m[0] == "execution_error"), msgs)
            raise RuntimeError(f"ComfyUI error: {err}")
        if status.get("completed"):
            for node_out in result.get("outputs", {}).values():
                for f in node_out.get("videos", []) + node_out.get("images", []):
                    return f
            raise RuntimeError("ComfyUI completed but no video output found")
    raise TimeoutError(f"Wan 2.2 generation timed out after {timeout_s}s")


def _build_wan22_workflow(
    prompt: str,
    negative: str,
    width: int,
    height: int,
    num_frames: int,
    steps: int,
    cfg: float,
    seed: int,
    frame_rate: int,
    unet_model: str,
) -> dict:
    return {
        # Separate model component loaders (Wan uses UNETLoader, not CheckpointLoaderSimple)
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet_model, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": WAN22_CLIP, "type": "wan"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": WAN22_VAE}},
        # Text conditioning
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
        # WanImageToVideo: T2V mode (no start_image). Outputs [pos_cond, neg_cond, latent]
        "6": {
            "class_type": "WanImageToVideo",
            "inputs": {
                "positive": ["4", 0], "negative": ["5", 0], "vae": ["3", 0],
                "width": width, "height": height, "length": num_frames, "batch_size": 1,
            },
        },
        # Standard KSampler with euler/beta — works well for Wan 2.2
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["6", 0], "negative": ["6", 1],
                "latent_image": ["6", 2],
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "euler", "scheduler": "beta", "denoise": 1.0,
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["8", 0], "frame_rate": frame_rate,
                "loop_count": 0, "filename_prefix": "openm_wan22",
                "format": "video/h264-mp4", "pingpong": False, "save_output": True,
            },
        },
    }


class ComfyUIWan22Video(BaseTool):
    name = "comfyui_wan22_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "comfyui_wan22"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "ComfyUI must be running at COMFYUI_BASE_URL (default: http://localhost:8188).\n"
        "Models required (already loaded):\n"
        "  UNet:  Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors\n"
        "  CLIP:  umt5_xxl_fp8_e4m3fn_scaled.safetensors\n"
        "  VAE:   wan2.2_vae.safetensors\n"
        "n8n: import n8n_workflows/comfyui_wan22_video_gen.json and activate.\n"
        "Webhook: POST http://localhost:5678/webhook/comfyui-wan22"
    )
    agent_skills = []

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "negative_prompt": True,
        "seed": True,
        "offline": True,
        "native_audio": False,
        "local_gpu": True,
        "model_selection": True,
    }
    best_for = [
        "high-quality local video generation — Wan 2.2 14B FP8 on 3090",
        "stronger prompt adherence than LTX-2 (UMT5-XXL text encoder)",
        "motion quality and temporal consistency",
        "documentary b-roll with complex scene descriptions",
        "5B model for faster iteration when quality bar is lower",
    ]
    not_good_for = [
        "clips > 8s (memory pressure on 24GB VRAM)",
        "sub-10-second iteration loops (14B is slow — use ltx2-2b or wan22-5b-fp16)",
        "audio-synced content",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "negative_prompt": {"type": "string", "default": "blurry, watermark, text, static, no movement, low quality, ugly"},
            "duration_seconds": {"type": "number", "default": 5, "description": "1–8s. Converted to frame count at 16fps."},
            "num_frames": {"type": "integer", "description": "Override frame count directly. Ignores duration_seconds."},
            "width": {"type": "integer", "default": 832},
            "height": {"type": "integer", "default": 480},
            "steps": {"type": "integer", "default": 20},
            "cfg": {"type": "number", "default": 6.0},
            "frame_rate": {"type": "integer", "default": 16},
            "seed": {"type": "integer"},
            "model": {
                "type": "string",
                "default": "wan22-14b-fp8",
                "enum": list(WAN22_MODELS.keys()),
                "description": "wan22-14b-fp8 (best, ~20GB) or wan22-5b-fp16 (faster, ~12GB)",
            },
            "output_path": {"type": "string"},
            "use_n8n": {"type": "boolean", "default": True},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=4, ram_mb=16000, vram_mb=22000, disk_mb=2000, network_required=False)
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["prompt", "model", "width", "height", "num_frames", "seed"]
    side_effects = ["writes video file to output_path", "queues job in ComfyUI"]
    user_visible_verification = ["Watch generated clip for motion quality and prompt adherence"]

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if _comfyui_reachable() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        duration = inputs.get("duration_seconds", 5)
        steps = inputs.get("steps", 20)
        model = inputs.get("model", "wan22-14b-fp8")
        # 14B: ~3-4 min for 5s/20 steps; 5B: ~1.5 min
        base = 240.0 if "14b" in model else 90.0
        return base * (duration / 5.0) * (steps / 20.0)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if not _comfyui_reachable():
            return ToolResult(success=False, error=f"ComfyUI not reachable at {_COMFYUI_URL}. " + self.install_instructions)

        start = time.time()
        prompt = inputs["prompt"]
        negative = inputs.get("negative_prompt", "blurry, watermark, text, static, no movement, low quality, ugly")
        width = int(inputs.get("width", 832))
        height = int(inputs.get("height", 480))
        steps = int(inputs.get("steps", 20))
        cfg = float(inputs.get("cfg", 6.0))
        frame_rate = int(inputs.get("frame_rate", 16))
        seed = int(inputs.get("seed", uuid.uuid4().int & 0x7FFFFFFF))
        model_key = inputs.get("model", "wan22-14b-fp8")
        unet_model = WAN22_MODELS.get(model_key, WAN22_MODELS["wan22-14b-fp8"])
        use_n8n = inputs.get("use_n8n", True)

        if "num_frames" in inputs:
            num_frames = int(inputs["num_frames"])
        else:
            duration = float(inputs.get("duration_seconds", 5))
            dur_rounded = max(1, min(8, round(duration)))
            num_frames = WAN22_FRAME_COUNTS.get(dur_rounded, 81)

        output_path = Path(inputs.get("output_path", f"/tmp/comfyui_wan22_{seed}.mp4"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if use_n8n:
                result = self._via_n8n(prompt, negative, width, height, num_frames, steps, cfg, seed, frame_rate, model_key, output_path)
            else:
                result = self._direct(prompt, negative, width, height, num_frames, steps, cfg, seed, frame_rate, unet_model, output_path)
        except Exception as exc:
            return ToolResult(success=False, error=f"Wan 2.2 video generation failed: {exc}")

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui_wan22",
                "model": unet_model,
                "prompt": prompt,
                "output": str(output_path),
                "seed": seed,
                "num_frames": num_frames,
                "duration_seconds": round(num_frames / frame_rate, 2),
                "comfyui_filename": result.get("filename"),
                "route": "n8n" if use_n8n else "direct",
            },
            artifacts=[str(output_path)],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=unet_model,
        )

    def _via_n8n(self, prompt, negative, width, height, num_frames, steps, cfg, seed, frame_rate, model_key, output_path: Path) -> dict:
        payload = {
            "prompt": prompt, "negative_prompt": negative,
            "width": width, "height": height, "num_frames": num_frames,
            "steps": steps, "cfg": cfg, "seed": seed,
            "frame_rate": frame_rate, "model": model_key,
        }
        resp = _http_json(_N8N_WAN22_WEBHOOK, payload, timeout=1900)
        if not resp.get("success"):
            raise RuntimeError(f"n8n workflow returned error: {resp}")
        video_bytes = _http_download(resp["download_url"], timeout=120)
        output_path.write_bytes(video_bytes)
        return resp

    def _direct(self, prompt, negative, width, height, num_frames, steps, cfg, seed, frame_rate, unet_model, output_path: Path) -> dict:
        workflow = _build_wan22_workflow(prompt, negative, width, height, num_frames, steps, cfg, seed, frame_rate, unet_model)
        prompt_id = _submit_direct(workflow)
        file_info = _poll_direct(prompt_id)
        params = urlencode({
            "filename": file_info["filename"],
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        })
        video_bytes = _http_download(f"{_COMFYUI_URL}/view?{params}", timeout=120)
        output_path.write_bytes(video_bytes)
        return file_info
