"""Contract tests for source_card_manifest.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas/artifacts/source_card_manifest.schema.json"
)
SCHEMA = json.loads(SCHEMA_PATH.read_text())


def _validate(manifest: dict) -> None:
    jsonschema.validate(manifest, SCHEMA)


def _card(overrides: dict | None = None, **kw) -> dict:
    base = {
        "card_id": "SC-01",
        "card_type": "article_header",
        "source_path": "assets/SC-01.png",
        "crop": {"x": 0, "y": 0, "w": 752, "h": 422},
        "canvas": {"w": 752, "h": 422, "top_margin": 10},
        "output_path": "assets/composed/SC-01-card.png",
    }
    if overrides:
        base.update(overrides)
    base.update(kw)
    return base


def _manifest(cards: list | None = None, **kw) -> dict:
    base = {"episode_id": "test-episode", "cards": cards if cards is not None else [_card()]}
    base.update(kw)
    return base


# ── pass cases ────────────────────────────────────────────────────────────────

def test_valid_article_header_passes():
    _validate(_manifest([_card({"card_type": "article_header"})]))


def test_valid_quote_proof_passes():
    _validate(_manifest([_card({
        "card_type": "quote_proof",
        "card_id": "SC-02",
        "source_path": "assets/SC-02.png",
        "crop": {"x": 0, "y": 2700, "w": 752, "h": 315},
        "canvas": {"w": 752, "h": 422, "top_margin": 10, "bottom_safe_margin_px": 97},
        "output_path": "assets/composed/SC-02-card.png",
    })]))


def test_optional_bottom_safe_margin_accepted():
    card = _card({"canvas": {"w": 752, "h": 422, "top_margin": 10, "bottom_safe_margin_px": 120}})
    _validate(_manifest([card]))


def test_multiple_cards_passes():
    cards = [
        _card({"card_id": "SC-01", "output_path": "assets/composed/SC-01-card.png"}),
        _card({"card_id": "SC-02", "card_type": "quote_proof", "output_path": "assets/composed/SC-02-card.png"}),
    ]
    _validate(_manifest(cards))


# ── fail cases ────────────────────────────────────────────────────────────────

def test_missing_cards_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate({"episode_id": "test"})


def test_empty_cards_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest(cards=[]))


def test_invalid_card_type_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([_card({"card_type": "screenshot"})]))


def test_missing_crop_fails():
    card = _card()
    del card["crop"]
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([card]))


def test_crop_zero_width_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([_card({"crop": {"x": 0, "y": 0, "w": 0, "h": 422}})]))


def test_crop_zero_height_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([_card({"crop": {"x": 0, "y": 0, "w": 752, "h": 0}})]))


def test_output_path_with_dotdot_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([_card({"output_path": "assets/composed/../SC-01-card.png"})]))


def test_output_path_outside_assets_composed_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate(_manifest([_card({"output_path": "assets/prepared/SC-01-card.png"})]))


def test_missing_episode_id_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate({"cards": [_card()]})
