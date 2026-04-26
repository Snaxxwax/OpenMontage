"""ACE-Step 1.5 / 1.5-XL local music generation.

Runs ACE-Step entirely on the local GPU (CUDA). No API key required.
Models are downloaded from HuggingFace on first use and cached locally.

Supported tasks:
  text2music  — Generate music from a text prompt + optional lyrics (default)
  cover       — Style-transfer from a reference audio file (audio2audio mode)

Notes:
  - Default model: ACE-Step-v1-3.5B (auto-downloaded by the library)
  - v1.5 / v1.5-xl: pass model='v1.5' or model='v1.5-xl'; these are
    downloaded via huggingface_hub.snapshot_download on first use.
  - Pipeline is cached per model variant after first load to avoid
    reloading weights on every call.
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

# HuggingFace repo IDs for each supported model variant.
# The 'default' key maps to the library's built-in REPO_ID so it can
# auto-download without us specifying a checkpoint_dir.
_MODEL_REPOS: dict[str, str | None] = {
    "default": None,                          # uses library's built-in REPO_ID
    "v1.5": "ACE-Step/ACE-Step-v1.5",
    "v1.5-xl": "ACE-Step/ACE-Step-v1-5-xlarge",
}

# Cached pipeline instances keyed by model variant — avoid reloading weights.
_PIPELINE_CACHE: dict[str, Any] = {}


def _is_acestep_available() -> bool:
    try:
        import importlib
        importlib.import_module("acestep")
        return True
    except ImportError:
        return False


def _is_cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


class ACEStepMusic(BaseTool):
    """Local GPU music generation via ACE-Step 1.5 / 1.5-XL."""

    name = "acestep_music"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "music_generation"
    provider = "acestep"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = ["python:acestep", "python:torch"]
    install_instructions = (
        "Install ACE-Step:\n"
        "  pip install git+https://github.com/ACE-Step/ACE-Step.git\n"
        "Models download from HuggingFace on first use (~8–16 GB per variant).\n"
        "Requires CUDA GPU with 8 GB+ VRAM (default/v1.5) or 20 GB+ (v1.5-xl).\n"
        "No API key needed — fully offline after first download."
    )

    agent_skills = ["acestep", "music"]

    capabilities = [
        "generate_background_music",
        "generate_song",
        "generate_instrumental",
        "cover_style_transfer",
    ]
    supports = {
        "instrumental": True,
        "vocals": True,
        "custom_lyrics": True,
        "bpm_control": True,
        "key_control": True,
        "seed_control": True,
        "cover": True,
        "offline": True,
    }
    best_for = [
        "free local music generation with no API cost",
        "instrumental background music for explainer videos",
        "full songs with vocals and custom lyrics",
        "style-transfer covers from a reference audio file",
        "reproducible music via seed control",
    ]
    not_good_for = [
        "sound effects (use ElevenLabs SFX instead)",
        "machines without a CUDA GPU",
        "very short stingers under 10 seconds",
    ]

    fallback_tools = ["suno_music", "music_gen"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "Music description layering genre, mood, instruments, and "
                    "production style. Example: 'Dark cinematic orchestral, tense "
                    "strings, pulsing bass, investigative thriller mood, "
                    "studio-polished production'"
                ),
            },
            "task": {
                "type": "string",
                "enum": ["text2music", "cover"],
                "default": "text2music",
                "description": (
                    "text2music — generate from prompt + optional lyrics (default). "
                    "cover — style-transfer from reference_path using audio2audio mode."
                ),
            },
            "duration_seconds": {
                "type": "number",
                "minimum": 10,
                "maximum": 600,
                "description": "Target audio duration in seconds. Required for text2music.",
            },
            "lyrics": {
                "type": "string",
                "description": (
                    "Optional structured lyrics with section tags: [Verse], [Chorus], "
                    "[Bridge], [Outro], etc. UPPERCASE lines = high vocal intensity. "
                    "Omit for instrumental."
                ),
            },
            "bpm": {
                "type": "number",
                "minimum": 30,
                "maximum": 300,
                "description": "Beats per minute. Omit to let the model decide.",
            },
            "key": {
                "type": "string",
                "description": (
                    "Musical key, e.g. 'D Minor', 'G Major'. Omit to let the model decide."
                ),
            },
            "model": {
                "type": "string",
                "enum": ["default", "v1.5", "v1.5-xl"],
                "default": "default",
                "description": (
                    "default — ACE-Step-v1-3.5B, downloaded automatically, ~8 GB VRAM. "
                    "v1.5 — ACE-Step-v1.5, ~8 GB VRAM, latest standard. "
                    "v1.5-xl — ACE-Step-v1.5-xlarge, ~20 GB VRAM, highest quality."
                ),
            },
            "infer_steps": {
                "type": "integer",
                "default": 60,
                "description": (
                    "Inference steps. 8 = turbo (fast, good quality). "
                    "60 = full quality (default)."
                ),
            },
            "guidance_scale": {
                "type": "number",
                "default": 15.0,
                "description": "Classifier-free guidance scale. Higher = more prompt-adherent.",
            },
            "cover_strength": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.5,
                "description": (
                    "For cover task: how closely to follow the reference audio. "
                    "0.2 = loose style inspiration, 0.5 = balanced (default), "
                    "0.9 = very close to reference."
                ),
            },
            "reference_path": {
                "type": "string",
                "description": "For cover task: path to the source audio file.",
            },
            "seed": {
                "type": "integer",
                "description": "Random seed for reproducibility. Omit for random.",
            },
            "output_path": {
                "type": "string",
                "description": (
                    "Output file path (.mp3 or .wav). "
                    "Defaults to acestep_output.wav."
                ),
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4,
        ram_mb=8192,
        vram_mb=8192,
        disk_mb=20000,   # model weights
        network_required=False,  # offline after first download
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["cuda_oom"])
    idempotency_key_fields = [
        "prompt", "duration_seconds", "lyrics", "bpm", "key", "seed", "model",
    ]
    side_effects = [
        "writes audio file to output_path",
        "downloads model weights on first run (~8–16 GB)",
    ]
    user_visible_verification = [
        "Listen to generated music for mood, genre, and quality",
        "Confirm duration matches the target video segment",
    ]

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> ToolStatus:
        if not _is_cuda_available():
            return ToolStatus.UNAVAILABLE
        if not _is_acestep_available():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def get_info(self) -> dict[str, Any]:
        base = {}
        try:
            base = super().get_info()
        except Exception:
            pass
        base["models"] = list(_MODEL_REPOS.keys())
        base["cuda_available"] = _is_cuda_available()
        base["acestep_installed"] = _is_acestep_available()
        return base

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0  # fully local

    # ── Public execute ────────────────────────────────────────────────────────

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if not _is_cuda_available():
            return ToolResult(
                success=False,
                error="ACE-Step requires a CUDA GPU. No CUDA device found.",
            )
        if not _is_acestep_available():
            return ToolResult(
                success=False,
                error="ACE-Step is not installed.\n" + self.install_instructions,
            )

        task = inputs.get("task", "text2music")
        start = time.time()

        try:
            if task == "text2music":
                result = self._text2music(inputs)
            elif task == "cover":
                result = self._cover(inputs)
            else:
                return ToolResult(success=False, error=f"Unknown task: {task!r}")
        except Exception as e:
            return ToolResult(success=False, error=f"ACE-Step generation failed: {e}")

        result.duration_seconds = round(time.time() - start, 2)
        result.cost_usd = 0.0
        return result

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_pipeline(self, model_variant: str = "default") -> Any:
        """Load (or return cached) ACEStepPipeline for the given model variant."""
        import torch
        from acestep.pipeline_ace_step import ACEStepPipeline

        if model_variant not in _PIPELINE_CACHE:
            repo_id = _MODEL_REPOS.get(model_variant)

            if repo_id is not None:
                # Download (or locate cached) checkpoint for a specific variant.
                from huggingface_hub import snapshot_download
                checkpoint_dir = snapshot_download(repo_id=repo_id)
                pipe = ACEStepPipeline(checkpoint_dir=checkpoint_dir)
                pipe.load_checkpoint(checkpoint_dir=checkpoint_dir)
            else:
                # 'default' variant — let the library use its built-in REPO_ID.
                pipe = ACEStepPipeline()
                pipe.load_checkpoint()

            _PIPELINE_CACHE[model_variant] = pipe

        return _PIPELINE_CACHE[model_variant]

    def _build_prompt(self, inputs: dict[str, Any]) -> str:
        """Append BPM/key metadata to the prompt as descriptive tokens."""
        prompt = inputs["prompt"]
        tags: list[str] = []
        if bpm := inputs.get("bpm"):
            tags.append(f"{int(bpm)} bpm")
        if key := inputs.get("key"):
            tags.append(key)
        if tags:
            prompt = prompt + ", " + ", ".join(tags)
        return prompt

    def _resolve_output(self, inputs: dict[str, Any], default: str = "acestep_output.wav") -> Path:
        output_path = Path(inputs.get("output_path", default))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def _parse_output(self, raw: list) -> str:
        """Extract the first audio file path from ACEStepPipeline's return value.

        ACEStepPipeline.__call__ returns:
            [output_path_str, ..., params_dict]
        where the last element is a dict and all preceding elements are file paths.
        """
        paths = [item for item in raw if isinstance(item, str)]
        if not paths:
            raise RuntimeError(f"No output path in ACE-Step result: {raw}")
        return paths[0]

    def _text2music(self, inputs: dict[str, Any]) -> ToolResult:
        duration = inputs.get("duration_seconds")
        if duration is None:
            return ToolResult(
                success=False,
                error=(
                    "acestep_music: duration_seconds is required for text2music. "
                    "Derive it from the approved target runtime in the script/proposal."
                ),
            )

        model_variant = inputs.get("model", "default")
        pipe = self._get_pipeline(model_variant)

        prompt = self._build_prompt(inputs)
        lyrics = inputs.get("lyrics") or ""
        seed = inputs.get("seed")
        manual_seeds = [seed] if seed is not None else None
        infer_steps = inputs.get("infer_steps", 60)
        guidance_scale = inputs.get("guidance_scale", 15.0)
        output_path = self._resolve_output(inputs)

        # Determine format from output extension (default wav)
        fmt = output_path.suffix.lstrip(".") or "wav"
        save_dir = output_path.parent

        raw = pipe(
            format=fmt,
            audio_duration=float(duration),
            prompt=prompt,
            lyrics=lyrics or "",
            infer_step=infer_steps,
            guidance_scale=guidance_scale,
            scheduler_type="euler",
            cfg_type="apg",
            omega_scale=10.0,
            manual_seeds=manual_seeds,
            task="text2music",
            save_path=str(output_path.resolve()),
        )

        generated_path = self._parse_output(raw)

        # Rename to the requested output_path if different
        gen = Path(generated_path)
        if gen.resolve() != output_path.resolve():
            if output_path.exists():
                output_path.unlink()
            gen.rename(output_path)

        return ToolResult(
            success=True,
            data={
                "provider": "acestep",
                "model": _MODEL_REPOS.get(model_variant) or "ACE-Step/ACE-Step-v1-3.5B",
                "task": "text2music",
                "prompt": prompt,
                "lyrics_used": bool(lyrics),
                "duration_seconds": duration,
                "infer_steps": infer_steps,
                "seed": seed,
                "output": str(output_path),
                "format": fmt,
            },
            artifacts=[str(output_path)],
            model=f"acestep/{model_variant}",
        )

    def _cover(self, inputs: dict[str, Any]) -> ToolResult:
        reference_path = inputs.get("reference_path")
        if not reference_path:
            return ToolResult(success=False, error="cover task requires reference_path.")
        if not Path(reference_path).exists():
            return ToolResult(success=False, error=f"reference_path not found: {reference_path}")

        duration = inputs.get("duration_seconds")
        model_variant = inputs.get("model", "default")
        pipe = self._get_pipeline(model_variant)

        prompt = self._build_prompt(inputs)
        cover_strength = inputs.get("cover_strength", 0.5)
        seed = inputs.get("seed")
        manual_seeds = [seed] if seed is not None else None
        infer_steps = inputs.get("infer_steps", 60)
        guidance_scale = inputs.get("guidance_scale", 15.0)
        output_path = self._resolve_output(inputs, "acestep_cover.wav")

        fmt = output_path.suffix.lstrip(".") or "wav"
        save_dir = output_path.parent

        call_kwargs: dict[str, Any] = dict(
            format=fmt,
            prompt=prompt,
            lyrics=inputs.get("lyrics") or "",
            infer_step=infer_steps,
            guidance_scale=guidance_scale,
            scheduler_type="euler",
            cfg_type="apg",
            omega_scale=10.0,
            manual_seeds=manual_seeds,
            audio2audio_enable=True,
            ref_audio_input=str(reference_path),
            ref_audio_strength=cover_strength,
            save_path=str(output_path.resolve()),
        )
        if duration is not None:
            call_kwargs["audio_duration"] = float(duration)

        raw = pipe(**call_kwargs)
        generated_path = self._parse_output(raw)

        gen = Path(generated_path)
        if gen.resolve() != output_path.resolve():
            if output_path.exists():
                output_path.unlink()
            gen.rename(output_path)

        return ToolResult(
            success=True,
            data={
                "provider": "acestep",
                "model": _MODEL_REPOS.get(model_variant) or "ACE-Step/ACE-Step-v1-3.5B",
                "task": "cover",
                "prompt": prompt,
                "reference": str(reference_path),
                "cover_strength": cover_strength,
                "output": str(output_path),
                "format": fmt,
            },
            artifacts=[str(output_path)],
            model=f"acestep/{model_variant}",
        )
