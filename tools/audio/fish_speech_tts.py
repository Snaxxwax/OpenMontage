"""Fish Speech local server TTS provider.

Wraps a separately running Fish Speech server so OpenMontage can use Fish Audio
as a local GPU-backed TTS provider without forcing Fish Speech into the repo's
Python 3.10 runtime.
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
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class FishSpeechTTS(BaseTool):
    name = "fish_speech_tts"
    version = "0.2.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "fish_speech"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = ["python:requests", "python:ormsgpack"]
    install_instructions = (
        "Run Fish Speech as a separate local server and point OpenMontage at it.\n"
        "Official docs: https://speech.fish.audio/install/ and https://speech.fish.audio/server/\n"
        "Recommended env vars:\n"
        "  export FISH_SPEECH_BASE_URL=http://127.0.0.1:8080\n"
        "  export FISH_SPEECH_API_KEY=...   # optional, only if your server requires bearer auth\n"
        "Fish Speech currently documents Python 3.12 and recommends a 24GB GPU for inference."
    )
    fallback = "piper_tts"
    fallback_tools = ["piper_tts", "google_tts", "openai_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_selection",
        "voice_cloning",
        "multilingual",
        "offline_generation",
    ]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
        "reference_voice_prompting": True,
    }
    best_for = [
        "high-quality local GPU TTS",
        "reference-voice prompting without cloud APIs",
        "multilingual local narration when a Fish server is already running",
    ]
    not_good_for = [
        "CPU-only low-latency workflows",
        "drop-in use without a separately running Fish Speech server",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "description": "Text to synthesize"},
            "voice_id": {
                "type": "string",
                "description": "Alias for Fish Speech reference_id. Passed through by tts_selector.",
            },
            "reference_id": {
                "type": "string",
                "description": "Saved Fish Speech reference voice ID on the local server.",
            },
            "reference_audio_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local audio paths for in-context voice prompting.",
            },
            "reference_texts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Transcript text matching each reference audio path.",
            },
            "format": {
                "type": "string",
                "default": "wav",
                "enum": ["wav", "mp3", "opus", "pcm"],
            },
            "latency": {
                "type": "string",
                "default": "normal",
                "enum": ["normal", "balanced"],
            },
            "chunk_length": {
                "type": "integer",
                "default": 200,
                "minimum": 100,
                "maximum": 1000,
            },
            "max_new_tokens": {
                "type": "integer",
                "default": 1024,
                "minimum": 0,
            },
            "top_p": {
                "type": "number",
                "default": 0.8,
                "minimum": 0.1,
                "maximum": 1.0,
            },
            "repetition_penalty": {
                "type": "number",
                "default": 1.1,
                "minimum": 0.9,
                "maximum": 2.0,
            },
            "temperature": {
                "type": "number",
                "default": 0.8,
                "minimum": 0.1,
                "maximum": 1.0,
            },
            "seed": {
                "type": ["integer", "null"],
                "description": "Optional deterministic seed. Omit for randomized inference.",
            },
            "normalize": {
                "type": "boolean",
                "default": True,
                "description": "Let Fish Speech normalize text for better number stability.",
            },
            "output_path": {"type": "string"},
            "server_url": {
                "type": "string",
                "description": "Optional per-call override for FISH_SPEECH_BASE_URL.",
            },
            "api_key": {
                "type": "string",
                "description": "Optional per-call bearer token override for FISH_SPEECH_API_KEY.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=2048, vram_mb=24576, disk_mb=500, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout", "connection"])
    idempotency_key_fields = ["text", "reference_id", "format", "seed"]
    side_effects = ["writes audio file to output_path", "calls local Fish Speech server"]
    user_visible_verification = [
        "Listen for correct voice identity and pronunciation",
        "Check that reference-voice prompting is stable across long sections",
    ]

    _EXT_MAP = {
        "wav": "wav",
        "mp3": "mp3",
        "opus": "opus",
        "pcm": "pcm",
    }

    def _base_url(self, inputs: dict[str, Any] | None = None) -> str:
        if inputs and inputs.get("server_url"):
            return str(inputs["server_url"]).rstrip("/")
        return os.environ.get("FISH_SPEECH_BASE_URL", "http://127.0.0.1:8080").rstrip("/")

    def _headers(self, inputs: dict[str, Any] | None = None) -> dict[str, str]:
        headers = {
            "content-type": "application/msgpack",
        }
        api_key = (inputs or {}).get("api_key") or os.environ.get("FISH_SPEECH_API_KEY")
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        return headers

    def _server_status(self, *, base_url: str, headers: dict[str, str]) -> ToolStatus:
        try:
            import requests

            response = requests.get(
                f"{base_url}/v1/health",
                headers=headers,
                timeout=3,
            )
            if response.ok:
                return ToolStatus.AVAILABLE
            return ToolStatus.DEGRADED
        except Exception:
            return ToolStatus.UNAVAILABLE

    def get_status(self) -> ToolStatus:
        try:
            self.check_dependencies()
        except Exception:
            return ToolStatus.UNAVAILABLE
        return self._server_status(base_url=self._base_url(), headers=self._headers())

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        try:
            self.check_dependencies()
        except Exception:
            return ToolResult(success=False, error="Fish Speech dependencies unavailable. " + self.install_instructions)

        base_url = self._base_url(inputs)
        headers = self._headers(inputs)
        if self._server_status(base_url=base_url, headers=headers) != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="Fish Speech server unavailable. " + self.install_instructions)

        start = time.time()
        try:
            result = self._generate(inputs, base_url=base_url, headers=headers)
        except Exception as exc:
            return ToolResult(success=False, error=f"Fish Speech TTS failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _build_references(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        audio_paths = inputs.get("reference_audio_paths") or []
        ref_texts = inputs.get("reference_texts") or []
        if not audio_paths:
            return []
        if len(audio_paths) != len(ref_texts):
            raise ValueError("reference_audio_paths and reference_texts must have the same length")

        references: list[dict[str, Any]] = []
        for audio_path, ref_text in zip(audio_paths, ref_texts):
            path = Path(audio_path)
            if not path.is_file():
                raise FileNotFoundError(f"Reference audio not found: {path}")
            references.append({
                "audio": path.read_bytes(),
                "text": ref_text,
            })
        return references

    def _generate(self, inputs: dict[str, Any], *, base_url: str, headers: dict[str, str]) -> ToolResult:
        import ormsgpack
        import requests

        from tools.analysis.audio_probe import probe_duration

        text = inputs["text"]
        reference_id = (
            inputs.get("reference_id")
            or inputs.get("voice_id")
            or os.environ.get("FISH_SPEECH_DEFAULT_REFERENCE_ID")
        )
        fmt = inputs.get("format", "wav")
        ext = self._EXT_MAP.get(fmt, fmt)
        output_path = Path(inputs.get("output_path", f"tts_output.{ext}"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "text": text,
            "references": self._build_references(inputs),
            "reference_id": reference_id,
            "format": fmt,
            "latency": inputs.get("latency", "normal"),
            "max_new_tokens": inputs.get("max_new_tokens", 1024),
            "chunk_length": inputs.get("chunk_length", 200),
            "top_p": inputs.get("top_p", 0.8),
            "repetition_penalty": inputs.get("repetition_penalty", 1.1),
            "temperature": inputs.get("temperature", 0.8),
            "streaming": False,
            "use_memory_cache": inputs.get("use_memory_cache", "off"),
            "seed": inputs.get("seed"),
            "normalize": inputs.get("normalize", True),
        }

        response = requests.post(
            f"{base_url}/v1/tts",
            params={"format": "msgpack"},
            data=ormsgpack.packb(payload),
            headers=headers,
            timeout=600,
        )
        if not response.ok:
            error_detail = response.text
            try:
                error_detail = response.json()
            except Exception:
                pass
            raise RuntimeError(f"Fish Speech server error ({response.status_code}): {error_detail}")

        output_path.write_bytes(response.content)
        audio_duration = probe_duration(output_path) if fmt != "pcm" else None

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "model": "fish-speech-server",
                "reference_id": reference_id,
                "format": fmt,
                "fish_speech_server_url": base_url,
                "text_length": len(text),
                "audio_duration_seconds": round(audio_duration, 2) if audio_duration else None,
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
            model="fish-speech-server",
        )
