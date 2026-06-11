"""Pipeline-managed ComfyUI infrastructure tools.

These tools intentionally expose only status/lifecycle operations for the
Dockerized ComfyUI service. Creative decisions such as workflow/model/prompt
selection remain in the channel manifest and director skills.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_SCRIPT = ROOT / "scripts" / "comfyui" / "ensure_comfyui_docker.py"


def _run_lifecycle(args: list[str], timeout: int) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["python3", str(LIFECYCLE_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=ROOT,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _json_or_text(stdout: str) -> Any:
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"output": stdout}


class _ComfyUIInfrastructureTool(BaseTool):
    """Shared contract for Dockerized ComfyUI infrastructure tools."""

    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "asset_generation"
    provider = "comfyui"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL_GPU
    dependencies = ["cmd:python3", "cmd:docker"]
    install_instructions = "Use docker-compose.comfyui.yml and scripts/comfyui/ensure_comfyui_docker.py."
    agent_skills = ["comfyui"]
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=10)

    def get_status(self) -> ToolStatus:
        if not LIFECYCLE_SCRIPT.is_file():
            return ToolStatus.UNAVAILABLE
        if shutil.which("python3") is None or shutil.which("docker") is None:
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE


class ComfyUIStatus(_ComfyUIInfrastructureTool):
    """Report Docker/API/GPU/queue state for the managed ComfyUI service."""

    name = "comfyui_status"
    capabilities = ["comfyui_status", "gpu_service_status", "asset_generation_preflight"]
    supports = {
        "side_effect_free": True,
        "docker_managed": True,
        "reports_queue": True,
        "reports_gpu": True,
    }
    best_for = [
        "pipeline preflight before optional source-asset generation",
        "checking whether the managed ComfyUI service is healthy",
    ]
    not_good_for = [
        "choosing prompts, models, workflows, or candidate promotion",
        "final video rendering",
    ]
    input_schema = {
        "type": "object",
        "properties": {
            "timeout_seconds": {"type": "integer", "default": 60},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "comfyui_api_healthy": {"type": "boolean"},
            "managed_container": {"type": ["object", "null"]},
            "gpu": {"type": "object"},
        },
    }
    side_effects: list[str] = []
    user_visible_verification = [
        "Confirm comfyui_api_healthy is true before generation",
        "Confirm queue_running and queue_pending are empty or expected",
    ]

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 2.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        timeout = int(inputs.get("timeout_seconds", 60))
        code, stdout, stderr = _run_lifecycle(["status"], timeout)
        payload = _json_or_text(stdout)
        if code != 0:
            return ToolResult(
                success=False,
                data={"stdout": payload, "stderr": stderr},
                error=f"ComfyUI status failed with exit code {code}: {stderr or stdout}",
                duration_seconds=round(time.time() - start, 2),
            )
        data = payload if isinstance(payload, dict) else {"status": payload}
        return ToolResult(success=True, data=data, duration_seconds=round(time.time() - start, 2))


class ComfyUILifecycle(_ComfyUIInfrastructureTool):
    """Run safe lifecycle actions for the managed ComfyUI Docker service."""

    name = "comfyui_lifecycle"
    capabilities = ["comfyui_ensure", "comfyui_free", "gpu_service_lifecycle"]
    supports = {
        "actions": ["status", "ensure", "free"],
        "dry_run": True,
        "docker_managed": True,
        "safe_gpu_handoff_policy": True,
    }
    best_for = [
        "reusing or starting the managed ComfyUI Docker service after approval",
        "freeing ComfyUI model VRAM after an approved generation batch",
    ]
    not_good_for = [
        "stopping arbitrary GPU processes",
        "creative/provider/model/workflow selection",
        "render-stage execution",
    ]
    input_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {"type": "string", "enum": ["status", "ensure", "free"]},
            "dry_run": {"type": "boolean", "default": False},
            "allow_preserved_stop": {"type": "boolean", "default": False},
            "timeout_seconds": {"type": "integer", "default": 240},
        },
    }
    output_schema = {"type": "object"}
    side_effects = [
        "ensure may start the managed ComfyUI Docker container",
        "free unloads ComfyUI models and frees VRAM through the ComfyUI API",
    ]
    user_visible_verification = [
        "Run comfyui_status after ensure to confirm API health",
        "Review reported protected/unknown GPU consumers before approving ensure",
    ]

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        action = inputs.get("action")
        if action == "ensure":
            return 30.0
        return 3.0

    def dry_run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        action = inputs.get("action", "ensure")
        return {
            "tool": self.name,
            "action": action,
            "estimated_cost_usd": 0.0,
            "estimated_runtime_seconds": self.estimate_runtime({"action": action}),
            "status": self.get_status().value,
            "would_execute": action in {"status", "ensure", "free"},
            "side_effects": self.side_effects if action in {"ensure", "free"} else [],
        }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        action = str(inputs.get("action", "")).strip()
        if action not in {"status", "ensure", "free"}:
            return ToolResult(
                success=False,
                error=f"Unsupported ComfyUI lifecycle action: {action!r}. Allowed: status, ensure, free.",
            )

        args = [action]
        if action == "ensure" and bool(inputs.get("dry_run", False)):
            args.append("--dry-run")
        if action == "ensure" and bool(inputs.get("allow_preserved_stop", False)):
            args.append("--allow-preserved-stop")

        timeout = int(inputs.get("timeout_seconds", 240))
        code, stdout, stderr = _run_lifecycle(args, timeout)
        payload = _json_or_text(stdout)
        if code != 0:
            return ToolResult(
                success=False,
                data={"action": action, "stdout": payload, "stderr": stderr},
                error=f"ComfyUI lifecycle action {action!r} failed with exit code {code}: {stderr or stdout}",
                duration_seconds=round(time.time() - start, 2),
            )
        data = payload if isinstance(payload, dict) else {"output": payload}
        data.setdefault("action", action)
        return ToolResult(success=True, data=data, duration_seconds=round(time.time() - start, 2))
