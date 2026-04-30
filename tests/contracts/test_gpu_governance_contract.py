from __future__ import annotations

from tools.base_tool import BaseTool, ToolRuntime, ToolStatus, ToolTier, ToolStability
from tools.tool_registry import ToolRegistry

from lib.gpu_governance import gpu_lock, mark_failed_after_isolation


class _DummyGpuTool(BaseTool):
    name = "dummy_gpu_tool"
    version = "0.0.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "dummy"
    stability = ToolStability.EXPERIMENTAL
    runtime = ToolRuntime.LOCAL_GPU

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs):
        return 0.0

    def execute(self, inputs):
        raise NotImplementedError


def test_provider_menu_marks_local_gpu_tools_busy_when_lock_held() -> None:
    reg = ToolRegistry()
    reg.register(_DummyGpuTool())
    # Keep this unit test scoped to the dummy tool (avoid auto-discovery).
    reg._discovered_packages.add("tools")  # type: ignore[attr-defined]

    with gpu_lock(tool_name="some_other_gpu_tool", timeout_s=0.0) as lk:
        assert lk.get("acquired") is True
        menu = reg.provider_menu()
        entry = next(e for e in menu["video_generation"]["unavailable"] if e["name"] == "dummy_gpu_tool")
        assert entry["status"] == "busy"
        assert "gpu_busy_reason" in entry


def test_provider_menu_marks_failed_after_isolation_for_local_gpu_tools() -> None:
    reg = ToolRegistry()
    reg.register(_DummyGpuTool())
    reg._discovered_packages.add("tools")  # type: ignore[attr-defined]
    mark_failed_after_isolation("dummy_gpu_tool")

    menu = reg.provider_menu()
    # failed_after_isolation is treated as unavailable bucket but status is distinct
    entry = next(e for e in menu["video_generation"]["unavailable"] if e["name"] == "dummy_gpu_tool")
    assert entry["status"] == "failed_after_isolation"
