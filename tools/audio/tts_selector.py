"""Capability-level text-to-speech selector that chooses among provider tools.

Provider discovery is automatic — any BaseTool with capability="tts"
is picked up from the registry.  Adding a new TTS provider requires only creating
the tool file in tools/audio/; no changes to this selector are needed.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStability, ToolTier, ToolStatus
from lib.gpu_governance import gpu_lock, mark_failed_after_isolation


_WORD_RE = re.compile(r"\S+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def estimate_speech_seconds(text: str, *, words_per_second: float = 2.8) -> float:
    word_count = len(_WORD_RE.findall(text or ""))
    if words_per_second <= 0:
        return 0.0
    return word_count / words_per_second


def split_sentences(text: str) -> list[str]:
    """Very lightweight sentence splitting with paragraph boundaries preserved."""
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences: list[str] = []
    for para in paragraphs:
        parts = _SENTENCE_SPLIT_RE.split(para.strip())
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)
    return sentences


def _split_long_sentence(sentence: str, *, max_words: int) -> list[str]:
    """Fallback splitter for extremely long sentences."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]

    # Prefer to split at softer boundaries first.
    soft_parts = re.split(r"([;,:])\s+", sentence)
    if len(soft_parts) > 1:
        rebuilt: list[str] = []
        buf = ""
        for part in soft_parts:
            if not part:
                continue
            buf = (buf + " " + part).strip()
            if len(buf.split()) >= max_words:
                rebuilt.append(buf.strip())
                buf = ""
        if buf.strip():
            rebuilt.append(buf.strip())
        return [s for s in rebuilt if s.strip()]

    # Last resort: chunk by word count.
    chunks: list[str] = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i : i + max_words]).strip())
    return [c for c in chunks if c]


def chunk_sentences(sentences: list[str], *, min_words: int, max_words: int) -> list[str]:
    if not sentences:
        return []
    if min_words <= 0:
        min_words = 1
    if max_words < min_words:
        max_words = min_words

    chunks: list[str] = []
    cur: list[str] = []
    cur_words = 0

    def flush() -> None:
        nonlocal cur, cur_words
        if cur:
            chunks.append(" ".join(cur).strip())
        cur = []
        cur_words = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_words = len(sentence.split())
        if sentence_words > max_words:
            flush()
            for piece in _split_long_sentence(sentence, max_words=max_words):
                chunks.append(piece)
            continue

        if cur_words + sentence_words > max_words and cur:
            flush()

        cur.append(sentence)
        cur_words += sentence_words

        if cur_words >= min_words:
            # Keep grouping until we'd exceed max_words; otherwise flush at a good boundary.
            flush()

    flush()
    return [c for c in chunks if c]


def derive_chunk_naming(
    output_path: Path, *, chunk_dir: Path | None = None, chunk_prefix: str | None = None
) -> tuple[str, Path, str]:
    out = Path(output_path)
    stem = out.stem
    prefix = chunk_prefix or (stem if re.fullmatch(r"s\d+", stem) else stem)
    chosen_chunk_dir = chunk_dir or (out.parent / "_chunks")
    concat_list_name = f"{prefix}_concat.txt"
    return prefix, chosen_chunk_dir, concat_list_name


def _suspected_truncation(
    *,
    duration_seconds: float | None,
    word_count: int,
    words_per_second: float,
) -> tuple[bool, str | None]:
    if duration_seconds is None:
        return True, "missing_duration"
    if duration_seconds <= 0:
        return True, "non_positive_duration"

    expected = word_count / words_per_second if words_per_second > 0 else 0.0
    if 47.0 <= duration_seconds <= 49.5 and expected > duration_seconds * 1.3:
        return True, "duration_cluster_48s"
    if word_count > 0 and duration_seconds < (word_count / 5.0):
        return True, "implausibly_short"
    return False, None


