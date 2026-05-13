from __future__ import annotations

from lib.asymmetric_gate_policy import GatePolicy


def test_render_readiness_policy_requires_declared_artifacts() -> None:
    policy = GatePolicy.asymmetric_source_commentary()

    result = policy.validate("render-readiness", {})

    assert result.ok is False
    assert result.reasons == ["render-readiness requires artifacts: capture_plan, segment_approval, visual_rhythm"]


def test_render_readiness_policy_passes_approved_source_proof_plan() -> None:
    policy = GatePolicy.asymmetric_source_commentary()

    result = policy.validate(
        "render-readiness",
        {
            "capture_plan": {
                "operator_approved_for_acquisition": True,
                "captures": [{"id": "cap-proof", "approved": True}],
            },
            "segment_approval": {
                "segments": [
                    {"segment_id": "seg-proof", "approved": True},
                    {"segment_id": "seg-source", "approved": True},
                ],
            },
            "visual_rhythm": {
                "operator_approved_for_render": True,
                "segments": [
                    {
                        "id": "seg-proof",
                        "approved": True,
                        "event_type": "proof",
                        "visual_mode": "source_clip",
                        "starts_at_seconds": 4,
                        "source_label_present": True,
                        "source_label": "Researcher demo",
                    },
                    {
                        "id": "seg-source",
                        "approved": True,
                        "event_type": "source",
                        "visual_mode": "source_clip",
                        "starts_at_seconds": 12,
                        "source_label_present": True,
                        "source_label": "Vendor doc",
                    },
                ],
            },
        },
    )

    assert result.ok is True
    assert result.reasons == []


def test_qc_policy_reads_ffmpeg_silence_log() -> None:
    policy = GatePolicy.asymmetric_source_commentary()

    result = policy.validate(
        "qc",
        {
            "qc_report": {
                "creative_pass": True,
                "operator_approved_for_creative_pass": True,
                "audio": {"duration_seconds": 5, "max_silence_seconds": 0, "tail_silence_seconds": 0},
            }
        },
        ffmpeg_log_text="[silencedetect @ x] silence_start: 1\n[silencedetect @ x] silence_end: 2.5 | silence_duration: 1.5",
    )

    assert result.ok is False
    assert "FFmpeg silencedetect found silence over 1 second" in result.reasons[0]
