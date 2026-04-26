"""ComfyUI video generation via a local/remote ComfyUI server.

Default (bundled) workflows:
- WAN 2.2 14B 4-step text-to-video
- WAN 2.2 14B 4-step image-to-video

For arbitrary models/workflows, provide `workflow_json`/`workflow_path` plus an
explicit `output_node` (recommended) and, for I2V, a `reference_image_patch`
so the tool knows which LoadImage node to patch with the uploaded filename.
"""

from __future__ import annotations

import json
import time
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


_WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "_comfyui" / "workflows"

_BUNDLED_OUTPUT_NODE_T2V = "16"
_BUNDLED_OUTPUT_NODE_I2V = "108"

_REQUIRED_MODELS_COMMON = [
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
]
_BUNDLED_REQUIRED_MODELS_T2V = [
    *_REQUIRED_MODELS_COMMON,
    "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
    "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
    "wan2.2_vae.safetensors",
    "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
    "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
]
_BUNDLED_REQUIRED_MODELS_I2V = [
    *_REQUIRED_MODELS_COMMON,
    "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
    "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
    "wan_2.1_vae.safetensors",
    "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
    "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
]


class ComfyUIVideo(BaseTool):
    name = "comfyui_video"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "comfyui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Start a ComfyUI server and set COMFYUI_SERVER_URL (or legacy COMFYUI_BASE_URL).\n"
        "Default: http://127.0.0.1:8188"
    )
    agent_skills = ["comfyui", "ltx2"]

    capabilities = ["text_to_video", "image_to_video", "custom_workflow"]
    def __init__(self) -> None:
        self._supports_cache: dict[str, Any] | None = None
        self._supports_cache_at: float | None = None

    def _bundled_op_readiness(self, *, cache_ttl_s: int = 15) -> dict[str, bool]:
        now = time.time()
        if self._supports_cache and self._supports_cache_at and (now - self._supports_cache_at) < cache_ttl_s:
            return {
                "text_to_video": bool(self._supports_cache.get("text_to_video")),
                "image_to_video": bool(self._supports_cache.get("image_to_video")),
            }

        client = ComfyUIClient(capability=self.capability)
        if not client.is_available():
            readiness = {"text_to_video": False, "image_to_video": False}
        else:
            _, missing_t2v = client.check_models(_BUNDLED_REQUIRED_MODELS_T2V)
            _, missing_i2v = client.check_models(_BUNDLED_REQUIRED_MODELS_I2V)
            readiness = {
                "text_to_video": not bool(missing_t2v),
                "image_to_video": not bool(missing_i2v),
            }

        self._supports_cache = readiness
        self._supports_cache_at = now
        return readiness

    @property
    def supports(self) -> dict[str, Any]:
        readiness = self._bundled_op_readiness()
        return {
            "seed": True,
            "reference_image": True,
            "custom_workflow": True,
            "offline": True,
            # Explicit per-operation readiness for selector filtering.
            # These reflect bundled/default workflow readiness (prompt-only usage).
            "text_to_video": readiness["text_to_video"],
            "image_to_video": readiness["image_to_video"],
            "bundled_t2v_ready": readiness["text_to_video"],
            "bundled_i2v_ready": readiness["image_to_video"],
        }
    best_for = [
        "local GPU video generation without API costs",
        "hardware portability when diffusers/PyTorch is unavailable",
        "WAN 2.2 14B i2v/t2v via bundled workflows (4-step accelerated)",
    ]
    not_good_for = ["machines without a running ComfyUI server", "CPU-only machines"]

    fallback_tools = ["wan_video", "hunyuan_video", "ltx_video_local", "kling_video", "video_selector"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video"],
                "default": "text_to_video",
            },
            "reference_image_path": {"type": "string", "description": "Local path for image_to_video"},
            "reference_image_url": {"type": "string", "description": "URL for image_to_video (downloaded then uploaded)"},
            "width": {"type": "integer", "default": 832},
            "height": {"type": "integer", "default": 480},
            "num_frames": {"type": "integer", "default": 81, "description": "81 frames ~= 5s at 16fps"},
            "fps": {"type": "integer", "default": 16},
            "seed": {"type": "integer", "description": "Random if omitted"},
            "output_path": {"type": "string"},
            "output_dir": {"type": "string"},
            "workflow_json": {"type": "string", "description": "Full ComfyUI workflow JSON (overrides bundled workflow)"},
            "workflow_path": {"type": "string", "description": "Path to workflow JSON file (overrides bundled workflow)"},
            "workflow_patches": {
                "type": "object",
                "description": "Node patches applied after loading the workflow (node_id -> {input: value})",
                "additionalProperties": True,
            },
            "output_node": {
                "type": "string",
                "description": (
                    "Optional node id to download outputs from. Strongly recommended for custom workflows. "
                    "If omitted, artifacts are auto-detected across all output nodes."
                ),
            },
            "reference_image_patch": {
                "type": "object",
                "description": (
                    "For custom workflows + image_to_video: where to patch the uploaded image filename "
                    "(e.g. {\"node_id\": \"97\", \"input_key\": \"image\"})."
                ),
                "properties": {
                    "node_id": {"type": "string"},
                    "input_key": {"type": "string", "default": "image"},
                },
                "additionalProperties": True,
            },
            "server_url": {"type": "string"},
            "timeout_seconds": {"type": "integer", "default": 900},
            "poll_interval_seconds": {"type": "number", "default": 10},
            "wait_for_queue": {"type": "boolean", "default": False},
            "queue_timeout_seconds": {"type": "integer", "default": 60},
            "require_free_vram_mb": {"type": "integer"},
            "require_free_ram_mb": {"type": "integer"},
            "resource_timeout_seconds": {"type": "integer", "default": 60},
            "provenance": {
                "type": "object",
                "description": "Optional provenance for workflow overrides (used for auditability).",
                "properties": {
                    "declared_model": {"type": "string"},
                    "workflow_name": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "additionalProperties": True,
            },
        },
    }

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=32000, vram_mb=16000, disk_mb=2000, network_required=False)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["prompt", "operation", "width", "height", "num_frames", "seed", "workflow_path"]
    side_effects = ["writes video file(s) to disk", "submits a job to a ComfyUI server"]
    user_visible_verification = ["Watch the generated clip(s) for motion coherence and artifacts"]

    def get_status(self) -> ToolStatus:
        client = ComfyUIClient(capability=self.capability)
        if not client.is_available():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        operation = inputs.get("operation", "text_to_video")
        return 240.0 if operation == "text_to_video" else 210.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()

        client = ComfyUIClient(inputs.get("server_url"), capability=self.capability)
        if not client.is_available():
            return ToolResult(success=False, error=client.unavailable_reason())

        operation = inputs.get("operation", "text_to_video")
        seed = inputs.get("seed") or ComfyUIClient.random_seed()

        workflow_source = "bundled"
        workflow_hash = None

        try:
            if inputs.get("workflow_json") or inputs.get("workflow_path"):
                workflow_source = "workflow_json" if inputs.get("workflow_json") else "workflow_path"
                if inputs.get("workflow_json") and inputs.get("workflow_path"):
                    return ToolResult(success=False, error="Provide only one of workflow_json or workflow_path.")
                if inputs.get("workflow_json"):
                    workflow = json.loads(inputs["workflow_json"])
                else:
                    workflow = ComfyUIClient.load_workflow(Path(inputs["workflow_path"]).expanduser())

                if inputs.get("workflow_patches"):
                    if not isinstance(inputs["workflow_patches"], dict):
                        return ToolResult(success=False, error="workflow_patches must be an object/dict.")
                    workflow = ComfyUIClient.patch_workflow(workflow, inputs["workflow_patches"])

                # For custom workflows, we can optionally upload and patch the reference image.
                if operation == "image_to_video":
                    ref_path = inputs.get("reference_image_path")
                    ref_url = inputs.get("reference_image_url")
                    if ref_path or ref_url:
                        local_ref = self._resolve_reference_image(ref_path, ref_url, seed)
                        uploaded = client.upload_image(local_path=local_ref, name=f"om_ref_{seed}.png")
                        patch = inputs.get("reference_image_patch") or {}
                        if not isinstance(patch, dict) or not patch.get("node_id"):
                            return ToolResult(
                                success=False,
                                error=(
                                    "Custom workflow image_to_video requires reference_image_patch "
                                    "(node_id + input_key) or an equivalent workflow_patches entry."
                                ),
                            )
                        node_id = str(patch.get("node_id"))
                        input_key = str(patch.get("input_key") or "image")
                        workflow = ComfyUIClient.patch_workflow(workflow, {node_id: {input_key: uploaded}})

                output_node = inputs.get("output_node")

            else:
                # Bundled workflow mode (WAN 2.2 4-step)
                if operation == "image_to_video":
                    workflow, output_node = self._build_bundled_i2v(inputs, client, seed)
                else:
                    workflow, output_node = self._build_bundled_t2v(inputs, client, seed)

            workflow_hash = ComfyUIClient.workflow_hash(workflow)

            timeout_s = int(inputs.get("timeout_seconds", 900))
            poll_interval_s = float(inputs.get("poll_interval_seconds", 10))
            wait_for_queue = bool(inputs.get("wait_for_queue", False))
            queue_timeout_s = int(inputs.get("queue_timeout_seconds", 60))

            dest: Path
            if inputs.get("output_dir"):
                dest = Path(inputs["output_dir"]).expanduser()
                dest.mkdir(parents=True, exist_ok=True)
            elif inputs.get("output_path"):
                dest = Path(inputs["output_path"]).expanduser()
                dest.parent.mkdir(parents=True, exist_ok=True)
            else:
                dest = Path(f"projects/_smoke/assets/video/comfyui_video_{operation}_{seed}").expanduser()
                dest.parent.mkdir(parents=True, exist_ok=True)

            run = client.run_workflow(
                workflow,
                dest=dest,
                output_node=output_node,
                timeout_s=timeout_s,
                poll_interval_s=poll_interval_s,
                wait_for_queue=wait_for_queue,
                queue_timeout_s=queue_timeout_s,
                min_vram_free_mb=inputs.get("require_free_vram_mb"),
                min_ram_free_mb=inputs.get("require_free_ram_mb"),
                resource_timeout_s=int(inputs.get("resource_timeout_seconds", 60)),
            )

        except (ComfyUIError, json.JSONDecodeError) as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"ComfyUI video generation failed: {exc}")

        artifacts = [a["local_path"] for a in run.get("artifacts", []) if a.get("local_path")]
        primary = artifacts[0] if artifacts else None

        provenance = inputs.get("provenance") or {}
        declared_model = provenance.get("declared_model") if isinstance(provenance, dict) else None
        model_label = "wan2.2-14b-fp8-4step" if workflow_source == "bundled" else (declared_model or "comfyui/user_workflow")

        num_frames = int(inputs.get("num_frames", 81))
        fps = int(inputs.get("fps", 16))

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui",
                "model": model_label,
                "prompt": inputs["prompt"],
                "operation": operation,
                "workflow_source": workflow_source,
                "workflow_hash": workflow_hash,
                "output_node": inputs.get("output_node") if workflow_source != "bundled" else output_node,
                "output_nodes": run.get("output_nodes", []),
                "prompt_id": run.get("prompt_id"),
                "width": int(inputs.get("width", 832 if operation == "text_to_video" else 640)),
                "height": int(inputs.get("height", 480 if operation == "text_to_video" else 640)),
                "num_frames": num_frames,
                "fps": fps,
                "duration_seconds": round(num_frames / max(fps, 1), 2),
                "output": primary,
                "outputs": artifacts,
            },
            artifacts=artifacts,
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=model_label,
        )

    # ------------------------------------------------------------------
    # Bundled workflow builders
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_reference_image(ref_path: str | None, ref_url: str | None, seed: int) -> Path:
        if ref_path:
            p = Path(ref_path).expanduser()
            if not p.is_file():
                raise FileNotFoundError(f"reference_image_path not found: {p}")
            return p
        if ref_url:
            r = requests.get(ref_url, timeout=60)
            r.raise_for_status()
            tmp = Path(f"projects/_smoke/assets/images/comfyui_ref_{seed}.png").expanduser()
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(r.content)
            return tmp
        raise ComfyUIError("image_to_video requires reference_image_path or reference_image_url")

    def _build_bundled_i2v(
        self,
        inputs: dict[str, Any],
        client: ComfyUIClient,
        seed: int,
    ) -> tuple[dict[str, Any], str]:
        _, missing = client.check_models(_BUNDLED_REQUIRED_MODELS_I2V)
        if missing:
            raise ComfyUIError(
                f"Bundled WAN I2V workflow requires missing models: {', '.join(missing)}"
            )

        width = int(inputs.get("width", 640))
        height = int(inputs.get("height", 640))
        num_frames = int(inputs.get("num_frames", 81))
        fps = int(inputs.get("fps", 16))

        local_ref = self._resolve_reference_image(inputs.get("reference_image_path"), inputs.get("reference_image_url"), seed)
        uploaded = client.upload_image(local_path=local_ref, name=f"om_{seed}.png")

        output_path = Path(inputs.get("output_path", f"projects/_smoke/assets/video/comfyui_wan22_i2v_{seed}.mp4")).expanduser()

        workflow = ComfyUIClient.load_workflow(_WORKFLOWS_DIR / "wan22-i2v-4step.json")
        workflow = ComfyUIClient.patch_workflow(
            workflow,
            {
                "93": {"text": inputs["prompt"]},
                "97": {"image": uploaded},
                "98": {"width": width, "height": height, "length": num_frames},
                "86": {"noise_seed": seed},
                "94": {"fps": fps},
                "108": {"filename_prefix": output_path.stem},
            },
        )
        return workflow, _BUNDLED_OUTPUT_NODE_I2V

    def _build_bundled_t2v(
        self,
        inputs: dict[str, Any],
        client: ComfyUIClient,
        seed: int,
    ) -> tuple[dict[str, Any], str]:
        _, missing = client.check_models(_BUNDLED_REQUIRED_MODELS_T2V)
        if missing:
            raise ComfyUIError(
                f"Bundled WAN T2V workflow requires missing models: {', '.join(missing)}"
            )

        width = int(inputs.get("width", 832))
        height = int(inputs.get("height", 480))
        num_frames = int(inputs.get("num_frames", 81))
        fps = int(inputs.get("fps", 16))

        output_path = Path(inputs.get("output_path", f"projects/_smoke/assets/video/comfyui_wan22_t2v_{seed}.mp4")).expanduser()

        workflow = ComfyUIClient.load_workflow(_WORKFLOWS_DIR / "wan22-t2v-4step.json")
        workflow = ComfyUIClient.patch_workflow(
            workflow,
            {
                "2": {"text": inputs["prompt"]},
                "11": {"width": width, "height": height, "batch_size": num_frames},
                "12": {"noise_seed": seed},
                "15": {"fps": fps},
                "16": {"filename_prefix": output_path.stem},
            },
        )
        return workflow, _BUNDLED_OUTPUT_NODE_T2V
