"""Gate policy for Asymmetric source-commentary runs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


ARTIFACT_NAMES = {
    "capture_plan": "source_capture_plan.json",
    "segment_approval": "source_segment_approval_manifest.json",
    "visual_rhythm": "visual_rhythm_plan.json",
    "qc_report": "qc_report.json",
}

SILENCE_END_RE = re.compile(
    r"silence_end:\s*(?P<end>[0-9.]+)\s*\|\s*silence_duration:\s*(?P<duration>[0-9.]+)"
)
SILENCE_START_RE = re.compile(r"silence_start:\s*(?P<start>[0-9.]+)")


@dataclass
class GateResult:
    ok: bool = True
    reasons: list[str] = field(default_factory=list)

    def fail(self, reason: str) -> None:
        self.ok = False
        self.reasons.append(reason)

    def payload(self) -> dict[str, Any]:
        return {"ok": self.ok, "reasons": self.reasons}


@dataclass(frozen=True)
class GateDefinition:
    name: str
    required_artifacts: tuple[str, ...]
    validator: Callable[..., GateResult]
    receipt_filename: str


def approved_source_or_proof_events(visual_rhythm: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for segment in visual_rhythm.get("segments") or []:
        if not isinstance(segment, dict):
            continue
        if segment.get("approved") is True and segment.get("event_type") in {"source", "proof"}:
            events.append(segment)
    return events


def validate_render_readiness(
    *,
    capture_plan: dict[str, Any],
    segment_approval: dict[str, Any],
    visual_rhythm: dict[str, Any],
) -> GateResult:
    result = GateResult()

    if capture_plan.get("operator_approved_for_acquisition") is not True:
        result.fail("operator approval is required before acquisition")

    unapproved_captures = [
        item.get("id", "<unknown>")
        for item in capture_plan.get("captures") or []
        if not isinstance(item, dict) or item.get("approved") is not True
    ]
    if unapproved_captures:
        result.fail(f"capture plan contains unapproved captures: {', '.join(map(str, unapproved_captures))}")

    if visual_rhythm.get("operator_approved_for_render") is not True:
        result.fail("operator approval is required before render")

    approved_segments = {
        item.get("segment_id")
        for item in segment_approval.get("segments") or []
        if isinstance(item, dict) and item.get("approved") is True
    }
    for segment in visual_rhythm.get("segments") or []:
        if not isinstance(segment, dict):
            result.fail("visual rhythm contains a non-object segment")
            continue
        segment_id = segment.get("id", "<unknown>")
        if segment.get("approved") is True and segment_id not in approved_segments:
            result.fail(f"visual segment is render-approved without segment approval: {segment_id}")
        is_source_clip = segment.get("event_type") == "source" or segment.get("visual_mode") == "source_clip"
        if is_source_clip and not (segment.get("source_label_present") is True and segment.get("source_label")):
            result.fail(f"source clip is missing an on-screen source label: {segment_id}")

    proof_times = [
        float(segment["starts_at_seconds"])
        for segment in visual_rhythm.get("segments") or []
        if (
            isinstance(segment, dict)
            and segment.get("approved") is True
            and segment.get("event_type") == "proof"
            and isinstance(segment.get("starts_at_seconds"), (int, float))
        )
    ]
    if not proof_times:
        result.fail("at least one approved proof event is required")
    elif min(proof_times) > 10:
        result.fail("first approved proof event must start by 10 seconds")

    source_or_proof_count = len(approved_source_or_proof_events(visual_rhythm))
    if source_or_proof_count < 2:
        result.fail("at least 2 approved source/proof events are required")

    return result


def parse_silencedetect_log(text: str, duration_seconds: float | None = None) -> dict[str, Any]:
    long_silences: list[dict[str, float]] = []
    last_silence_start: float | None = None
    tail_silence_seconds = 0.0

    for line in text.splitlines():
        start_match = SILENCE_START_RE.search(line)
        if start_match:
            last_silence_start = float(start_match.group("start"))
        end_match = SILENCE_END_RE.search(line)
        if end_match:
            end = float(end_match.group("end"))
            duration = float(end_match.group("duration"))
            start = max(end - duration, 0.0)
            long_silences.append({"start": start, "end": end, "duration": duration})
            last_silence_start = None

    if duration_seconds is not None and last_silence_start is not None:
        tail_silence_seconds = max(duration_seconds - last_silence_start, 0.0)
        long_silences.append(
            {
                "start": last_silence_start,
                "end": duration_seconds,
                "duration": tail_silence_seconds,
            }
        )

    return {"silences": long_silences, "tail_silence_seconds": tail_silence_seconds}


def validate_qc_report(*, qc_report: dict[str, Any], ffmpeg_log_text: str = "") -> GateResult:
    result = GateResult()

    if qc_report.get("creative_pass") is not True:
        result.fail("creative_pass must be true")
    if qc_report.get("operator_approved_for_creative_pass") is not True:
        result.fail("operator approval is required before creative pass")

    audio = qc_report.get("audio") if isinstance(qc_report.get("audio"), dict) else {}
    max_silence = audio.get("max_silence_seconds", qc_report.get("max_silence_seconds"))
    tail_silence = audio.get("tail_silence_seconds", qc_report.get("tail_silence_seconds"))
    duration = audio.get("duration_seconds", qc_report.get("duration_seconds"))

    if isinstance(max_silence, (int, float)) and float(max_silence) > 1:
        result.fail(f"silence over 1 second detected in QC report: {float(max_silence):.3f}s")
    if isinstance(tail_silence, (int, float)) and float(tail_silence) > 1:
        result.fail(f"tail silence over 1 second detected in QC report: {float(tail_silence):.3f}s")

    if ffmpeg_log_text:
        parsed = parse_silencedetect_log(
            ffmpeg_log_text,
            float(duration) if isinstance(duration, (int, float)) else None,
        )
        for silence in parsed["silences"]:
            if silence["duration"] > 1:
                result.fail(
                    "FFmpeg silencedetect found silence over 1 second: "
                    f"{silence['duration']:.3f}s at {silence['start']:.3f}-{silence['end']:.3f}"
                )
        if parsed["tail_silence_seconds"] > 1:
            result.fail(f"FFmpeg silencedetect found tail silence over 1 second: {parsed['tail_silence_seconds']:.3f}s")

    return result


class GatePolicy:
    def __init__(self, definitions: dict[str, GateDefinition]) -> None:
        self.definitions = definitions

    @classmethod
    def asymmetric_source_commentary(cls) -> "GatePolicy":
        return cls(
            {
                "render-readiness": GateDefinition(
                    name="render-readiness",
                    required_artifacts=("capture_plan", "segment_approval", "visual_rhythm"),
                    validator=validate_render_readiness,
                    receipt_filename="render_readiness_gate.json",
                ),
                "qc": GateDefinition(
                    name="qc",
                    required_artifacts=("qc_report",),
                    validator=validate_qc_report,
                    receipt_filename="qc_gate.json",
                ),
            }
        )

    def definition(self, name: str) -> GateDefinition:
        try:
            return self.definitions[name]
        except KeyError as exc:
            raise ValueError(f"unknown gate: {name}") from exc

    def validate(self, name: str, artifacts: dict[str, dict[str, Any]], **kwargs: Any) -> GateResult:
        definition = self.definition(name)
        missing = [key for key in definition.required_artifacts if key not in artifacts or not artifacts[key]]
        if missing:
            return GateResult(ok=False, reasons=[f"{name} requires artifacts: {', '.join(missing)}"])
        if name == "render-readiness":
            return definition.validator(
                capture_plan=artifacts["capture_plan"],
                segment_approval=artifacts["segment_approval"],
                visual_rhythm=artifacts["visual_rhythm"],
            )
        if name == "qc":
            return definition.validator(
                qc_report=artifacts["qc_report"],
                ffmpeg_log_text=str(kwargs.get("ffmpeg_log_text") or ""),
            )
        raise ValueError(f"unknown gate: {name}")

    def receipt_path(self, name: str, qc_dir: Path) -> Path:
        return qc_dir / self.definition(name).receipt_filename
