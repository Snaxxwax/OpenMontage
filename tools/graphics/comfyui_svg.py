"""Local SVG generation via ComfyUI raster-to-vector workflows.

Uses a dedicated ComfyUI instance with SVG custom nodes loaded. The reliable
default is VTracer for multicolor assets; Potrace is exposed for simple
two-tone silhouettes and logos.
"""

from __future__ import annotations

import copy
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any
from urllib import request

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
from tools.graphics.comfyui_image import ComfyUIImage

COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8190
COMFYUI_INPUT_DIR = Path("/home/pop/ComfyUI/input")
WORKFLOW_DIR = Path("/home/pop/ComfyUI/workflows")
VTRACER_WORKFLOW_PATH = WORKFLOW_DIR / "local_svg_vtracer_api.json"
POTRACE_WORKFLOW_PATH = WORKFLOW_DIR / "local_svg_potrace_api.json"


class ComfyUISVG(BaseTool):
    name = "comfyui_svg"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "comfyui_svg"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Start the SVG-enabled ComfyUI API server on localhost:8190.\n"
        "Expected custom nodes: ComfyUI-ToSVG and ComfyUI-ToSVG-Potracer."
    )
    agent_skills = []

    capabilities = ["generate_svg", "vectorize_image", "text_to_vector"]
    supports = {
        "offline": True,
        "svg_output": True,
        "prompt_to_svg": True,
        "image_to_svg": True,
        "seed": True,
    }
    best_for = [
        "local SVG generation for maps and flat explainer graphics",
        "vectorizing locally generated FLUX images into SVG",
        "local-first prototyping without API spend",
    ]
    not_good_for = [
        "exact text rendering",
        "highly precise cartography from a vague text prompt",
        "complex multicolor assets with Potrace mode",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Optional prompt. If image_path is omitted, a local FLUX raster is generated first and then vectorized.",
            },
            "image_path": {
                "type": "string",
                "description": "Optional local raster image to vectorize. Most reliable path for maps and diagrams.",
            },
            "method": {
                "type": "string",
                "enum": ["vtracer", "potrace"],
                "default": "vtracer",
            },
            "style": {"type": "string", "default": "systemic-pulse"},
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 576},
            "seed": {"type": "integer", "default": -1},
            "steps": {"type": "integer", "default": 20},
            "guidance": {"type": "number", "default": 3.5},
            "quantize_colors": {
                "type": "integer",
                "default": 6,
                "description": "Number of colors to quantize before vectorization. Lower values give cleaner SVGs.",
            },
            "output_path": {"type": "string"},
        },
        "anyOf": [
            {"required": ["prompt"]},
            {"required": ["image_path"]},
        ],
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=4000, vram_mb=16000, disk_mb=1000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = [
        "prompt",
        "image_path",
        "method",
        "width",
        "height",
        "seed",
        "steps",
        "guidance",
        "quantize_colors",
    ]
    side_effects = [
        "writes SVG to output_path",
        "may write an intermediate PNG when prompt is used",
        "requires SVG-enabled ComfyUI server on localhost:8190",
    ]
    user_visible_verification = [
        "Inspect the SVG in a vector editor or browser",
        "Check map borders and path cleanliness before using in a video",
    ]

    def _server_url(self, path: str) -> str:
        return f"http://{COMFYUI_HOST}:{COMFYUI_PORT}{path}"

    def get_status(self) -> ToolStatus:
        try:
            with request.urlopen(self._server_url("/object_info"), timeout=5) as resp:
                if resp.status != 200:
                    return ToolStatus.UNAVAILABLE
                object_info = json.loads(resp.read())
            if "TS_ImageToSVGStringColor_Vtracer" in object_info:
                return ToolStatus.AVAILABLE
        except Exception:
            return ToolStatus.UNAVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error=(
                    "SVG-enabled ComfyUI server not running on 127.0.0.1:8190. "
                    + self.install_instructions
                ),
            )

        start = time.time()
        method = inputs.get("method", "vtracer")

        source_image = self._prepare_source_image(inputs)
        if isinstance(source_image, ToolResult):
            return source_image

        output_path = Path(inputs.get("output_path", f"generated_{method}.svg"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            generated_svg = self._run_vector_workflow(
                source_image=source_image,
                method=method,
                output_path=output_path,
                quantize_colors=int(inputs.get("quantize_colors", 6)),
            )
        except Exception as e:
            return ToolResult(success=False, error=f"ComfyUI SVG generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui_svg",
                "method": method,
                "prompt": inputs.get("prompt"),
                "source_image": str(source_image),
                "output": str(generated_svg),
                "quantize_colors": int(inputs.get("quantize_colors", 6)),
            },
            artifacts=[str(generated_svg)],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=inputs.get("seed") if inputs.get("seed", -1) != -1 else None,
            model=f"comfyui-{method}",
        )

    def _prepare_source_image(self, inputs: dict[str, Any]) -> Path | ToolResult:
        image_path = inputs.get("image_path")
        if image_path:
            path = Path(image_path)
            if not path.exists():
                return ToolResult(success=False, error=f"image_path does not exist: {path}")
            return path

        prompt = inputs.get("prompt", "").strip()
        if not prompt:
            return ToolResult(success=False, error="Either prompt or image_path is required.")

        raster_output = Path(inputs.get("output_path", "generated.svg")).with_suffix(".png")
        raster_result = ComfyUIImage().execute(
            {
                "prompt": prompt,
                "style": inputs.get("style", "systemic-pulse"),
                "width": int(inputs.get("width", 1024)),
                "height": int(inputs.get("height", 576)),
                "seed": int(inputs.get("seed", -1)),
                "steps": int(inputs.get("steps", 20)),
                "guidance": float(inputs.get("guidance", 3.5)),
                "output_path": str(raster_output),
            }
        )
        if not raster_result.success:
            return ToolResult(
                success=False,
                error=f"Failed to generate raster source image before SVG conversion: {raster_result.error}",
            )
        return Path(raster_result.data["output"])

    def _run_vector_workflow(
        self,
        *,
        source_image: Path,
        method: str,
        output_path: Path,
        quantize_colors: int,
    ) -> Path:
        workflow_path = VTRACER_WORKFLOW_PATH if method == "vtracer" else POTRACE_WORKFLOW_PATH
        workflow = json.loads(workflow_path.read_text())
        workflow = copy.deepcopy(workflow)

        # Copy source image into ComfyUI input so LoadImage can see it.
        COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        input_name = f"openmontage_{uuid.uuid4().hex[:8]}{source_image.suffix.lower()}"
        comfy_input = COMFYUI_INPUT_DIR / input_name
        shutil.copy2(source_image, comfy_input)

        workflow["1"]["inputs"]["image"] = input_name
        workflow["4"]["inputs"]["filename_prefix"] = output_path.stem
        workflow["4"]["inputs"]["append_timestamp"] = False
        workflow["4"]["inputs"]["custom_output_path"] = str(output_path.parent)

        if method == "vtracer":
            workflow["2"]["inputs"]["colors"] = max(2, quantize_colors)
            workflow["3"]["inputs"]["path_precision"] = 2
            workflow["3"]["inputs"]["mode"] = "polygon"
        else:
            workflow["2"]["inputs"]["colors"] = 2

        prompt_id = self._queue_prompt(workflow)
        self._wait_for_prompt(prompt_id)

        if not output_path.exists():
            raise RuntimeError(f"Expected SVG output not found: {output_path}")
        return output_path

    def _queue_prompt(self, workflow: dict[str, Any]) -> str:
        payload = json.dumps(
            {"prompt": workflow, "client_id": "openmontage-comfyui-svg"}
        ).encode()
        req = request.Request(
            self._server_url("/prompt"),
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["prompt_id"]

    def _wait_for_prompt(self, prompt_id: str, timeout: float = 180.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with request.urlopen(self._server_url(f"/history/{prompt_id}"), timeout=10) as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                status = history[prompt_id].get("status", {})
                if status.get("completed"):
                    if status.get("status_str") != "success":
                        raise RuntimeError(f"ComfyUI workflow did not succeed: {status}")
                    return
            time.sleep(1.5)
        raise RuntimeError(f"Timed out waiting for ComfyUI SVG workflow after {timeout}s.")
