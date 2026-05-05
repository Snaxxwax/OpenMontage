"""ComfyUI image generation via a local/remote ComfyUI server.

This is a *backend abstraction* tool: it can run the bundled "flux2-txt2img"
workflow out of the box, and it can run arbitrary user-provided workflows via
`workflow_json`/`workflow_path` + `output_node`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

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

# Models referenced by the bundled flux2-txt2img workflow template.
_BUNDLED_REQUIRED_MODELS = [
    "flux2-dev-nvfp4.safetensors",
    "mistral_3_small_flux2_fp4_mixed.safetensors",
    "flux2-vae.safetensors",
]


class ComfyUIImage(BaseTool):
    name = "comfyui_image"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "comfyui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []  # validated dynamically via server reachability
    install_instructions = (
        "Start a ComfyUI server and set COMFYUI_SERVER_URL (or legacy COMFYUI_BASE_URL).\n"
        "Default: http://127.0.0.1:8188"
    )
    agent_skills = ["comfyui", "flux-best-practices"]

    capabilities = ["text_to_image", "custom_workflow"]
    def __init__(self) -> None:
        self._supports_cache: dict[str, Any] | None = None
        self._supports_cache_at: float | None = None

    def _bundled_ready(self, *, cache_ttl_s: int = 15) -> bool:
        now = time.time()
        if self._supports_cache is not None and self._supports_cache_at and (now - self._supports_cache_at) < cache_ttl_s:
            return bool(self._supports_cache.get("bundled_flux2_ready"))

        client = ComfyUIClient(capability=self.capability)
        if not client.is_available():
            ready = False
        else:
            _, missing = client.check_models(_BUNDLED_REQUIRED_MODELS)
            ready = not bool(missing)

        self._supports_cache = {"bundled_flux2_ready": ready}
        self._supports_cache_at = now
        return ready

    @property
    def supports(self) -> dict[str, Any]:
        bundled_ready = self._bundled_ready()
        return {
            "seed": True,
            "custom_size": True,
            "custom_workflow": True,
            "offline": True,
            # Explicit readiness so selectors can avoid routing to the bundled
            # default when required models aren't installed (unless workflow override is provided).
            "text_to_image": bundled_ready,
            "bundled_flux2_ready": bundled_ready,
        }
    best_for = [
        "local GPU image generation without API costs",
        "hardware portability when diffusers/PyTorch is unavailable",
        "running arbitrary community ComfyUI workflows (explicit output_node recommended)",
    ]
    not_good_for = ["machines without a running ComfyUI server", "CPU-only machines"]

    fallback_tools = ["flux_image", "local_diffusion", "openai_image", "image_gen"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Text prompt for generation"},
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 1024},
            "steps": {"type": "integer", "default": 20},
            "guidance": {"type": "number", "default": 3.5},
            "seed": {"type": "integer", "description": "Random if omitted"},
            "output_path": {"type": "string", "description": "Local output file path (single or base name)"},
            "output_dir": {"type": "string", "description": "Local output directory (downloads keep server filenames)"},
            "workflow_json": {"type": "string", "description": "Full ComfyUI workflow JSON (overrides bundled workflow)"},
            "workflow_path": {"type": "string", "description": "Path to a workflow JSON file (overrides bundled workflow)"},
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
            "server_url": {"type": "string", "description": "Override COMFYUI_SERVER_URL for this call"},
            "timeout_seconds": {"type": "integer", "default": 600},
            "poll_interval_seconds": {"type": "number", "default": 5},
            "wait_for_queue": {"type": "boolean", "default": False},
            "queue_timeout_seconds": {"type": "integer", "default": 60},
            "require_free_vram_mb": {"type": "integer", "description": "Optional resource gate (best-effort)"},
            "require_free_ram_mb": {"type": "integer", "description": "Optional resource gate (best-effort)"},
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

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=8000, vram_mb=8000, disk_mb=500, network_required=False)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["prompt", "width", "height", "steps", "seed", "workflow_path"]
    side_effects = ["writes image file(s) to disk", "submits a job to a ComfyUI server"]
    user_visible_verification = ["Inspect generated image(s) for quality and prompt adherence"]

    def get_status(self) -> ToolStatus:
        client = ComfyUIClient(capability=self.capability)
        if not client.is_available():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return float(inputs.get("steps", 20)) * 1.5

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()

        client = ComfyUIClient(inputs.get("server_url"), capability=self.capability)
        if not client.is_available():
            return ToolResult(success=False, error=client.unavailable_reason())

        # Resolve workflow
        workflow_source = "bundled"
        workflow_hash = None
        seed = inputs.get("seed") or ComfyUIClient.random_seed()

        try:
            if inputs.get("workflow_json") or inputs.get("workflow_path"):
                if inputs.get("workflow_json") and inputs.get("workflow_path"):
                    return ToolResult(
                        success=False,
                        error="Provide only one of workflow_json or workflow_path (not both).",
                    )
                if inputs.get("workflow_json"):
                    workflow = json.loads(inputs["workflow_json"])
                    workflow_source = "workflow_json"
                else:
                    workflow = ComfyUIClient.load_workflow(Path(inputs["workflow_path"]).expanduser())
                    workflow_source = "workflow_path"
            else:
                _, missing = client.check_models(_BUNDLED_REQUIRED_MODELS)
                if missing:
                    raise ComfyUIError(
                        "Bundled FLUX2 workflow is selected but required models are missing: "
                        + ", ".join(missing)
                    )
                workflow = ComfyUIClient.load_workflow(_WORKFLOWS_DIR / "flux2-txt2img.json")
                # Patch bundled workflow with prompt + params
                width = int(inputs.get("width", 1024))
                height = int(inputs.get("height", 1024))
                steps = int(inputs.get("steps", 20))
                guidance = float(inputs.get("guidance", 3.5))
                out_path = Path(inputs.get("output_path", f"shared_studio/projects/_smoke/assets/images/comfyui_flux2_{seed}")).expanduser()
                workflow = ComfyUIClient.patch_workflow(
                    workflow,
                    {
                        "4": {"text": inputs["prompt"]},
                        "5": {"guidance": guidance},
                        "6": {"width": width, "height": height, "batch_size": 1},
                        "7": {"noise_seed": seed},
                        "10": {"steps": steps, "width": width, "height": height},
                        "13": {"filename_prefix": out_path.stem},
                    },
                )

            # Apply user patches last (for both bundled + override workflows)
            if inputs.get("workflow_patches"):
                if not isinstance(inputs["workflow_patches"], dict):
                    return ToolResult(success=False, error="workflow_patches must be an object/dict.")
                workflow = ComfyUIClient.patch_workflow(workflow, inputs["workflow_patches"])

            workflow_hash = ComfyUIClient.workflow_hash(workflow)

            output_node = inputs.get("output_node")
            timeout_s = int(inputs.get("timeout_seconds", 600))
            poll_interval_s = float(inputs.get("poll_interval_seconds", 5))
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
                dest = Path(f"shared_studio/projects/_smoke/assets/images/comfyui_image_{seed}").expanduser()
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
            return ToolResult(success=False, error=f"ComfyUI image generation failed: {exc}")

        artifacts = [a["local_path"] for a in run.get("artifacts", []) if a.get("local_path")]
        primary = artifacts[0] if artifacts else None

        provenance = inputs.get("provenance") or {}
        declared_model = provenance.get("declared_model") if isinstance(provenance, dict) else None

        # Only claim the bundled model name when we actually used the bundled template.
        model_label = "flux2-dev-nvfp4" if workflow_source == "bundled" else (declared_model or "comfyui/user_workflow")

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui",
                "model": model_label,
                "prompt": inputs["prompt"],
                "workflow_source": workflow_source,
                "workflow_hash": workflow_hash,
                "output_node": inputs.get("output_node"),
                "output_nodes": run.get("output_nodes", []),
                "prompt_id": run.get("prompt_id"),
                "output": primary,
                "outputs": artifacts,
            },
            artifacts=artifacts,
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=model_label,
        )
