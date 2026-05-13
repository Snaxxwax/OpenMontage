"""Steel Browser web capture tool.

Uses a self-hosted Steel Browser API for source-page screenshots. This is a
web-capture backend, not a general scraper: it writes explicit capture receipts
so production runs can audit which browser backend captured each source.
"""

from __future__ import annotations

import os
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


class SteelBrowserCapture(BaseTool):
    name = "steel_browser_capture"
    version = "0.1.0"
    tier = ToolTier.SOURCE
    capability = "web_capture"
    provider = "steel"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.HYBRID

    dependencies = ["python:requests"]
    install_instructions = (
        "Run Steel Browser on a non-conflicting port, for example:\n"
        "  docker run -d --name steel-browser -p 3020:3000 -p 9323:9223 ghcr.io/steel-dev/steel-browser\n"
        "Then set STEEL_BROWSER_URL=http://127.0.0.1:3020 if using a different endpoint."
    )
    agent_skills = ["web-capture", "source-commentary"]

    capabilities = [
        "capture_web_screenshot",
        "capture_source_receipt",
        "steel_quick_action_screenshot",
    ]
    supports = {
        "full_page": True,
        "viewport_dimensions": True,
        "self_hosted": True,
        "provenance_receipt": True,
    }
    best_for = [
        "source-page screenshot capture for source-commentary videos",
        "web pages that need a managed browser session instead of local headless Chromium",
        "auditable capture backend selection in production runs",
    ]
    not_good_for = [
        "downloading videos or copyrighted media",
        "interactive screen recordings",
        "bypassing access controls or authenticated sources without permission",
    ]

    input_schema = {
        "type": "object",
        "required": ["url", "output_path"],
        "properties": {
            "url": {"type": "string", "description": "URL to capture"},
            "output_path": {"type": "string", "description": "Destination PNG path"},
            "steel_url": {
                "type": "string",
                "description": "Steel API base URL. Defaults to STEEL_BROWSER_URL or http://127.0.0.1:3020.",
            },
            "full_page": {"type": "boolean", "default": False},
            "delay_ms": {"type": "integer", "default": 1500},
            "width": {"type": "integer", "default": 1280},
            "height": {"type": "integer", "default": 720},
            "receipt_path": {
                "type": "string",
                "description": "Optional JSON receipt path. Defaults to output_path with .json suffix.",
            },
            "timeout_seconds": {"type": "integer", "default": 90},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "capture_backend": {"type": "string"},
            "url": {"type": "string"},
            "output_path": {"type": "string"},
            "receipt_path": {"type": "string"},
            "steel_url": {"type": "string"},
            "bytes": {"type": "integer"},
            "content_type": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=100, network_required=True)
    idempotency_key_fields = ["url", "full_page", "width", "height"]
    side_effects = ["writes screenshot file", "writes capture receipt", "calls Steel Browser API"]
    fallback_tools = []
    user_visible_verification = [
        "Open the screenshot and verify the page content is visible",
        "Check the receipt JSON for capture backend and timestamp",
    ]

    def _base_url(self, inputs: dict[str, Any] | None = None) -> str:
        raw = (inputs or {}).get("steel_url") or os.environ.get("STEEL_BROWSER_URL") or "http://127.0.0.1:3020"
        return str(raw).rstrip("/")

    def get_status(self) -> ToolStatus:
        try:
            self.check_dependencies()
            import requests

            response = requests.get(self._base_url() + "/", timeout=3)
            if not response.ok or "Steel Browser API" not in response.text:
                return ToolStatus.UNAVAILABLE
            return ToolStatus.AVAILABLE
        except Exception:
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        try:
            self.check_dependencies()
            import requests
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

        base_url = self._base_url(inputs)
        output_path = Path(inputs["output_path"]).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path = Path(inputs.get("receipt_path") or output_path.with_suffix(".json")).expanduser()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "url": inputs["url"],
            "fullPage": bool(inputs.get("full_page", False)),
            "delay": int(inputs.get("delay_ms", 1500)),
            "dimensions": {
                "width": int(inputs.get("width", 1280)),
                "height": int(inputs.get("height", 720)),
            },
        }

        try:
            response = requests.post(
                base_url + "/v1/screenshot",
                json=payload,
                timeout=int(inputs.get("timeout_seconds", 90)),
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"Steel screenshot request failed: {exc}")

        content_type = response.headers.get("content-type", "")
        if not response.ok:
            detail = response.text[:1000]
            return ToolResult(
                success=False,
                error=f"Steel screenshot failed ({response.status_code}, {content_type}): {detail}",
                data={"steel_url": base_url, "url": inputs["url"], "status_code": response.status_code},
                duration_seconds=round(time.time() - start, 2),
            )

        is_image_bytes = (
            response.content.startswith(b"\x89PNG")
            or response.content.startswith(b"\xff\xd8\xff")
            or response.content.startswith(b"RIFF") and b"WEBP" in response.content[:16]
        )
        if "image" not in content_type.lower() and not is_image_bytes:
            return ToolResult(
                success=False,
                error=f"Steel screenshot returned non-image content ({content_type}): {response.text[:500]}",
                data={"steel_url": base_url, "url": inputs["url"], "status_code": response.status_code},
                duration_seconds=round(time.time() - start, 2),
            )

        output_path.write_bytes(response.content)
        receipt = {
            "capture_backend": "steel_browser",
            "steel_url": base_url,
            "url": inputs["url"],
            "output_path": str(output_path),
            "full_page": bool(inputs.get("full_page", False)),
            "delay_ms": int(inputs.get("delay_ms", 1500)),
            "dimensions": payload["dimensions"],
            "content_type": content_type,
            "bytes": len(response.content),
            "captured_at_unix": time.time(),
        }
        import json

        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        receipt["receipt_path"] = str(receipt_path)

        return ToolResult(
            success=True,
            data=receipt,
            artifacts=[str(output_path), str(receipt_path)],
            duration_seconds=round(time.time() - start, 2),
        )
