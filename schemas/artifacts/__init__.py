"""Artifact schema loading and validation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_DIR = Path(__file__).parent

ARTIFACT_NAMES = [
    "research_brief",
    "transcript_index",
    "narration_claim_map",
    "source_candidate_manifest",
    "evidence_candidate_manifest",
    "clip_use_receipts",
    "extracted_clip_manifest",
    "approved_clip_manifest",
    "source_commentary_edit_plan",
    "source_commentary_render_report",
    "source_commentary_qc_report",
    "asymmetric_greenlight",
    "source_query_plan",
    "youtube_source_manifest",
    "source_capture_plan",
    "source_proof_manifest",
    "asymmetric_claim_map",
    "rights_risk_manifest",
    "visual_rhythm_plan",
    "source_segment_approval_manifest",
    "proposal_packet",
    "brief",
    "script",
    "character_design",
    "rig_plan",
    "pose_library",
    "scene_plan",
    "action_timeline",
    "asset_manifest",
    "edit_decisions",
    "render_report",
    "publish_log",
    "review",
    "cost_log",
    "decision_log",
    "source_media_review",
    "final_review",
    "character_qa_report",
    "video_analysis_brief",
]


def load_schema(name: str) -> dict:
    """Load a JSON schema by artifact name."""
    path = SCHEMA_DIR / f"{name}.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    with open(path) as f:
        return json.load(f)


def validate_artifact(name: str, data: dict[str, Any]) -> None:
    """Validate artifact data against its schema. Raises on failure."""
    schema = load_schema(name)
    jsonschema.validate(instance=data, schema=schema)


def list_schemas() -> list[str]:
    """List all available artifact schema names."""
    return [p.stem.replace(".schema", "") for p in SCHEMA_DIR.glob("*.schema.json")]
