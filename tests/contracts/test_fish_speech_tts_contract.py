from __future__ import annotations

from tools.audio.fish_speech_tts import FishSpeechTTS
from tools.base_tool import ToolResult, ToolStatus


def test_fish_speech_input_schema_exposes_server_overrides() -> None:
    tool = FishSpeechTTS()
    props = tool.input_schema.get("properties", {})
    assert "server_url" in props
    assert "api_key" in props


def test_fish_speech_base_url_prefers_per_call_override(monkeypatch) -> None:
    monkeypatch.setenv("FISH_SPEECH_BASE_URL", "http://env-server:8080")
    tool = FishSpeechTTS()

    assert tool._base_url({"server_url": "http://call-server:9090"}) == "http://call-server:9090"
    assert tool._base_url({}) == "http://env-server:8080"


def test_fish_speech_headers_prefers_per_call_api_key(monkeypatch) -> None:
    monkeypatch.setenv("FISH_SPEECH_API_KEY", "env-key")
    tool = FishSpeechTTS()

    headers = tool._headers({"api_key": "call-key"})
    assert headers.get("authorization") == "Bearer call-key"

    env_headers = tool._headers({})
    assert env_headers.get("authorization") == "Bearer env-key"


def test_fish_speech_execute_checks_explicit_server_url(monkeypatch) -> None:
    tool = FishSpeechTTS()

    monkeypatch.setattr(tool, "check_dependencies", lambda: None)

    seen: dict[str, str] = {}

    def fake_server_status(*, base_url: str, headers: dict[str, str]) -> ToolStatus:
        seen["base_url"] = base_url
        return ToolStatus.UNAVAILABLE

    monkeypatch.setattr(tool, "_server_status", fake_server_status)

    result = tool.execute({"text": "hello", "server_url": "http://explicit-server:1234"})
    assert result.success is False
    assert seen["base_url"] == "http://explicit-server:1234"


def test_fish_speech_refuses_unsafe_long_text_by_default(monkeypatch) -> None:
    tool = FishSpeechTTS()
    monkeypatch.setattr(tool, "check_dependencies", lambda: None)
    monkeypatch.setattr(tool, "_server_status", lambda **kwargs: ToolStatus.AVAILABLE)
    monkeypatch.setattr(tool, "_generate", lambda *a, **k: ToolResult(success=True, data={}, artifacts=[]))

    long_text = "word " * 300  # ~107s at 2.8 wps
    result = tool.execute({"text": long_text})
    assert result.success is False
    assert "Refusing unsafe long Fish Speech request" in (result.error or "")


def test_fish_speech_allows_long_text_with_explicit_escape_hatch(monkeypatch) -> None:
    tool = FishSpeechTTS()
    monkeypatch.setattr(tool, "check_dependencies", lambda: None)
    monkeypatch.setattr(tool, "_server_status", lambda **kwargs: ToolStatus.AVAILABLE)
    monkeypatch.setattr(tool, "_generate", lambda *a, **k: ToolResult(success=True, data={}, artifacts=[]))

    long_text = "word " * 300
    result = tool.execute({"text": long_text, "allow_long_single_request": True})
    assert result.success is True
