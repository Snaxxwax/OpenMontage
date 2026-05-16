"""Contract tests for publish_package.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas" / "artifacts" / "publish_package.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(pkg: dict) -> list[str]:
    return [e.message for e in Draft7Validator(_schema()).iter_errors(pkg)]


# ── fixture builder ───────────────────────────────────────────────────────────

def _package(**overrides) -> dict:
    base = {
        "version": "1.0",
        "episode_id": "cloudflare-chokepoint-test",
        "render_path": "renders/example.mp4",
        "duration_seconds": 72.006,
        "package_status": "pending_review",
        "generated_at": "2026-05-15T23:00:00Z",
        "title_options": [
            {
                "title": "Example title",
                "pillar": "Hidden Control",
                "why": "Why this title works",
            }
        ],
        "description": "Paste-ready YouTube description.",
        "tags": ["ai security", "infrastructure"],
        "chapters": [
            {"timecode": "0:00", "label": "Opening claim"}
        ],
        "thumbnail_brief": {
            "variant": "power",
            "hero_object": "Cloudflare logo over infrastructure map",
            "signal_color": "#F5A400",
            "headline_text": "WHO CONTROLS THIS?",
            "composition_notes": "Large readable text, one focal object, no clutter.",
        },
        "source_credits": [
            "Source: Cloudflare Blog / Matthew Prince, August 5, 2019"
        ],
    }
    base.update(overrides)
    return base


# ── pass tests ────────────────────────────────────────────────────────────────

def test_valid_full_package_passes():
    assert _validate(_package()) == []


def test_package_status_pending_review_passes():
    assert _validate(_package(package_status="pending_review")) == []


def test_package_status_approved_passes():
    assert _validate(_package(package_status="approved")) == []


# ── fail tests ────────────────────────────────────────────────────────────────

def test_missing_title_options_fails():
    pkg = _package()
    del pkg["title_options"]
    assert _validate(pkg), "expected error for missing title_options"


def test_missing_source_credits_fails():
    pkg = _package()
    del pkg["source_credits"]
    assert _validate(pkg), "expected error for missing source_credits"


def test_missing_thumbnail_brief_fails():
    pkg = _package()
    del pkg["thumbnail_brief"]
    assert _validate(pkg), "expected error for missing thumbnail_brief"


def test_empty_title_options_fails():
    pkg = _package(title_options=[])
    assert _validate(pkg), "expected error for empty title_options"


def test_empty_source_credits_fails():
    pkg = _package(source_credits=[])
    assert _validate(pkg), "expected error for empty source_credits"
