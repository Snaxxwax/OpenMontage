"""F5-TTS local voice-cloning text-to-speech provider tool."""

from __future__ import annotations

import shutil
import subprocess
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


class F5TTS(BaseTool):
    """Local F5-TTS provider using the upstream `f5-tts_infer-cli` command."""

    name = "f5_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "f5_tts"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = ["cmd:f5-tts_infer-cli"]
    install_instructions = (
        "Install F5-TTS locally:\n"
        "  python3 -m pip install --user f5-tts\n"
        "Then verify:\n"
        "  f5-tts_infer-cli --help"
    )
    fallback = "piper_tts"
    fallback_tools = ["fish_speech_tts", "piper_tts", "openai_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_cloning",
        "reference_audio_conditioning",
        "offline_generation",
    ]
    supports = {
        "voice_cloning": True,
        "reference_audio": True,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
        "section_generation": True,
    }
    best_for = [
        "local-first narrator generation with reference-audio conditioning",
        "privacy-sensitive voice simulation after consent/provenance review",
        "section-based documentary narration when a stable reference voice exists",
    ]
    not_good_for = [
        "fully deterministic narration without fixed seeds/checkpoints",
        "generation without approved reference audio and reference transcript",
    ]

    input_schema = {
        "type": "object",
        "required": ["text", "reference_audio_path", "reference_text"],
        "properties": {
            "text": {"type": "string", "description": "Text to synthesize"},
            "reference_audio_path": {
                "type": "string",
                "description": "Approved reference voice audio file",
            },
            "reference_text": {
                "type": "string",
                "description": "Transcript for reference_audio_path",
            },
            "output_path": {"type": "string", "default": "f5_tts_output.wav"},
            "model": {"type": "string", "default": "F5TTS_v1_Base"},
            "device": {"type": "string", "default": "cuda"},
            "speed": {"type": "number", "default": 1.0},
            "nfe_step": {"type": "integer", "default": 32},
            "cfg_strength": {"type": "number", "default": 2.0},
            "remove_silence": {"type": "boolean", "default": False},
            "vocoder_name": {
                "type": "string",
                "default": "vocos",
                "enum": ["vocos", "bigvgan"],
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=8192, vram_mb=8000, disk_mb=5000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["cuda", "timeout"])
    idempotency_key_fields = [
        "text",
        "reference_audio_path",
        "reference_text",
        "model",
        "speed",
        "nfe_step",
        "cfg_strength",
    ]
    side_effects = [
        "writes audio file to output_path",
        "may download model/vocoder weights on first use via F5-TTS dependencies",
        "uses local GPU when device=cuda",
    ]
    user_visible_verification = [
        "Listen to generated audio for narrator match, pacing, artifacts, and consent/provenance suitability",
        "Run audio_probe to validate duration, sample rate, channels, and clipping risk",
    ]

    def get_status(self) -> ToolStatus:
        if shutil.which("f5-tts_infer-cli"):
            return ToolStatus.AVAILABLE
        try:
            import f5_tts  # noqa: F401

            return ToolStatus.AVAILABLE
        except ImportError:
            return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def build_command(self, inputs: dict[str, Any]) -> list[str]:
        text = inputs.get("text")
        reference_audio = inputs.get("reference_audio_path")
        reference_text = inputs.get("reference_text")
        if not text:
            raise ValueError("F5-TTS requires non-empty text")
        if not reference_audio:
            raise ValueError("F5-TTS requires reference_audio_path")
        ref_path = Path(reference_audio)
        if not ref_path.exists():
            raise FileNotFoundError(f"F5-TTS reference audio missing: {ref_path}")
        if not reference_text:
            raise ValueError("F5-TTS requires reference_text for the reference audio")

        output_path = Path(inputs.get("output_path", "f5_tts_output.wav"))
        output_dir = output_path.parent if str(output_path.parent) else Path(".")
        output_file = output_path.name

        cmd = [
            "f5-tts_infer-cli",
            "--model", str(inputs.get("model", "F5TTS_v1_Base")),
            "--ref_audio", str(ref_path),
            "--ref_text", str(reference_text),
            "--gen_text", str(text),
            "--output_dir", str(output_dir),
            "--output_file", output_file,
            "--vocoder_name", str(inputs.get("vocoder_name", "vocos")),
            "--speed", str(inputs.get("speed", 1.0)),
            "--nfe_step", str(inputs.get("nfe_step", 32)),
            "--cfg_strength", str(inputs.get("cfg_strength", 2.0)),
        ]
        if inputs.get("device"):
            cmd.extend(["--device", str(inputs["device"])])
        if inputs.get("remove_silence", False):
            cmd.append("--remove_silence")
        return cmd

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="F5-TTS not available. " + self.install_instructions)

        start = time.time()
        try:
            result = self._generate(inputs)
        except Exception as exc:
            return ToolResult(success=False, error=f"F5-TTS generation failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _generate(self, inputs: dict[str, Any]) -> ToolResult:
        output_path = Path(inputs.get("output_path", "f5_tts_output.wav"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = self.build_command(inputs)

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(inputs.get("timeout_seconds", 900)),
        )

        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"F5-TTS failed (exit {proc.returncode}): {proc.stderr or proc.stdout}",
            )
        if not output_path.exists():
            return ToolResult(success=False, error=f"F5-TTS output file missing: {output_path}")

        audio_duration = None
        try:
            from tools.analysis.audio_probe import probe_duration

            audio_duration = probe_duration(output_path)
        except Exception:
            audio_duration = None

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "model": inputs.get("model", "F5TTS_v1_Base"),
                "text_length": len(inputs["text"]),
                "reference_audio_path": str(inputs["reference_audio_path"]),
                "output": str(output_path),
                "format": output_path.suffix.lstrip(".") or "wav",
                "duration_seconds": audio_duration,
            },
            artifacts=[str(output_path)],
            model=inputs.get("model", "F5TTS_v1_Base"),
        )
