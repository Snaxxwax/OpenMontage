"""Local image generation via ComfyUI API server (FLUX.1-dev fp8)."""

from __future__ import annotations

import json
import time
import uuid
import copy
from pathlib import Path
from typing import Any
from urllib import request

import yaml

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

import os
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "172.18.0.2")
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", 18188))
WORKFLOW_PATH = Path("/home/pop/ComfyUI/workflows/flux_dev_api.json")
STYLES_DIR = Path(__file__).parent.parent.parent / "styles"
DEFAULT_STYLE = "systemic-pulse"


def _load_style(style_name: str) -> dict:
    path = STYLES_DIR / f"{style_name}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text())
    return {}

# Node IDs in the workflow (see flux_dev_api.json)
_PROMPT_NODE = "4"
_SEED_NODE = "7"
_SIZE_NODE = "5"
_GUIDANCE_NODE = "6"
_SAVE_NODE = "10"


class ComfyUIImage(BaseTool):
    name = "comfyui_image"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "comfyui_flux"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Start ComfyUI API server:\n"
        "  cd /home/pop/ComfyUI && python3 main.py --listen 127.0.0.1 --port 8188\n"
        "Ensure fish-speech is unloaded first to free VRAM."
    )
    agent_skills = []

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": False,  # FLUX uses guidance scale instead
        "seed": True,
        "offline": True,
        "custom_size": True,
        "lora": True,
    }
    best_for = [
        "free local image generation (zero API cost)",
        "vector-style and illustration prompts",
        "educational infographic visuals",
        "high-fidelity scene illustrations for Hidden Systems channel",
        "batch production — no rate limits or per-image cost",
    ]
    not_good_for = [
        "when fish-speech is loaded (VRAM conflict — unload first)",
        "when ComfyUI server is not running",
        "photorealistic portrait generation (use cloud API instead)",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Scene description — brand style prefix is applied automatically"},
            "style": {"type": "string", "default": DEFAULT_STYLE, "description": "Style playbook name from styles/. Defaults to systemic-pulse."},
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 576, "description": "Default 576 for 16:9 video frames"},
            "seed": {"type": "integer", "default": -1},
            "steps": {"type": "integer", "default": 25},
            "guidance": {"type": "number", "default": 3.5},
            "output_path": {"type": "string"},
            "poll_interval": {"type": "number", "default": 2.0},
            "timeout": {"type": "number", "default": 300.0},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=4000, vram_mb=16000, disk_mb=1000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["prompt", "width", "height", "seed", "steps", "guidance"]
    side_effects = [
        "writes image to output_path",
        "requires ComfyUI server running on localhost:8188",
        "requires fish-speech to be unloaded",
    ]
    user_visible_verification = ["Inspect generated image for visual quality and prompt adherence"]

    def _server_url(self, path: str) -> str:
        return f"http://{COMFYUI_HOST}:{COMFYUI_PORT}{path}"

    def get_status(self) -> ToolStatus:
        try:
            req = request.urlopen(self._server_url("/system_stats"), timeout=3)
            if req.status == 200:
                return ToolStatus.AVAILABLE
        except Exception:
            pass
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        steps = inputs.get("steps", 20)
        return steps * 2.5  # ~2.5s per step on RTX 3090 for FLUX fp8

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error=(
                    "ComfyUI server not running. Start it with:\n"
                    "  cd /home/pop/ComfyUI && python3 main.py --listen 127.0.0.1 --port 8188\n"
                    "Remember to unload fish-speech first."
                ),
            )

        start = time.time()
        style_name = inputs.get("style", DEFAULT_STYLE)
        style = _load_style(style_name)
        asset_cfg = style.get("asset_generation", {})
        flux_defaults = asset_cfg.get("flux_defaults", {})

        style_prefix = asset_cfg.get("image_prompt_prefix", "").strip()
        style_negative = asset_cfg.get("image_negative_prompt", "").strip()
        raw_prompt = inputs["prompt"].strip()
        prompt_text = f"{style_prefix} {raw_prompt}".strip() if style_prefix else raw_prompt

        width = inputs.get("width", flux_defaults.get("width", 1024))
        height = inputs.get("height", flux_defaults.get("height", 576))
        seed = inputs.get("seed", -1)
        steps = inputs.get("steps", flux_defaults.get("steps", 25))
        guidance = inputs.get("guidance", flux_defaults.get("guidance", 3.5))
        poll_interval = inputs.get("poll_interval", 2.0)
        timeout = inputs.get("timeout", 300.0)

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Load and patch the workflow
        try:
            workflow = json.loads(WORKFLOW_PATH.read_text())
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to load workflow: {e}")

        workflow = copy.deepcopy(workflow)
        workflow[_PROMPT_NODE]["inputs"]["text"] = prompt_text
        workflow["8"]["inputs"]["text"] = style_negative  # negative prompt node
        workflow[_SIZE_NODE]["inputs"]["width"] = width
        workflow[_SIZE_NODE]["inputs"]["height"] = height
        workflow[_SEED_NODE]["inputs"]["seed"] = seed
        workflow[_SEED_NODE]["inputs"]["steps"] = steps
        workflow[_GUIDANCE_NODE]["inputs"]["guidance"] = guidance

        client_id = str(uuid.uuid4())
        payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()

        # Queue the prompt
        try:
            req = request.Request(
                self._server_url("/prompt"),
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = request.urlopen(req, timeout=30)
            resp_data = json.loads(resp.read())
            prompt_id = resp_data["prompt_id"]
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to queue prompt: {e}")

        # Poll for completion
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(poll_interval)
            try:
                history_resp = request.urlopen(
                    self._server_url(f"/history/{prompt_id}"), timeout=10
                )
                history = json.loads(history_resp.read())
            except Exception:
                continue

            if prompt_id not in history:
                continue

            outputs = history[prompt_id].get("outputs", {})
            save_node_output = outputs.get(_SAVE_NODE, {})
            images = save_node_output.get("images", [])
            if not images:
                continue

            # Fetch the generated image via the /view API endpoint
            img_info = images[0]
            img_filename = img_info["filename"]
            img_subfolder = img_info.get("subfolder", "")
            img_type = img_info.get("type", "output")

            view_url = (
                self._server_url(f"/view")
                + f"?filename={img_filename}&subfolder={img_subfolder}&type={img_type}"
            )

            output_path_str = inputs.get("output_path")
            if output_path_str:
                output_path = Path(output_path_str)
            else:
                output_path = Path(f"generated_{uuid.uuid4().hex[:8]}.png")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                img_resp = request.urlopen(view_url, timeout=60)
                output_path.write_bytes(img_resp.read())
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to download output image: {e}")

            return ToolResult(
                success=True,
                data={
                    "provider": "comfyui_flux",
                    "model": "flux1-dev-fp8",
                    "style": style_name,
                    "prompt": prompt_text,
                    "raw_prompt": raw_prompt,
                    "output": str(output_path),
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "guidance": guidance,
                },
                artifacts=[str(output_path)],
                cost_usd=0.0,
                duration_seconds=round(time.time() - start, 2),
                seed=seed,
                model="flux1-dev-fp8",
            )

        return ToolResult(
            success=False,
            error=f"Timed out waiting for ComfyUI after {timeout}s. "
                  f"Check server logs at /home/pop/ComfyUI/.",
        )