class TTSSelector(BaseTool):
    name = "tts_selector"
    version = "0.2.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "selector"
    stability = ToolStability.BETA
    runtime = ToolRuntime.HYBRID
    agent_skills = ["text-to-speech", "elevenlabs", "openai-docs"]

    capabilities = [
        "text_to_speech",
        "provider_selection",
    ]
    supports = {
        "user_preference_routing": True,
        "offline_fallback": True,
        "multilingual": True,
    }
    best_for = [
        "preflight tool selection",
        "user-facing recommendation flows",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "allow_paid_providers": {
                "type": "boolean",
                "default": False,
                "description": "Explicitly allow API/paid providers when local options are unavailable.",
            },
            "allow_concurrent_gpu": {
                "type": "boolean",
                "default": False,
                "description": "Bypass the local GPU mutex (unsafe; only if providers can coexist).",
            },
            "voice_id": {
                "type": "string",
                "description": "Provider-specific voice ID. Passed through to the selected TTS provider.",
            },
            "model_id": {
                "type": "string",
                "description": "TTS model to use (e.g. eleven_multilingual_v2). Passed through to provider.",
            },
            "stability": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Voice stability (ElevenLabs). Lower = more expressive.",
            },
            "similarity_boost": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Voice similarity boost (ElevenLabs).",
            },
            "style": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Style exaggeration (ElevenLabs). Higher = more expressive.",
            },
            "output_format": {
                "type": "string",
                "description": "Audio output format (e.g. mp3_44100_128). Passed through to provider.",
            },
            "preferred_provider": {
                "type": "string",
                "description": "Provider name or 'auto'. Valid values are discovered at runtime from the registry.",
                "default": "auto",
            },
            "allowed_providers": {
                "type": "array",
                "items": {"type": "string"},
            },
            "operation": {
                "type": "string",
                "enum": ["generate", "rank"],
                "default": "generate",
                "description": "Operation mode. 'rank' returns scored provider rankings without generating.",
            },
            "output_path": {"type": "string"},
            "chunk_dir": {
                "type": "string",
                "description": "Optional directory to store intermediate TTS chunks (Fish Speech chunking).",
            },
            "chunk_prefix": {
                "type": "string",
                "description": "Optional deterministic prefix for chunk filenames (Fish Speech chunking).",
            },
            "chunking": {
                "type": "object",
                "description": "Optional chunking controls (Fish Speech).",
                "properties": {
                    "enabled": {
                        "type": ["boolean", "null"],
                        "description": "Enable/disable chunking; null/omitted = auto.",
                    },
                    "threshold_seconds": {"type": "number", "default": 40},
                    "target_chunk_seconds_min": {"type": "number", "default": 25},
                    "target_chunk_seconds_max": {"type": "number", "default": 40},
                    "words_per_second": {"type": "number", "default": 2.8},
                },
            },
        },
    }

    def _providers(self) -> list[BaseTool]:
        """Auto-discover TTS providers from the registry."""
        from tools.tool_registry import registry
        registry.ensure_discovered()
        return [t for t in registry.get_by_capability("tts")
                if t.name != self.name]

    @property
    def providers(self) -> list[BaseTool]:
        """Public alias for discovered providers.

        Some scripts/snippets expect a `providers` attribute.
        """
        return self._providers()

    @property
    def fallback_tools(self) -> list[str]:
        """Dynamically built from discovered providers."""
        return [t.name for t in self._providers()]

    @property
    def provider_matrix(self) -> dict[str, dict[str, str]]:
        """Built at runtime from each provider's best_for field."""
        matrix = {}
        for tool in self._providers():
            strength = ", ".join(tool.best_for) if tool.best_for else tool.name
            matrix[tool.provider] = {"tool": tool.name, "strength": strength}
        return matrix

    def get_status(self) -> ToolStatus:
        if any(tool.get_status() == ToolStatus.AVAILABLE for tool in self._providers()):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        candidates = self._providers()
        if not candidates:
            return 0.0
        tool, _ = self._select_best_tool(inputs, candidates, self._prepare_task_context(inputs))
        return tool.estimate_cost(inputs) if tool else 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from lib.scoring import rank_providers

        task_context = self._prepare_task_context(inputs)
        candidates = self._providers()

        # Rank mode — return scored provider rankings without generating
        if inputs.get("operation") == "rank":
            rankings = rank_providers(candidates, task_context)
            return ToolResult(
                success=True,
                data={
                    "rankings": self._serialize_rankings(candidates, rankings),
                    "explanation": "\n".join(r.explain() for r in rankings[:5]),
                    "normalized_task_context": task_context,
                },
            )

        # Normal generation — use scored selection
        paid_policy_error = self._enforce_paid_provider_policy(inputs, candidates)
        if paid_policy_error:
            return ToolResult(success=False, error=paid_policy_error)

        tool, score = self._select_best_tool(inputs, candidates, task_context)
        if tool is None:
            if not inputs.get("allow_paid_providers", False):
                return ToolResult(
                    success=False,
                    error="No local/non-API provider available. Paid/API fallback requires allow_paid_providers=true.",
                )
            return ToolResult(success=False, error="No TTS provider available.")

        def _run() -> ToolResult:
            # Fish Speech chunking orchestration (Phase 6): chunk long narration by default.
            if (
                inputs.get("operation", "generate") == "generate"
                and tool.provider == "fish_speech"
                and isinstance(inputs.get("text"), str)
            ):
                chunking_cfg = inputs.get("chunking") or {}
                enabled = chunking_cfg.get("enabled", None)
                threshold_seconds = float(chunking_cfg.get("threshold_seconds", 40))
                words_per_second = float(chunking_cfg.get("words_per_second", 2.8))
                estimated_seconds = estimate_speech_seconds(inputs["text"], words_per_second=words_per_second)
                if enabled is True or (enabled is not False and estimated_seconds > threshold_seconds):
                    return self._execute_fish_speech_chunked(tool, inputs, score)
            return tool.execute(inputs)

        if getattr(tool, "runtime", None) == ToolRuntime.LOCAL_GPU and not inputs.get("allow_concurrent_gpu", False):
            with gpu_lock(tool_name=tool.name, timeout_s=0.0) as lk:
                if not lk.get("acquired"):
                    holder = lk.get("holder")
                    msg = "GPU is busy (VRAM occupied by another local GPU tool)."
                    if holder:
                        msg += f" Lock held by {holder.tool_name} (pid={holder.pid})."
                    return ToolResult(
                        success=False,
                        error=msg,
                        data={
                            "gpu_status": "busy",
                            "gpu_lock_holder": holder.tool_name if holder else None,
                            "gpu_lock_pid": holder.pid if holder else None,
                            "selected_tool": tool.name,
                            "selected_provider": tool.provider,
                        },
                    )
                result = _run()
        else:
            result = _run()

        if (
            not result.success
            and tool is not None
            and getattr(tool, "runtime", None) == ToolRuntime.LOCAL_GPU
            and not inputs.get("allow_concurrent_gpu", False)
        ):
            mark_failed_after_isolation(tool.name)
            result.data = result.data or {}
            result.data["gpu_status"] = "failed_after_isolation"

        if result.success:
            result.data.setdefault("selected_tool", tool.name)
            result.data["selected_provider"] = tool.provider
            result.data["selection_reason"] = score.explain() if score else f"Selected {tool.provider} ({tool.name})"
            if score:
                result.data["provider_score"] = score.to_dict()
            result.data.update(self._tool_context_payload(tool))
            result.data["alternatives_considered"] = [
                t.name for t in candidates
                if t.name != tool.name and t.get_status().value == "available"
            ]
        return result

    def _execute_fish_speech_chunked(self, tool: BaseTool, inputs: dict[str, Any], score: object) -> ToolResult:
        from tools.analysis.audio_probe import probe_duration

        text = str(inputs.get("text") or "")
        chunking_cfg = inputs.get("chunking") or {}
        wps = float(chunking_cfg.get("words_per_second", 2.8))
        min_s = float(chunking_cfg.get("target_chunk_seconds_min", 25))
        max_s = float(chunking_cfg.get("target_chunk_seconds_max", 40))
        threshold_s = float(chunking_cfg.get("threshold_seconds", 40))
        estimated_total_s = estimate_speech_seconds(text, words_per_second=wps)

        output_path = Path(inputs.get("output_path") or "tts_output.wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        chunk_dir_input = inputs.get("chunk_dir")
        chunk_dir = Path(chunk_dir_input) if chunk_dir_input else None
        chunk_prefix = inputs.get("chunk_prefix")
        prefix, chunk_dir, concat_list_name = derive_chunk_naming(output_path, chunk_dir=chunk_dir, chunk_prefix=chunk_prefix)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        min_words = max(1, int(math.ceil(wps * min_s)))
        max_words = max(min_words, int(math.floor(wps * max_s)))
        sentences = split_sentences(text)
        chunks_text = chunk_sentences(sentences, min_words=min_words, max_words=max_words)
        if not chunks_text:
            chunks_text = [text.strip()] if text.strip() else []

        # If chunking was forced but we still ended up with a single chunk, keep it safe:
        # it still runs through fish_speech_tts with chunking_enabled=true.
        chunk_results: list[dict[str, Any]] = []
        chunk_paths: list[Path] = []
        truncation_flags: list[dict[str, Any]] = []

        for i, chunk_text in enumerate(chunks_text, start=1):
            chunk_filename = f"{prefix}_c{i:02d}.wav"
            chunk_output_path = (chunk_dir / chunk_filename).resolve()
            chunk_word_count = len(_WORD_RE.findall(chunk_text))
            chunk_est_s = chunk_word_count / wps if wps > 0 else 0.0

            t0 = time.time()
            chunk_inputs = dict(inputs)
            chunk_inputs.update(
                {
                    "text": chunk_text,
                    "format": "wav",
                    "output_path": str(chunk_output_path),
                    "chunking_enabled": True,
                }
            )
            tool_result = tool.execute(chunk_inputs)
            wall_s = time.time() - t0
            if not tool_result.success:
                return ToolResult(
                    success=False,
                    error=f"Fish Speech chunk {i}/{len(chunks_text)} failed: {tool_result.error}",
                    data={
                        "chunking_used": True,
                        "estimated_total_seconds": estimated_total_s,
                        "threshold_seconds": threshold_s,
                        "chunk_failed_index": i,
                        "chunk_output_path": str(chunk_output_path),
                        "chunks_attempted": chunk_results,
                    },
                )

            if not chunk_output_path.is_file() or chunk_output_path.stat().st_size == 0:
                return ToolResult(
                    success=False,
                    error=f"Fish Speech chunk {i}/{len(chunks_text)} produced no audio at {chunk_output_path}",
                    data={
                        "chunking_used": True,
                        "estimated_total_seconds": estimated_total_s,
                        "threshold_seconds": threshold_s,
                        "chunk_failed_index": i,
                        "truncation_reason": "missing_file",
                        "chunk_output_path": str(chunk_output_path),
                        "chunks_attempted": chunk_results,
                    },
                )

            duration_tool = None
            try:
                duration_tool = (tool_result.data or {}).get("audio_duration_seconds")
            except Exception:
                duration_tool = None
            duration_probe = probe_duration(chunk_output_path)
            duration_s = float(duration_tool) if isinstance(duration_tool, (int, float)) else float(duration_probe or 0.0)

            suspected, reason = _suspected_truncation(
                duration_seconds=duration_s,
                word_count=chunk_word_count,
                words_per_second=wps,
            )
            if suspected:
                truncation_flags.append(
                    {
                        "chunk_index": i,
                        "reason": reason,
                        "duration_seconds": duration_s,
                        "estimated_seconds": chunk_est_s,
                        "word_count": chunk_word_count,
                        "output_path": str(chunk_output_path),
                    }
                )
                return ToolResult(
                    success=False,
                    error=f"Suspected truncation in Fish Speech chunk {i}/{len(chunks_text)} ({reason}).",
                    data={
                        "chunking_used": True,
                        "estimated_total_seconds": estimated_total_s,
                        "threshold_seconds": threshold_s,
                        "chunk_failed_index": i,
                        "truncation_reason": reason,
                        "truncation_flags": truncation_flags,
                        "chunks_attempted": chunk_results,
                    },
                )

            chunk_paths.append(chunk_output_path)
            chunk_results.append(
                {
                    "index": i,
                    "text_length": len(chunk_text),
                    "word_count": chunk_word_count,
                    "estimated_seconds": round(chunk_est_s, 2),
                    "output_path": str(chunk_output_path),
                    "duration_seconds": round(duration_s, 2),
                    "wall_time_seconds": round(wall_s, 2),
                    "realtime_factor": round((wall_s / duration_s), 3) if duration_s > 0 else None,
                    "suspected_truncation": False,
                }
            )

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            return ToolResult(
                success=False,
                error="ffmpeg is required to concatenate Fish Speech chunks but was not found on PATH.",
                data={"chunking_used": True, "chunk_count": len(chunk_paths), "chunk_dir": str(chunk_dir)},
            )

        concat_list_path = (chunk_dir / concat_list_name).resolve()
        concat_lines = [f"file '{p.as_posix()}'" for p in chunk_paths]
        concat_list_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

        out_ext = output_path.suffix.lower().lstrip(".") or "wav"
        merged_path = output_path.resolve()

        cmd: list[str]
        if out_ext == "wav":
            cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(merged_path)]
        elif out_ext == "mp3":
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "4",
                str(merged_path),
            ]
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                str(merged_path),
            ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            return ToolResult(
                success=False,
                error=f"ffmpeg concat failed: {exc.stderr or exc.stdout or str(exc)}",
                data={
                    "chunking_used": True,
                    "chunk_count": len(chunk_paths),
                    "concat_list_path": str(concat_list_path),
                    "ffmpeg_command": cmd,
                },
            )

        if not merged_path.is_file() or merged_path.stat().st_size == 0:
            return ToolResult(
                success=False,
                error=f"Concatenated output missing or empty: {merged_path}",
                data={"chunking_used": True, "merged_output_path": str(merged_path), "ffmpeg_command": cmd},
            )

        merged_duration = probe_duration(merged_path) if merged_path.suffix.lower() != ".pcm" else None
        return ToolResult(
            success=True,
            data={
                "provider": tool.provider,
                "model": (getattr(tool, "model", None) or "fish-speech-server"),
                "chunking_used": True,
                "chunk_count": len(chunk_paths),
                "chunks": chunk_results,
                "chunk_dir": str(chunk_dir),
                "concat_list_path": str(concat_list_path),
                "merged_output_path": str(merged_path),
                "merged_duration_seconds": round(merged_duration, 2) if merged_duration else None,
                "estimated_total_seconds": round(estimated_total_s, 2),
                "threshold_seconds": threshold_s,
                "ffmpeg_command": cmd,
                "truncation_flags": truncation_flags,
            },
            artifacts=[str(merged_path)],
        )

    def _select_best_tool(
        self,
        inputs: dict[str, Any],
        candidates: list[BaseTool],
        task_context: dict[str, Any],
    ) -> tuple[BaseTool | None, object]:
        """Select the best TTS provider using scored ranking."""
        from lib.scoring import rank_providers

        preferred = inputs.get("preferred_provider", "auto")
        allowed = set(inputs.get("allowed_providers") or [])
        if allowed:
            candidates = [tool for tool in candidates if tool.provider in allowed]

        if not inputs.get("allow_paid_providers", False) and preferred == "auto":
            candidates = [t for t in candidates if t.runtime != ToolRuntime.API]

        rankings = rank_providers(candidates, task_context)

        tool_by_provider: dict[str, BaseTool] = {}
        for tool in candidates:
            if tool.provider not in tool_by_provider and tool.get_status() == ToolStatus.AVAILABLE:
                tool_by_provider[tool.provider] = tool

        if preferred != "auto":
            for score_item in rankings:
                if score_item.provider == preferred and score_item.provider in tool_by_provider:
                    return tool_by_provider[score_item.provider], score_item

        for score_item in rankings:
            if score_item.provider in tool_by_provider:
                return tool_by_provider[score_item.provider], score_item

        return None, None

    def _enforce_paid_provider_policy(self, inputs: dict[str, Any], candidates: list[BaseTool]) -> str | None:
        allow_paid = bool(inputs.get("allow_paid_providers", False))
        preferred = str(inputs.get("preferred_provider", "auto"))
        allowed = set(inputs.get("allowed_providers") or [])
        if allow_paid:
            return None

        api_providers = {t.provider for t in candidates if t.runtime == ToolRuntime.API}
        if preferred != "auto" and preferred in api_providers:
            return (
                f"Preferred provider '{preferred}' is a paid/API provider. "
                "Set allow_paid_providers=true to approve paid/API fallback."
            )
        if allowed and (allowed & api_providers):
            return (
                "allowed_providers includes paid/API providers. "
                "Set allow_paid_providers=true to approve paid/API fallback."
            )
        return None

    def _prepare_task_context(self, inputs: dict[str, Any]) -> dict[str, Any]:
        from lib.scoring import normalize_task_context

        return normalize_task_context(
            inputs.get("task_context", {}),
            prompt=inputs.get("text", ""),
            capability=self.capability,
            operation=inputs.get("operation", "generate"),
        )

    @staticmethod
    def _tool_context_payload(tool: BaseTool) -> dict[str, Any]:
        info = tool.get_info()
        return {
            "selected_tool_agent_skills": info.get("agent_skills", []),
            "required_agent_skills": info.get("agent_skills", []),
            "selected_tool_usage_location": info.get("usage_location"),
            "selected_tool_best_for": info.get("best_for", []),
        }

    def _serialize_rankings(self, candidates: list[BaseTool], rankings: list[object]) -> list[dict[str, Any]]:
        tool_by_name = {tool.name: tool for tool in candidates}
        serialized: list[dict[str, Any]] = []
        for score in rankings:
            item = score.to_dict()
            tool = tool_by_name.get(score.tool_name)
            if tool:
                info = tool.get_info()
                item["agent_skills"] = info.get("agent_skills", [])
                item["usage_location"] = info.get("usage_location")
                item["best_for"] = info.get("best_for", [])
                item["status"] = str(tool.get_status())
            serialized.append(item)
        return serialized
