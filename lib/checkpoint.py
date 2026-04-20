"""Checkpoint writer/reader for pipeline state persistence.

Each stage writes a checkpoint after completion. The orchestrator uses
checkpoints to resume pipelines and to present state at human checkpoints.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema

from schemas.artifacts import ARTIFACT_NAMES, validate_artifact

# All known stages across all pipelines (used only for artifact name lookup).
ALL_KNOWN_STAGES = frozenset([
    "research", "proposal", "idea", "script", "scene_plan",
    "assets", "edit", "compose", "publish",
])

# Backward-compatible alias — existing code / tests that import STAGES still work.
# New code should use get_pipeline_stages(pipeline_type) instead.
STAGES = ["research", "proposal", "idea", "script", "scene_plan",
          "assets", "edit", "compose", "publish"]

CANONICAL_STAGE_ARTIFACTS = {
    "research": "research_brief",
    "proposal": "proposal_packet",
    "idea": "brief",
    "script": "script",
    "scene_plan": "scene_plan",
    "assets": "asset_manifest",
    "edit": "edit_decisions",
    "compose": "render_report",
    "publish": "publish_log",
}

# Additional artifacts that may be produced alongside canonical ones.
# These are not stage-defining but are required by governance contracts.
SUPPLEMENTARY_ARTIFACTS = {
    "intent_contract",       # Editorial intent contract created during proposal
    "editorial_qa",          # Script QA gate covering title, time relevance, citations
    "source_media_review",  # Required before first planning stage when user media exists
    "final_review",         # Required by compose stage before presenting to user
    "video_analysis_brief", # Reference-video grounding artifact carried alongside stages
}

REQUIRED_SUPPLEMENTARY_ARTIFACTS_BY_STAGE = {
    "proposal": ("intent_contract",),
    "script": ("editorial_qa",),
    "compose": ("final_review",),
}

DEFAULT_ASSET_QUALITY_THRESHOLDS = {
    "max_fallback_runtime_ratio": 0.20,
    "max_consecutive_fallback_scenes": 2,
}

_TITLE_STOPWORDS = {
    "a", "an", "and", "at", "by", "could", "for", "from", "how", "if", "in",
    "is", "most", "of", "on", "or", "that", "the", "this", "to", "what", "why",
    "will", "with", "you", "your",
}

_HIGH_RISK_COMPLIANCE_TERMS = (
    "401", "finance", "financial", "invest", "ira", "legal", "medicare",
    "medical", "retire", "retirement", "social security", "tax",
)


def get_pipeline_stages(pipeline_type: str | None) -> list[str]:
    """Return the ordered stage list for a specific pipeline.

    Falls back to STAGES (deterministic canonical order) when pipeline_type
    is not provided or the manifest cannot be loaded.

    Previous versions used a set intersection here, which produced
    nondeterministic ordering. The fallback now uses a stable list.
    """
    if pipeline_type is None:
        # Deterministic canonical fallback — sorted to ensure stable ordering
        import logging
        logging.getLogger(__name__).warning(
            "get_pipeline_stages called without pipeline_type — "
            "using canonical fallback order. Pass pipeline_type for correctness."
        )
        return list(STAGES)

    try:
        from lib.pipeline_loader import load_pipeline, get_stage_order
        manifest = load_pipeline(pipeline_type)
        return get_stage_order(manifest)
    except (FileNotFoundError, Exception):
        # Graceful fallback: return all known stages in canonical order
        return list(STAGES)

CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "checkpoints"
    / "checkpoint.schema.json"
)


class CheckpointValidationError(ValueError):
    """Raised when a checkpoint or its canonical artifacts are invalid."""


@lru_cache(maxsize=1)
def _load_checkpoint_schema() -> dict[str, Any]:
    with open(CHECKPOINT_SCHEMA_PATH) as f:
        return json.load(f)


def _normalize_title_tokens(title: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", title.lower())
    normalized = []
    for token in tokens:
        if token in _TITLE_STOPWORDS:
            continue
        if re.fullmatch(r"\d{4}", token):
            continue
        normalized.append(token)
    return set(normalized)


def _title_similarity(anchor_title: str, script_title: str) -> float:
    anchor_tokens = _normalize_title_tokens(anchor_title)
    script_tokens = _normalize_title_tokens(script_title)
    if not anchor_tokens and not script_tokens:
        return 1.0
    if not anchor_tokens or not script_tokens:
        return 0.0
    overlap = anchor_tokens & script_tokens
    union = anchor_tokens | script_tokens
    return len(overlap) / len(union)


def _is_high_risk_script(script: dict[str, Any]) -> bool:
    text_chunks = [str(script.get("title", ""))]
    text_chunks.extend(str(section.get("text", "")) for section in script.get("sections", []))
    corpus = " ".join(text_chunks).lower()
    return any(term in corpus for term in _HIGH_RISK_COMPLIANCE_TERMS)


def _is_fallback_asset(asset: dict[str, Any]) -> bool:
    provider = str(asset.get("provider", "")).lower()
    subtype = str(asset.get("subtype", "")).lower()
    source_tool = str(asset.get("source_tool", "")).lower()
    summary = str(asset.get("generation_summary", "")).lower()
    if "fallback" in provider or provider in {"placeholder", "local_placeholder"}:
        return True
    if subtype == "fallback":
        return True
    if "fallback" in source_tool or "placeholder" in source_tool:
        return True
    return any(marker in summary for marker in ("fallback", "placeholder", "stock query failed"))


def _compute_asset_quality_gate(asset_manifest: dict[str, Any]) -> dict[str, Any]:
    assets = asset_manifest.get("assets", [])
    video_assets = [asset for asset in assets if asset.get("type") == "video"]
    total_runtime = sum(float(asset.get("duration_seconds") or 0.0) for asset in video_assets)
    fallback_assets = [asset for asset in video_assets if _is_fallback_asset(asset)]
    fallback_runtime = sum(float(asset.get("duration_seconds") or 0.0) for asset in fallback_assets)
    ratio = (fallback_runtime / total_runtime) if total_runtime > 0 else 0.0

    max_consecutive = 0
    current_run = 0
    for asset in video_assets:
        if _is_fallback_asset(asset):
            current_run += 1
            max_consecutive = max(max_consecutive, current_run)
        else:
            current_run = 0

    declared_thresholds = asset_manifest.get("quality_gate", {}).get("thresholds", {})
    thresholds = {
        "max_fallback_runtime_ratio": float(
            declared_thresholds.get(
                "max_fallback_runtime_ratio",
                DEFAULT_ASSET_QUALITY_THRESHOLDS["max_fallback_runtime_ratio"],
            )
        ),
        "max_consecutive_fallback_scenes": int(
            declared_thresholds.get(
                "max_consecutive_fallback_scenes",
                DEFAULT_ASSET_QUALITY_THRESHOLDS["max_consecutive_fallback_scenes"],
            )
        ),
    }

    blocked_reasons: list[str] = []
    if total_runtime > 0 and ratio > thresholds["max_fallback_runtime_ratio"]:
        blocked_reasons.append(
            f"Fallback runtime ratio {ratio:.1%} exceeds threshold "
            f"{thresholds['max_fallback_runtime_ratio']:.0%}"
        )
    if max_consecutive > thresholds["max_consecutive_fallback_scenes"]:
        blocked_reasons.append(
            f"Fallback run length {max_consecutive} exceeds threshold "
            f"{thresholds['max_consecutive_fallback_scenes']}"
        )

    return {
        "passed": not blocked_reasons,
        "fallback_video_count": len(fallback_assets),
        "total_video_count": len(video_assets),
        "fallback_runtime_seconds": round(fallback_runtime, 3),
        "total_video_runtime_seconds": round(total_runtime, 3),
        "fallback_runtime_ratio": round(ratio, 4),
        "max_consecutive_fallback_scenes": max_consecutive,
        "thresholds": thresholds,
        "blocked_reasons": blocked_reasons,
    }


def _validate_stage_supplementary_artifacts(
    stage: str,
    status: str,
    artifacts: dict[str, Any],
) -> None:
    if status not in {"completed", "awaiting_human"}:
        return
    for artifact_name in REQUIRED_SUPPLEMENTARY_ARTIFACTS_BY_STAGE.get(stage, ()):
        if artifact_name not in artifacts:
            raise CheckpointValidationError(
                f"Stage {stage!r} with status {status!r} must include "
                f"supplementary artifact {artifact_name!r}"
            )


def _validate_completed_script_editorial_qa(artifacts: dict[str, Any]) -> None:
    script = artifacts.get("script")
    editorial_qa = artifacts.get("editorial_qa")
    if not isinstance(script, dict) or not isinstance(editorial_qa, dict):
        return

    if editorial_qa.get("status") != "pass":
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed unless editorial_qa.status == 'pass'"
        )
    if editorial_qa.get("recommended_action") != "proceed":
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed unless editorial_qa.recommended_action == 'proceed'"
        )

    checks = editorial_qa.get("checks", {})
    title_alignment = checks.get("title_alignment", {})
    temporal_alignment = checks.get("temporal_alignment", {})
    citation_coverage = checks.get("citation_coverage", {})
    compliance = checks.get("compliance", {})

    anchor_title = str(title_alignment.get("anchor_title", ""))
    script_title = str(title_alignment.get("script_title", ""))
    actual_script_title = str(script.get("title", ""))
    if script_title != actual_script_title:
        raise CheckpointValidationError(
            "editorial_qa.checks.title_alignment.script_title must match script.title"
        )

    actual_similarity = _title_similarity(anchor_title, actual_script_title)
    declared_similarity = float(title_alignment.get("similarity_score", 0.0))
    if abs(actual_similarity - declared_similarity) > 0.15:
        raise CheckpointValidationError(
            "editorial_qa similarity score does not match the script/title pair closely enough"
        )

    temporal_policy = temporal_alignment.get("temporal_update_policy")
    if temporal_policy == "none" and anchor_title != actual_script_title:
        raise CheckpointValidationError(
            "temporal_update_policy='none' requires script.title to match anchor_title exactly"
        )
    if temporal_policy == "supporting_facts_only" and actual_similarity < 0.5:
        raise CheckpointValidationError(
            "supporting_facts_only scripts must preserve the anchor title promise closely"
        )
    if not title_alignment.get("policy_compliant", False):
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed when title_alignment.policy_compliant is false"
        )
    if not temporal_alignment.get("allowed_scope_respected", False):
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed when temporal_alignment.allowed_scope_respected is false"
        )

    sections = script.get("sections", [])
    total_sections = len(sections)
    sourced_sections = sum(1 for section in sections if section.get("source_ref"))
    actual_ratio = (sourced_sections / total_sections) if total_sections else 0.0
    declared_ratio = float(citation_coverage.get("coverage_ratio", 0.0))
    if citation_coverage.get("total_sections") != total_sections:
        raise CheckpointValidationError(
            "editorial_qa citation coverage total_sections must match the script"
        )
    if citation_coverage.get("sections_with_sources") != sourced_sections:
        raise CheckpointValidationError(
            "editorial_qa citation coverage sections_with_sources must match the script"
        )
    if abs(actual_ratio - declared_ratio) > 0.05:
        raise CheckpointValidationError(
            "editorial_qa citation coverage ratio does not match the script sections"
        )
    if total_sections > 0 and actual_ratio < 0.8:
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed when fewer than 80% of sections have source_ref"
        )

    if _is_high_risk_script(script) and compliance.get("topic_risk") == "high":
        if not compliance.get("financial_advice_disclaimer_present", False):
            raise CheckpointValidationError(
                "High-risk financial/medical/legal scripts must include a disclaimer in editorial_qa"
            )
    if compliance.get("outcome_overstatement_detected", False):
        raise CheckpointValidationError(
            "Stage 'script' cannot be completed while compliance flags outcome overstatement"
        )


def _validate_completed_asset_quality_gate(artifacts: dict[str, Any]) -> None:
    asset_manifest = artifacts.get("asset_manifest")
    if not isinstance(asset_manifest, dict):
        return

    assets = asset_manifest.get("assets", [])
    has_video_assets = any(asset.get("type") == "video" for asset in assets)
    if not has_video_assets:
        return

    declared_gate = asset_manifest.get("quality_gate")
    if not isinstance(declared_gate, dict):
        raise CheckpointValidationError(
            "Asset manifests with video assets must include a quality_gate"
        )

    computed_gate = _compute_asset_quality_gate(asset_manifest)
    for key in (
        "fallback_video_count",
        "total_video_count",
        "max_consecutive_fallback_scenes",
    ):
        if int(declared_gate.get(key, -1)) != int(computed_gate[key]):
            raise CheckpointValidationError(
                f"asset_manifest quality_gate.{key} does not match computed asset quality stats"
            )
    for key in (
        "fallback_runtime_seconds",
        "total_video_runtime_seconds",
        "fallback_runtime_ratio",
    ):
        if abs(float(declared_gate.get(key, -1.0)) - float(computed_gate[key])) > 0.01:
            raise CheckpointValidationError(
                f"asset_manifest quality_gate.{key} does not match computed asset quality stats"
            )
    if declared_gate.get("thresholds") != computed_gate["thresholds"]:
        raise CheckpointValidationError(
            "asset_manifest quality_gate.thresholds must match the declared thresholds used for validation"
        )
    if bool(declared_gate.get("passed")) != bool(computed_gate["passed"]):
        raise CheckpointValidationError(
            "asset_manifest quality_gate.passed does not match computed asset quality result"
        )
    if list(declared_gate.get("blocked_reasons", [])) != computed_gate["blocked_reasons"]:
        raise CheckpointValidationError(
            "asset_manifest quality_gate.blocked_reasons does not match computed asset quality result"
        )
    if not computed_gate["passed"]:
        raise CheckpointValidationError(
            "Stage 'assets' cannot be completed while the asset quality gate is failing"
        )


def _validate_completed_compose_review(artifacts: dict[str, Any]) -> None:
    final_review = artifacts.get("final_review")
    if not isinstance(final_review, dict):
        return
    if final_review.get("status") != "pass":
        raise CheckpointValidationError(
            "Stage 'compose' cannot be completed unless final_review.status == 'pass'"
        )
    if final_review.get("recommended_action") != "present_to_user":
        raise CheckpointValidationError(
            "Stage 'compose' cannot be completed unless final_review.recommended_action == 'present_to_user'"
        )


def _validate_artifacts_for_stage(
    stage: str,
    status: str,
    artifacts: dict[str, Any],
) -> None:
    required_artifact = CANONICAL_STAGE_ARTIFACTS[stage]
    if status in {"completed", "awaiting_human"} and required_artifact not in artifacts:
        raise CheckpointValidationError(
            f"Stage {stage!r} with status {status!r} must include "
            f"canonical artifact {required_artifact!r}"
        )

    _validate_stage_supplementary_artifacts(stage, status, artifacts)

    for artifact_name, artifact_data in artifacts.items():
        if artifact_name not in ARTIFACT_NAMES:
            continue
        if not isinstance(artifact_data, dict):
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} must be a JSON object matching its schema"
            )
        try:
            validate_artifact(artifact_name, artifact_data)
        except Exception as exc:
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} failed schema validation: {exc}"
            ) from exc

    if status == "completed":
        if stage == "script":
            _validate_completed_script_editorial_qa(artifacts)
        if stage == "assets":
            _validate_completed_asset_quality_gate(artifacts)
        if stage == "compose":
            _validate_completed_compose_review(artifacts)


def validate_checkpoint(checkpoint: dict[str, Any]) -> None:
    """Validate checkpoint structure and canonical artifact payloads.

    Uses pipeline_type (if present) to resolve the valid stage list.
    Falls back to ALL_KNOWN_STAGES when pipeline_type is absent.
    """
    stage = checkpoint.get("stage")
    status = checkpoint.get("status")
    artifacts = checkpoint.get("artifacts")
    pipeline_type = checkpoint.get("pipeline_type")

    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )

    if not isinstance(stage, str) or stage not in valid_stages:
        raise CheckpointValidationError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )
    if not isinstance(status, str):
        raise CheckpointValidationError(f"Invalid status: {status!r}")
    if not isinstance(artifacts, dict):
        raise CheckpointValidationError("Checkpoint artifacts must be a dictionary")

    _validate_artifacts_for_stage(stage, status, artifacts)

    try:
        jsonschema.validate(instance=checkpoint, schema=_load_checkpoint_schema())
    except jsonschema.ValidationError as exc:
        raise CheckpointValidationError(f"Checkpoint failed schema validation: {exc.message}") from exc


def _checkpoint_path(pipeline_dir: Path, project_id: str, stage: str) -> Path:
    return pipeline_dir / project_id / f"checkpoint_{stage}.json"


def _decision_log_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / "decision_log.json"


def _merge_decision_log(
    pipeline_dir: Path, project_id: str, new_log: dict[str, Any]
) -> None:
    """Append new decisions to the project-level decision log.

    Each stage may produce decisions. This function merges them into a
    single cumulative file so reviewers and the bench can inspect the
    full audit trail.
    """
    path = _decision_log_path(pipeline_dir, project_id)
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    else:
        existing = {
            "version": "1.0",
            "project_id": project_id,
            "decisions": [],
        }

    existing_ids = {d["decision_id"] for d in existing.get("decisions", [])}
    for decision in new_log.get("decisions", []):
        if decision.get("decision_id") not in existing_ids:
            existing["decisions"].append(decision)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def write_checkpoint(
    pipeline_dir: Path,
    project_id: str,
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    *,
    pipeline_type: Optional[str] = None,
    style_playbook: Optional[str] = None,
    checkpoint_policy: str = "guided",
    human_approval_required: bool = False,
    human_approved: bool = False,
    review: Optional[dict] = None,
    cost_snapshot: Optional[dict] = None,
    error: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Path:
    """Write a checkpoint file for a pipeline stage."""
    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )
    if stage not in valid_stages:
        raise ValueError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )

    checkpoint = {
        "version": "1.0",
        "project_id": project_id,
        "pipeline_type": pipeline_type or "unknown",
        "stage": stage,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint_policy": checkpoint_policy,
        "human_approval_required": human_approval_required,
        "human_approved": human_approved,
        "artifacts": artifacts,
    }
    if style_playbook is not None:
        checkpoint["style_playbook"] = style_playbook
    if review is not None:
        checkpoint["review"] = review
    if cost_snapshot is not None:
        checkpoint["cost_snapshot"] = cost_snapshot
    if error is not None:
        checkpoint["error"] = error
    if metadata is not None:
        checkpoint["metadata"] = metadata

    # Merge decision_log: if this checkpoint carries new decisions,
    # append them to the project-level decision log file, then write the
    # reference back into relevant artifacts so downstream consumers can find it.
    if "decision_log" in artifacts and isinstance(artifacts["decision_log"], dict):
        _merge_decision_log(pipeline_dir, project_id, artifacts["decision_log"])
        log_ref = str(_decision_log_path(pipeline_dir, project_id))

        # Write decision_log_ref into proposal_packet and render_report
        # artifacts if they are present in this checkpoint.
        for artifact_key in ("proposal_packet", "render_report"):
            if artifact_key in artifacts and isinstance(artifacts[artifact_key], dict):
                plan_or_top = artifacts[artifact_key]
                # proposal_packet stores it under production_plan
                if artifact_key == "proposal_packet":
                    plan = plan_or_top.get("production_plan")
                    if isinstance(plan, dict):
                        plan["decision_log_ref"] = log_ref
                else:
                    plan_or_top["decision_log_ref"] = log_ref

    validate_checkpoint(checkpoint)

    path = _checkpoint_path(pipeline_dir, project_id, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return path


def read_checkpoint(
    pipeline_dir: Path, project_id: str, stage: str
) -> Optional[dict[str, Any]]:
    """Read a checkpoint file. Returns None if not found."""
    path = _checkpoint_path(pipeline_dir, project_id, stage)
    if not path.exists():
        return None
    with open(path) as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_latest_checkpoint(
    pipeline_dir: Path, project_id: str
) -> Optional[dict[str, Any]]:
    """Find the most recent checkpoint for a project (by file mtime)."""
    project_dir = pipeline_dir / project_id
    if not project_dir.exists():
        return None

    checkpoints = sorted(
        project_dir.glob("checkpoint_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not checkpoints:
        return None

    with open(checkpoints[0]) as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_completed_stages(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> list[str]:
    """Return list of stages that have a completed checkpoint.

    When pipeline_type is provided, only checks stages defined in that
    pipeline's manifest — preventing false positives from leftover
    checkpoints of a different pipeline type.
    """
    stages_to_check = get_pipeline_stages(pipeline_type)
    completed = []
    for stage in stages_to_check:
        cp = read_checkpoint(pipeline_dir, project_id, stage)
        if cp and cp.get("status") == "completed":
            completed.append(stage)
    return completed


def get_next_stage(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> Optional[str]:
    """Determine the next stage to run based on completed checkpoints.

    Uses pipeline-specific stage order so that pipelines with different
    stage sequences (e.g. cinematic vs explainer) progress correctly.
    """
    stages = get_pipeline_stages(pipeline_type) if pipeline_type else STAGES
    completed = set(get_completed_stages(pipeline_dir, project_id, pipeline_type))
    for stage in stages:
        if stage not in completed:
            return stage
    return None
