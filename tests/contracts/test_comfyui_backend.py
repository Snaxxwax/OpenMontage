"""Contract tests for the ComfyUI backend abstraction tools.

These tests are intentionally offline-friendly: they do not require a running
ComfyUI server. They focus on:
- tool contract fields (schemas, metadata)
- selector filtering behavior when a provider publishes explicit readiness
- client workflow patching helpers
"""

from __future__ import annotations

import pytest

from tools._comfyui.client import ComfyUIClient, ComfyUIError
from tools.audio.comfyui_audio import ComfyUIAudio
from tools.base_tool import BaseTool
from tools.graphics.comfyui_image import ComfyUIImage
from tools.graphics.image_selector import ImageSelector
from tools.video.comfyui_wan_video import ComfyUIWanVideo
from tools.video.comfyui_video import ComfyUIVideo
from tools.video.video_selector import VideoSelector


TOOLS = [ComfyUIImage, ComfyUIVideo, ComfyUIAudio]


@pytest.mark.parametrize("cls", TOOLS, ids=lambda c: c.name)
def test_tools_are_base_tools(cls) -> None:
    assert issubclass(cls, BaseTool)
    tool = cls()
    assert tool.name
    assert tool.provider == "comfyui"
    assert tool.capability in {"image_generation", "video_generation", "music_generation"}


@pytest.mark.parametrize("cls", TOOLS, ids=lambda c: c.name)
def test_workflow_override_contract_fields_present(cls) -> None:
    tool = cls()
    props = tool.input_schema.get("properties", {})
    # All ComfyUI tools must expose a consistent override contract.
    assert "workflow_json" in props
    assert "workflow_path" in props
    assert "workflow_patches" in props
    assert "output_node" in props
    assert "server_url" in props


def test_comfyui_audio_requires_workflow_override(monkeypatch) -> None:
    # Make server look reachable so we can test the contract error path.
    monkeypatch.setattr(ComfyUIClient, "is_available", lambda self: True)
    tool = ComfyUIAudio()
    result = tool.execute({"prompt": "test"})
    assert result.success is False
    assert result.error
    assert "requires workflow_json or workflow_path" in result.error


def test_video_selector_respects_explicit_operation_readiness(monkeypatch) -> None:
    # Force ComfyUIClient.is_available() to be False quickly (no network).
    import tools._comfyui.client as comfy_mod

    monkeypatch.setattr(comfy_mod.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no server")))

    sel = VideoSelector()
    providers = sel._providers()
    candidates = sel._filter_candidates({"operation": "text_to_video"}, providers)
    assert "comfyui" not in {t.provider for t in candidates}


def test_image_selector_respects_explicit_text_to_image_readiness(monkeypatch) -> None:
    import tools._comfyui.client as comfy_mod

    monkeypatch.setattr(comfy_mod.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no server")))

    sel = ImageSelector()
    providers = sel._providers()
    candidates = sel._filter_candidates({"prompt": "x", "generation_mode": "generate"}, providers)
    assert "comfyui" not in {t.provider for t in candidates}


def test_patch_workflow_missing_node_raises() -> None:
    workflow = {"1": {"class_type": "Anything", "inputs": {"x": 1}}}
    with pytest.raises(ComfyUIError, match="not found"):
        ComfyUIClient.patch_workflow(workflow, {"999": {"x": 2}})


def test_comfyui_wan_video_exposes_queue_and_resource_controls() -> None:
    tool = ComfyUIWanVideo()
    props = tool.input_schema.get("properties", {})
    assert "wait_for_queue" in props
    assert "queue_timeout_seconds" in props
    assert "require_free_vram_mb" in props
    assert "require_free_ram_mb" in props
    assert "resource_timeout_seconds" in props
    assert tool.supports.get("text_to_video") is False
    assert tool.supports.get("image_to_video") is True


def test_comfyui_wan_video_unavailable_uses_client_reason(monkeypatch) -> None:
    monkeypatch.setattr(ComfyUIClient, "is_available", lambda self: False)
    monkeypatch.setattr(ComfyUIClient, "unavailable_reason", lambda self: "custom unavailable")

    tool = ComfyUIWanVideo()
    result = tool.execute({"prompt": "test"})
    assert result.success is False
    assert result.error == "custom unavailable"


def test_video_selector_excludes_comfyui_wan_by_default() -> None:
    sel = VideoSelector()
    providers = sel._providers()
    if not any(t.provider == "comfyui_wan" for t in providers):
        pytest.skip("comfyui_wan provider not discovered")

    candidates = sel._filter_candidates({"prompt": "x", "operation": "image_to_video"}, providers)
    assert "comfyui_wan" not in {t.provider for t in candidates}


def test_video_selector_allows_comfyui_wan_when_explicit() -> None:
    sel = VideoSelector()
    providers = sel._providers()
    if not any(t.provider == "comfyui_wan" for t in providers):
        pytest.skip("comfyui_wan provider not discovered")

    candidates = sel._filter_candidates(
        {"prompt": "x", "operation": "image_to_video", "preferred_provider": "comfyui_wan"},
        providers,
    )
    assert "comfyui_wan" in {t.provider for t in candidates}
