"""Schema validation tests for broadcast-explainer artifact schemas."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest
import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas" / "artifacts"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())


# ── audio_timing ──────────────────────────────────────────────────────────────

VALID_AUDIO_TIMING = {
    "version": "1.0",
    "total_duration_seconds": 54.94,
    "sections": [
        {"id": "s01_hook",  "start": 0.0,   "end": 3.855,  "duration": 3.855},
        {"id": "s02_scale", "start": 3.855, "end": 17.229, "duration": 13.374},
    ],
}


def test_audio_timing_valid():
    schema = load_schema("audio_timing")
    jsonschema.validate(VALID_AUDIO_TIMING, schema)


def test_audio_timing_missing_sections():
    schema = load_schema("audio_timing")
    bad = {**VALID_AUDIO_TIMING}
    del bad["sections"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_audio_timing_section_missing_id():
    schema = load_schema("audio_timing")
    bad = {
        **VALID_AUDIO_TIMING,
        "sections": [{"start": 0.0, "end": 3.855, "duration": 3.855}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_audio_timing_negative_duration():
    schema = load_schema("audio_timing")
    bad = {
        **VALID_AUDIO_TIMING,
        "sections": [{"id": "s01_hook", "start": 0.0, "end": 3.855, "duration": -1.0}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


# ── qa_report ─────────────────────────────────────────────────────────────────

VALID_QA_REPORT_PASS = {
    "version": "1.0",
    "passed": True,
    "lint": {"errors": 0, "warnings": 1},
    "validate": {"contrast_failures": []},
    "animation_map": {"flags": [], "dead_zones": []},
    "issues": [],
    "warnings": ["File size 348 lines exceeds recommendation"],
}

VALID_QA_REPORT_FAIL = {
    "version": "1.0",
    "passed": False,
    "lint": {"errors": 0, "warnings": 0},
    "validate": {"contrast_failures": []},
    "animation_map": {"flags": [], "dead_zones": []},
    "issues": [
        {
            "severity": "block",
            "type": "animation_map_offscreen",
            "element": "#axiom-layer #mouth-open",
            "description": "Element offscreen during speech section s02_scale",
        }
    ],
    "warnings": [],
}


def test_qa_report_pass_valid():
    schema = load_schema("qa_report")
    jsonschema.validate(VALID_QA_REPORT_PASS, schema)


def test_qa_report_fail_valid():
    schema = load_schema("qa_report")
    jsonschema.validate(VALID_QA_REPORT_FAIL, schema)


def test_qa_report_missing_passed():
    schema = load_schema("qa_report")
    bad = {**VALID_QA_REPORT_PASS}
    del bad["passed"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_qa_report_invalid_severity():
    schema = load_schema("qa_report")
    bad = {
        **VALID_QA_REPORT_FAIL,
        "issues": [{"severity": "critical", "type": "x", "element": "y", "description": "z"}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
