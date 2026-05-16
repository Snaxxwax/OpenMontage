"""Contract tests for asymmetric_write_final_qc.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from asymmetric_write_final_qc import write_final_qc  # noqa: E402


# ── fixture builders ──────────────────────────────────────────────────────────

def _render_report(**overrides) -> dict:
    base = {
        "project_id": "test-episode-001",
        "render_path": "/project/renders/test.mp4",
        "duration_seconds": 72.0,
        "resolution": "1280x720",
        "fps": 30,
    }
    base.update(overrides)
    return base


def _qc_report(**overrides) -> dict:
    base = {
        "project_id": "test-episode-001",
        "qc_passed": True,
        "claim_traceability_passed": True,
        "source_labels_visible": True,
        "audio_mix_passed": True,
        "failures": [],
    }
    base.update(overrides)
    return base


def _staged_manifest(**overrides) -> dict:
    base = {
        "render_id": "test-render-001",
        "gate_passed": True,
        "assets": [
            {"staged_path": "media/clip.mp4"},
            {"staged_path": "audio/narration.mp3"},
        ],
    }
    base.update(overrides)
    return base


def _approved_clips(**overrides) -> dict:
    base = {
        "approved_clips": [
            {
                "receipt_id": "receipt-001",
                "source_label_required": True,
                "source_label_text": "NBC News, Aug 2019",
            },
        ]
    }
    base.update(overrides)
    return base


# ── callable ──────────────────────────────────────────────────────────────────

def test_write_final_qc_callable():
    assert callable(write_final_qc)


# ── file written ──────────────────────────────────────────────────────────────

def test_writes_file(tmp_path):
    out = tmp_path / "qc" / "final_qc.md"
    write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    assert out.exists()
    assert out.stat().st_size > 0


# ── PASS / FAIL verdicts ──────────────────────────────────────────────────────

def test_pass_when_both_pass(tmp_path):
    out = tmp_path / "final_qc.md"
    rc = write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    assert rc == 0
    assert "PASS" in out.read_text()


def test_fail_when_qc_false(tmp_path):
    out = tmp_path / "final_qc.md"
    rc = write_final_qc(
        _render_report(),
        _qc_report(qc_passed=False),
        _staged_manifest(),
        _approved_clips(),
        out,
    )
    assert rc == 1
    assert "FAIL" in out.read_text()


def test_fail_when_gate_false(tmp_path):
    out = tmp_path / "final_qc.md"
    rc = write_final_qc(
        _render_report(),
        _qc_report(),
        _staged_manifest(gate_passed=False),
        _approved_clips(),
        out,
    )
    assert rc == 1
    assert "FAIL" in out.read_text()


# ── file written even on failure ──────────────────────────────────────────────

def test_file_written_even_on_fail(tmp_path):
    out = tmp_path / "qc" / "final_qc.md"
    rc = write_final_qc(
        _render_report(),
        _qc_report(qc_passed=False),
        _staged_manifest(gate_passed=False),
        _approved_clips(),
        out,
    )
    assert rc == 1
    assert out.exists()


# ── content checks ────────────────────────────────────────────────────────────

def test_content_contains_verdict(tmp_path):
    out = tmp_path / "final_qc.md"
    write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    content = out.read_text()
    assert "verdict" in content.lower()


def test_failures_listed_in_output(tmp_path):
    out = tmp_path / "final_qc.md"
    qc = _qc_report(qc_passed=False, failures=["audio_mix too loud", "label missing on clip-7"])
    write_final_qc(_render_report(), qc, _staged_manifest(), _approved_clips(), out)
    content = out.read_text()
    assert "audio_mix too loud" in content
    assert "label missing on clip-7" in content


def test_source_label_in_output(tmp_path):
    out = tmp_path / "final_qc.md"
    write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    assert "NBC News, Aug 2019" in out.read_text()


def test_episode_id_in_header(tmp_path):
    out = tmp_path / "final_qc.md"
    write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    content = out.read_text()
    assert "test-episode-001" in content.splitlines()[0]


# ── parent dir creation ───────────────────────────────────────────────────────

def test_creates_parent_dir(tmp_path):
    out = tmp_path / "deep" / "nested" / "final_qc.md"
    write_final_qc(_render_report(), _qc_report(), _staged_manifest(), _approved_clips(), out)
    assert out.exists()
