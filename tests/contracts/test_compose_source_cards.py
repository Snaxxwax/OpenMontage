"""Contract tests for asymmetric_compose_source_cards.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from scripts.asymmetric_compose_source_cards import (
    MIN_QUOTE_PROOF_BOTTOM_MARGIN,
    compose_source_cards,
)


def _make_source_image(path: Path, w: int = 800, h: int = 4000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), (200, 200, 200)).save(path)


def _card(overrides: dict | None = None) -> dict:
    base = {
        "card_id": "SC-01",
        "card_type": "article_header",
        "source_path": "assets/SC-01.png",
        "crop": {"x": 0, "y": 0, "w": 752, "h": 422},
        "canvas": {"w": 752, "h": 422, "top_margin": 0},
        "output_path": "assets/composed/SC-01-card.png",
    }
    if overrides:
        base.update(overrides)
    return base


def _manifest(cards: list | None = None) -> dict:
    return {
        "episode_id": "test-episode",
        "cards": cards if cards is not None else [_card()],
    }


def _run(manifest: dict, tmp_path: Path) -> tuple[int, Path]:
    qc_path = tmp_path / "qc_report.md"
    rc = compose_source_cards(manifest, tmp_path, qc_path)
    return rc, qc_path


# ── 1. callable ───────────────────────────────────────────────────────────────

def test_compose_source_cards_callable():
    assert callable(compose_source_cards)


# ── 2. valid article_header produces PNG ──────────────────────────────────────

def test_article_header_produces_png(tmp_path):
    _make_source_image(tmp_path / "assets/SC-01.png")
    rc, qc = _run(_manifest(), tmp_path)
    assert rc == 0
    out = tmp_path / "assets/composed/SC-01-card.png"
    assert out.exists()
    img = Image.open(out)
    assert img.size == (752, 422)


# ── 3. valid quote_proof produces PNG ─────────────────────────────────────────

def test_quote_proof_produces_png(tmp_path):
    _make_source_image(tmp_path / "assets/SC-02.png", w=752, h=4000)
    card = _card({
        "card_id": "SC-02",
        "card_type": "quote_proof",
        "source_path": "assets/SC-02.png",
        "crop": {"x": 0, "y": 0, "w": 752, "h": 315},
        "canvas": {"w": 752, "h": 422, "top_margin": 10, "bottom_safe_margin_px": 97},
        "output_path": "assets/composed/SC-02-card.png",
    })
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 0
    out = tmp_path / "assets/composed/SC-02-card.png"
    assert out.exists()
    img = Image.open(out)
    assert img.size == (752, 422)


# ── 4. missing source file fails ──────────────────────────────────────────────

def test_missing_source_file_fails(tmp_path):
    # source PNG never created
    rc, qc = _run(_manifest(), tmp_path)
    assert rc == 1
    assert "does not exist" in qc.read_text()


# ── 5. crop out of bounds fails ───────────────────────────────────────────────

def test_crop_out_of_bounds_fails(tmp_path):
    _make_source_image(tmp_path / "assets/SC-01.png", w=752, h=422)
    card = _card({"crop": {"x": 0, "y": 0, "w": 800, "h": 500}})  # exceeds 752×422
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 1
    assert "exceeds image bounds" in qc.read_text()


# ── 6. output_path escape fails ───────────────────────────────────────────────

def test_output_path_dotdot_fails(tmp_path):
    _make_source_image(tmp_path / "assets/SC-01.png")
    card = _card({"output_path": "assets/composed/../../evil.png"})
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 1
    assert "must not contain .." in qc.read_text()


# ── 7. output_path outside assets/composed fails ─────────────────────────────

def test_output_path_outside_assets_composed_fails(tmp_path):
    _make_source_image(tmp_path / "assets/SC-01.png")
    card = _card({"output_path": "assets/prepared/SC-01-card.png"})
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 1
    assert "must be under assets/composed/" in qc.read_text()


# ── 8. quote_proof bottom_safe_margin_px < MIN fails ─────────────────────────

def test_quote_proof_bottom_margin_too_small_fails(tmp_path):
    _make_source_image(tmp_path / "assets/SC-02.png", w=752, h=4000)
    card = _card({
        "card_id": "SC-02",
        "card_type": "quote_proof",
        "source_path": "assets/SC-02.png",
        "crop": {"x": 0, "y": 0, "w": 752, "h": 315},
        "canvas": {
            "w": 752, "h": 422, "top_margin": 10,
            "bottom_safe_margin_px": MIN_QUOTE_PROOF_BOTTOM_MARGIN - 1,
        },
        "output_path": "assets/composed/SC-02-card.png",
    })
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 1
    text = qc.read_text()
    assert "bottom_safe_margin_px" in text


# ── 9. quote_proof insufficient computed bottom margin fails ──────────────────

def test_quote_proof_insufficient_computed_bottom_fails(tmp_path):
    # canvas_h=422, top_margin=10, crop_h=315 → computed_bottom=97
    # require 120 → should fail
    _make_source_image(tmp_path / "assets/SC-02.png", w=752, h=4000)
    card = _card({
        "card_id": "SC-02",
        "card_type": "quote_proof",
        "source_path": "assets/SC-02.png",
        "crop": {"x": 0, "y": 0, "w": 752, "h": 315},
        "canvas": {
            "w": 752, "h": 422, "top_margin": 10,
            "bottom_safe_margin_px": 120,
        },
        "output_path": "assets/composed/SC-02-card.png",
    })
    rc, qc = _run(_manifest([card]), tmp_path)
    assert rc == 1
    assert "computed bottom clear" in qc.read_text()


# ── 10. QC report written even on failure ────────────────────────────────────

def test_qc_report_written_on_failure(tmp_path):
    # source doesn't exist → failure
    rc, qc = _run(_manifest(), tmp_path)
    assert rc == 1
    assert qc.exists()
    text = qc.read_text()
    assert "FAIL" in text
    assert "## Failures" in text


# ── bonus: QC report structure on success ────────────────────────────────────

def test_qc_report_structure_on_success(tmp_path):
    _make_source_image(tmp_path / "assets/SC-01.png")
    rc, qc = _run(_manifest(), tmp_path)
    assert rc == 0
    text = qc.read_text()
    assert "PASS" in text
    assert "episode_id" in text or "test-episode" in text
    assert "## Failures" in text
    assert "(none)" in text
