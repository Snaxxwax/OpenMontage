from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStatus, ToolTier, ToolStability
from tools.video.video_selector import VideoSelector
from tools.graphics.image_selector import ImageSelector
from tools.audio.tts_selector import TTSSelector


@dataclass
class _FakeScore:
    def explain(self) -> str:
        return "fake-score"

    def to_dict(self) -> dict[str, Any]:
        return {"weighted_score": 1.0}


class _ApiOnlyVideoTool(BaseTool):
    name = "api_video"
    version = "0.0.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "api_provider"
    stability = ToolStability.EXPERIMENTAL
    runtime = ToolRuntime.API

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 1.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, data={"provider": self.provider})


class _LocalVideoTool(_ApiOnlyVideoTool):
    name = "local_video"
    provider = "local_provider"
    runtime = ToolRuntime.LOCAL

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0


class _ApiOnlyImageTool(_ApiOnlyVideoTool):
    capability = "image_generation"
    name = "api_image"


class _LocalImageTool(_LocalVideoTool):
    capability = "image_generation"
    name = "local_image"


class _ApiOnlyTtsTool(_ApiOnlyVideoTool):
    capability = "tts"
    name = "api_tts"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        out = Path(inputs.get("output_path") or "out.wav")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"ok")
        return ToolResult(success=True, data={"provider": self.provider}, artifacts=[str(out)])


class _LocalTtsTool(_LocalVideoTool):
    capability = "tts"
    name = "local_tts"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        out = Path(inputs.get("output_path") or "out.wav")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"ok")
        return ToolResult(success=True, data={"provider": self.provider}, artifacts=[str(out)])


def test_auto_mode_api_only_fails_without_allow_paid(monkeypatch, tmp_path: Path) -> None:
    selector = VideoSelector()
    api = _ApiOnlyVideoTool()
    monkeypatch.setattr(selector, "_providers", lambda: [api])

    result = selector.execute({"prompt": "x", "output_path": str(tmp_path / "o.mp4"), "allow_paid_providers": False})
    assert result.success is False
    assert "Paid/API fallback requires allow_paid_providers=true" in (result.error or "")


def test_auto_mode_prefers_local_over_api(monkeypatch, tmp_path: Path) -> None:
    selector = VideoSelector()
    api = _ApiOnlyVideoTool()
    local = _LocalVideoTool()
    monkeypatch.setattr(selector, "_providers", lambda: [api, local])

    result = selector.execute({"prompt": "x", "output_path": str(tmp_path / "o.mp4"), "allow_paid_providers": False})
    assert result.success is True
    assert result.data.get("selected_provider") == "local_provider"


def test_explicit_api_preferred_requires_allow_paid(monkeypatch, tmp_path: Path) -> None:
    selector = ImageSelector()
    api = _ApiOnlyImageTool()
    monkeypatch.setattr(selector, "_providers", lambda: [api])

    result = selector.execute({"prompt": "x", "output_path": str(tmp_path / "o.png"), "preferred_provider": "api_provider"})
    assert result.success is False
    assert "allow_paid_providers=true" in (result.error or "")


def test_explicit_api_preferred_allowed_when_approved(monkeypatch, tmp_path: Path) -> None:
    selector = TTSSelector()
    api = _ApiOnlyTtsTool()
    monkeypatch.setattr(selector, "_providers", lambda: [api])
    monkeypatch.setattr(selector, "_select_best_tool", lambda inputs, candidates, ctx: (api, _FakeScore()))

    result = selector.execute(
        {"text": "hello", "output_path": str(tmp_path / "o.wav"), "preferred_provider": "api_provider", "allow_paid_providers": True}
    )
    assert result.success is True
