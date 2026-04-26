from __future__ import annotations

from tools.audio.fish_speech_tts import FishSpeechTTS
from tools.base_tool import ToolStatus


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
