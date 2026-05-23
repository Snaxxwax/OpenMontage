"""Fish Speech local GPU text-to-speech provider tool."""

from __future__ import annotations

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
    """Text-to-speech provider backed by a local Fish Speech HTTP server."""

    name = "fish_speech_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "fish_speech"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []  # checked dynamically via HTTP health endpoint
    install_instructions = (
        "Start Fish Speech S2-Pro locally and expose the HTTP API. Default expected endpoints:\n"
        "  http://127.0.0.1:8080/v1/health\n"
        "  http://127.0.0.1:8080/v1/tts\n"
        "Modern Archivist commonly uses reference_id=asymmetric_narrator_v1."
    )
    fallback = "piper_tts"
    fallback_tools = ["piper_tts", "openai_tts", "elevenlabs_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_cloning",
        "local_gpu_generation",
        "prosody_tags",
    ]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
        "requires_local_server": True,
        "prosody_tags": True,
    }
    best_for = [
        "Modern Archivist / Failure Ledger narration",
        "local voice-cloned production with reference_id voices",
        "expressive narration with lightweight prosody tags",
    ]
    not_good_for = [
        "CPU-only machines",
        "production when the local Fish Speech server is not already running",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "reference_id": {
                "type": "string",
                "default": "asymmetric_narrator_v1",
                "description": "Fish Speech reference voice ID.",
            },
            "server_url": {
                "type": "string",
                "default": "http://127.0.0.1:8080",
                "description": "Base URL for the Fish Speech HTTP API.",
            },
            "format": {
                "type": "string",
                "default": "wav",
                "enum": ["wav", "mp3", "flac"],
            },
            "temperature": {"type": "number", "default": 0.72},
            "top_p": {"type": "number", "default": 0.8},
            "repetition_penalty": {"type": "number", "default": 1.1},
            "normalize": {"type": "boolean", "default": True},
            "streaming": {"type": "boolean", "default": False},
            "use_memory_cache": {"type": "string", "default": "on"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=8192, vram_mb=12000, disk_mb=1000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout", "connection"])
    idempotency_key_fields = ["text", "reference_id", "format", "temperature", "top_p"]
    side_effects = ["writes audio file to output_path", "calls local Fish Speech HTTP server"]
    user_visible_verification = ["Listen to generated audio for narrator match, pacing, and tag handling"]

    DEFAULT_SERVER_URL = "http://127.0.0.1:8080"
    DEFAULT_REFERENCE_ID = "asymmetric_narrator_v1"

    def get_status(self) -> ToolStatus:
        try:
            import requests

            response = requests.get(f"{self.DEFAULT_SERVER_URL}/v1/health", timeout=2)
            if response.status_code == 200 and "ok" in response.text.lower():
                return ToolStatus.AVAILABLE
        except Exception:
            pass
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        try:
            result = self._generate(inputs)
        except Exception as exc:
            return ToolResult(success=False, error=f"Fish Speech TTS failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _generate(self, inputs: dict[str, Any]) -> ToolResult:
        import requests

        server_url = inputs.get("server_url", self.DEFAULT_SERVER_URL).rstrip("/")
        health = requests.get(f"{server_url}/v1/health", timeout=5)
        health.raise_for_status()
        if "ok" not in health.text.lower():
            return ToolResult(success=False, error=f"Fish Speech unhealthy: {health.text[:200]}")

        fmt = inputs.get("format", "wav")
        output_path = Path(inputs.get("output_path", f"fish_speech_tts.{fmt}"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = self.build_payload(inputs)
        response = requests.post(f"{server_url}/v1/tts", json=payload, timeout=300)
        if response.status_code != 200:
            return ToolResult(
                success=False,
                error=f"Fish Speech failed (HTTP {response.status_code}): {response.text[:500]}",
            )
        output_path.write_bytes(response.content)
        if not output_path.exists() or output_path.stat().st_size == 0:
            return ToolResult(success=False, error=f"Fish Speech output file missing or empty: {output_path}")

        audio_duration = None
        if fmt == "wav":
            try:
                from tools.analysis.audio_probe import probe_duration

                audio_duration = probe_duration(output_path)
            except Exception:
                audio_duration = None

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "model": "fish-speech-s2-pro",
                "reference_id": payload["reference_id"],
                "format": fmt,
                "text_length": len(payload["text"]),
                "audio_duration_seconds": round(audio_duration, 2) if audio_duration else None,
                "server_url": server_url,
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
            model="fish-speech-s2-pro",
        )

    def build_payload(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Build the Fish Speech /v1/tts JSON payload from tool inputs."""
        return {
            "text": self._spoken_text(inputs["text"]),
            "reference_id": inputs.get("reference_id", self.DEFAULT_REFERENCE_ID),
            "format": inputs.get("format", "wav"),
            "streaming": inputs.get("streaming", False),
            "normalize": inputs.get("normalize", True),
            "temperature": inputs.get("temperature", 0.72),
            "top_p": inputs.get("top_p", 0.8),
            "repetition_penalty": inputs.get("repetition_penalty", 1.1),
            "use_memory_cache": inputs.get("use_memory_cache", "on"),
        }

    @staticmethod
    def _spoken_text(text: str) -> str:
        """Keep supported prosody tags and avoid speaking puppet-only tags literally."""
        return text.replace("[sip]", "[short pause]")
