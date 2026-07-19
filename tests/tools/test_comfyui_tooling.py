import json
from pathlib import Path



from tools.base_tool import ToolRuntime, ToolTier
from tools.tool_registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[2]


def test_comfyui_infrastructure_tools_are_registry_discoverable():
    reg = ToolRegistry()
    reg.discover("tools")

    status = reg.get("comfyui_status")
    lifecycle = reg.get("comfyui_lifecycle")

    assert status is not None
    assert lifecycle is not None
    assert status.tier == ToolTier.GENERATE
    assert lifecycle.tier == ToolTier.GENERATE
    assert status.runtime == ToolRuntime.LOCAL_GPU
    assert lifecycle.runtime == ToolRuntime.LOCAL_GPU
    assert status.provider == "comfyui"
    assert lifecycle.provider == "comfyui"


def test_comfyui_status_tool_wraps_status_script_with_json(monkeypatch):
    from tools.graphics.comfyui_tools import ComfyUIStatus

    calls = []

    def fake_run(cmd, capture_output, text, timeout, cwd):
        calls.append({"cmd": cmd, "timeout": timeout, "cwd": cwd})

        class Proc:
            returncode = 0
            stdout = json.dumps({"comfyui_api_healthy": True, "managed_container": {"State": "running"}})
            stderr = ""

        return Proc()

    monkeypatch.setattr("tools.graphics.comfyui_tools.subprocess.run", fake_run)

    result = ComfyUIStatus().execute({})

    assert result.success
    assert result.data["comfyui_api_healthy"] is True
    assert result.data["managed_container"]["State"] == "running"
    assert calls[0]["cmd"][-1] == "status"
    assert calls[0]["cwd"] == ROOT


def test_comfyui_lifecycle_tool_only_allows_safe_actions_and_preserves_dry_run(monkeypatch):
    from tools.graphics.comfyui_tools import ComfyUILifecycle

    calls = []

    def fake_run(cmd, capture_output, text, timeout, cwd):
        calls.append(cmd)

        class Proc:
            returncode = 0
            stdout = json.dumps({"ok": True})
            stderr = ""

        return Proc()

    monkeypatch.setattr("tools.graphics.comfyui_tools.subprocess.run", fake_run)

    blocked = ComfyUILifecycle().execute({"action": "stop"})
    assert not blocked.success
    assert "Unsupported ComfyUI lifecycle action" in blocked.error

    ensured = ComfyUILifecycle().execute({"action": "ensure", "dry_run": True})
    assert ensured.success
    assert calls[-1][-2:] == ["ensure", "--dry-run"]

    freed = ComfyUILifecycle().execute({"action": "free"})
    assert freed.success
    assert calls[-1][-1] == "free"
