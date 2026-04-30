from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tools.audio.tts_selector import TTSSelector
from tools.base_tool import ToolResult, ToolRuntime, ToolStatus


@dataclass
class _FakeScore:
    def explain(self) -> str:
        return "fake-score"

    def to_dict(self) -> dict[str, Any]:
        return {"weighted_score": 1.0}


class _FakeFishSpeechTool:
    name = "fish_speech_tts"
    provider = "fish_speech"
    runtime = ToolRuntime.LOCAL_GPU
    best_for = ["voiceover", "narration"]

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def get_info(self) -> dict[str, Any]:
        return {"agent_skills": [], "usage_location": "local", "best_for": self.best_for}

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        out = Path(inputs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"RIFF....WAVEfmt ")  # tiny placeholder
        return ToolResult(
            success=True,
            data={"audio_duration_seconds": 30.0, "output": str(out)},
            artifacts=[str(out)],
        )


class _FakeOtherTool(_FakeFishSpeechTool):
    name = "other_tts"
    provider = "other"
    runtime = ToolRuntime.LOCAL

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # Selector should call this once with the original output_path.
        out = Path(inputs.get("output_path") or "tts_output.wav")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"ok")
        return ToolResult(success=True, data={"output": str(out)}, artifacts=[str(out)])


def _long_text(words: int = 260) -> str:
    # Force sentence boundaries so chunking can group sentences.
    sentence = " ".join(["word"] * 20) + "."
    sentences = [sentence] * max(1, words // 20)
    return " ".join(sentences)


def test_selector_chunks_fish_speech_long_text(monkeypatch, tmp_path: Path) -> None:
    selector = TTSSelector()
    fish = _FakeFishSpeechTool()

    monkeypatch.setattr(selector, "_providers", lambda: [fish])
    monkeypatch.setattr(selector, "_select_best_tool", lambda inputs, candidates, ctx: (fish, _FakeScore()))

    # Make duration probing deterministic without real audio decoding.
    import tools.analysis.audio_probe as audio_probe

    monkeypatch.setattr(audio_probe, "probe_duration", lambda p: 30.0)

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool, capture_output: bool, text: bool):
        calls.append(cmd)
        # Create merged output so selector validation passes.
        out_path = Path(cmd[-1])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"merged")

        class _CP:
            returncode = 0
            stdout = ""
            stderr = ""

        return _CP()

    import tools.audio.tts_selector as tts_selector_mod

    monkeypatch.setattr(tts_selector_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(tts_selector_mod.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    out = tmp_path / "s07.mp3"
    result = selector.execute({"text": _long_text(), "output_path": str(out)})
    assert result.success is True
    assert result.data.get("chunking_used") is True
    assert result.data.get("chunk_count", 0) >= 2

    chunk_paths = [Path(c["output_path"]) for c in result.data["chunks"]]
    assert chunk_paths[0].name == "s07_c01.wav"
    assert chunk_paths[1].name == "s07_c02.wav"
    assert (tmp_path / "_chunks").is_dir()

    # Concat list file contains absolute chunk paths.
    concat_list = Path(result.data["concat_list_path"])
    text = concat_list.read_text(encoding="utf-8")
    for p in chunk_paths:
        assert f"file '{p.as_posix()}'" in text

    # ffmpeg invoked once for concat.
    assert len(calls) == 1
    assert calls[0][0].endswith("ffmpeg")


def test_selector_rejects_suspected_truncation(monkeypatch, tmp_path: Path) -> None:
    selector = TTSSelector()
    fish = _FakeFishSpeechTool()

    monkeypatch.setattr(selector, "_providers", lambda: [fish])
    monkeypatch.setattr(selector, "_select_best_tool", lambda inputs, candidates, ctx: (fish, _FakeScore()))

    import tools.analysis.audio_probe as audio_probe

    # Always report a 48s duration for chunk files (triggering duration_cluster_48s).
    monkeypatch.setattr(audio_probe, "probe_duration", lambda p: 48.0)

    import tools.audio.tts_selector as tts_selector_mod

    monkeypatch.setattr(tts_selector_mod.subprocess, "run", lambda *a, **k: pytest.fail("ffmpeg should not run"))
    monkeypatch.setattr(tts_selector_mod.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    long = _long_text(words=900)  # ensures at least one chunk is still 'expected' > ~62s
    out = tmp_path / "s07.wav"
    result = selector.execute(
        {
            "text": long,
            "output_path": str(out),
            "chunking": {"target_chunk_seconds_min": 70, "target_chunk_seconds_max": 90},
        }
    )
    assert result.success is False
    assert "Suspected truncation" in (result.error or "")
    assert result.data.get("truncation_reason") in {"duration_cluster_48s", "implausibly_short"}


def test_selector_does_not_chunk_non_fish_provider(monkeypatch, tmp_path: Path) -> None:
    selector = TTSSelector()
    other = _FakeOtherTool()

    monkeypatch.setattr(selector, "_providers", lambda: [other])
    monkeypatch.setattr(selector, "_select_best_tool", lambda inputs, candidates, ctx: (other, _FakeScore()))

    out = tmp_path / "out.wav"
    result = selector.execute({"text": _long_text(), "output_path": str(out)})
    assert result.success is True
    assert result.data.get("chunking_used") is not True
