"""ComfyUI audio generation via a local/remote ComfyUI server.

Unlike images/videos, audio workflows vary widely across node packs and models.
This tool is therefore intentionally *workflow-first*: provide a ComfyUI
workflow JSON (or path) plus an explicit `output_node` (recommended).

The shared ComfyUIClient will auto-detect artifacts across output nodes when
`output_node` is omitted, and it will download any outputs that expose a
`filename` field (WAV/MP3/OGG/etc) via the standard `/view` endpoint.
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


class ComfyUIAudio(BaseTool):
    name = "comfyui_audio"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "music_generation"
    provider = "comfyui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Start a ComfyUI server and set COMFYUI_SERVER_URL (or legacy COMFYUI_BASE_URL).\n"
        "Default: http://127.0.0.1:8188\n"
        "Then export a ComfyUI audio workflow JSON and pass it via workflow_json/workflow_path."
    )
    agent_skills = ["comfyui", "acestep", "music"]

    capabilities = ["generate_background_music", "generate_sfx", "custom_workflow"]
    supports = {
        "custom_workflow": True,
        "offline": True,
        "seed": True,
    }
    best_for = [
        "running local ComfyUI audio workflows (ACE-Step, Stable Audio, custom node packs)",
        "hardware portability when Python audio model stacks are hard to install",
    ]
    not_good_for = [
        "machines without a running ComfyUI server",
        "users who don't have an exported ComfyUI audio workflow yet",
    ]

    fallback_tools = ["music_gen", "suno_music"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "Human intent string for auditability. Custom workflows may ignore it; "
                    "use workflow_patches to inject it into specific nodes."
                ),
            },
            "seed": {"type": "integer", "description": "Optional seed metadata; only applied if your workflow uses it"},
            "output_path": {"type": "string"},
            "output_dir": {"type": "string"},
            "workflow_json": {"type": "string", "description": "Full ComfyUI workflow JSON (required)"},
            "workflow_path": {"type": "string", "description": "Path to workflow JSON file (required)"},
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

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=16000, vram_mb=8000, disk_mb=1000, network_required=False)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["prompt", "seed", "workflow_path"]
    side_effects = ["writes audio file(s) to disk", "submits a job to a ComfyUI server"]
    user_visible_verification = ["Listen to output audio for quality and artifacts"]

    def get_status(self) -> ToolStatus:
        client = ComfyUIClient(capability=self.capability)
        return ToolStatus.AVAILABLE if client.is_available() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 240.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()

        client = ComfyUIClient(inputs.get("server_url"), capability=self.capability)
        if not client.is_available():
            return ToolResult(success=False, error=client.unavailable_reason())

        if inputs.get("workflow_json") and inputs.get("workflow_path"):
            return ToolResult(success=False, error="Provide only one of workflow_json or workflow_path.")

        if not inputs.get("workflow_json") and not inputs.get("workflow_path"):
            return ToolResult(
                success=False,
                error=(
                    "comfyui_audio requires workflow_json or workflow_path.\n"
                    "Export a workflow from the ComfyUI UI (Save -> API Format) and provide the JSON here."
                ),
            )

        try:
            if inputs.get("workflow_json"):
                workflow = json.loads(inputs["workflow_json"])
                workflow_source = "workflow_json"
            else:
                workflow = ComfyUIClient.load_workflow(Path(inputs["workflow_path"]).expanduser())
                workflow_source = "workflow_path"

            if inputs.get("workflow_patches"):
                if not isinstance(inputs["workflow_patches"], dict):
                    return ToolResult(success=False, error="workflow_patches must be an object/dict.")
                workflow = ComfyUIClient.patch_workflow(workflow, inputs["workflow_patches"])

            workflow_hash = ComfyUIClient.workflow_hash(workflow)

            dest: Path
            seed = inputs.get("seed") or ComfyUIClient.random_seed()
            if inputs.get("output_dir"):
                dest = Path(inputs["output_dir"]).expanduser()
                dest.mkdir(parents=True, exist_ok=True)
            elif inputs.get("output_path"):
                dest = Path(inputs["output_path"]).expanduser()
                dest.parent.mkdir(parents=True, exist_ok=True)
            else:
                dest = Path(f"shared_studio/projects/_smoke/assets/audio/comfyui_audio_{seed}").expanduser()
                dest.parent.mkdir(parents=True, exist_ok=True)

            run = client.run_workflow(
                workflow,
                dest=dest,
                output_node=inputs.get("output_node"),
                timeout_s=int(inputs.get("timeout_seconds", 900)),
                poll_interval_s=float(inputs.get("poll_interval_seconds", 10)),
                wait_for_queue=bool(inputs.get("wait_for_queue", False)),
                queue_timeout_s=int(inputs.get("queue_timeout_seconds", 60)),
                min_vram_free_mb=inputs.get("require_free_vram_mb"),
                min_ram_free_mb=inputs.get("require_free_ram_mb"),
                resource_timeout_s=int(inputs.get("resource_timeout_seconds", 60)),
            )

        except (ComfyUIError, json.JSONDecodeError) as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"ComfyUI audio generation failed: {exc}")

        artifacts = [a["local_path"] for a in run.get("artifacts", []) if a.get("local_path")]
        primary = artifacts[0] if artifacts else None

        provenance = inputs.get("provenance") or {}
        declared_model = provenance.get("declared_model") if isinstance(provenance, dict) else None
        model_label = declared_model or "comfyui/user_workflow"

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
            seed=inputs.get("seed"),
            model=model_label,
        )

