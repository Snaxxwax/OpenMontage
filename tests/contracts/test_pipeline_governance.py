from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_SCHEMA = ROOT / "schemas/pipelines/pipeline_manifest.schema.json"


REQUIRED_STAGE_FIELDS = {
    "name",
    "skill",
    "produces",
    "tools_available",
    "checkpoint_required",
    "human_approval_default",
    "review_focus",
    "success_criteria",
}

FORBIDDEN_STAGE_FIELDS = {
    # These were used by the prototype/thin manifest and encourage hidden script flow.
    "output",
    "provider",
    "lifecycle",
    "should_run_check",
    "saved_assets_policy",
    "notes",
}

FORBIDDEN_PYTHON_ORCHESTRATION_TERMS = {
    "checkpoint_required",
    "human_approval_default",
    "approval.status",
    "auto_select_first",
    "auto-select-first",
}

ALLOWED_SCRIPT_EXCEPTIONS = set()


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))



def test_pipeline_schema_supports_explicit_subagent_review_lanes() -> None:
    schema = json.loads(PIPELINE_SCHEMA.read_text(encoding="utf-8"))
    minimal_manifest = {
        "name": "review-lane-fixture",
        "version": "1.0",
        "subagent_policy": {
            "enabled": True,
            "decision_owner": "executive_producer",
            "nested_subagents_allowed": False,
            "max_parallel": 3,
            "completion_contract_required": True,
            "main_session_verifies_outputs": True,
            "blocker_handling": "surface_to_operator",
        },
        "stages": [
            {
                "name": "research",
                "skill": "channels/example/skills/research-director.md",
                "produces": ["research_packet"],
                "tools_available": [],
                "checkpoint_required": True,
                "human_approval_default": False,
                "review_focus": ["evidence quality"],
                "success_criteria": ["research packet exists"],
                "subagents": [
                    {
                        "name": "evidence_auditor",
                        "skill": "channels/example/skills/review/evidence-auditor.md",
                        "mode": "blocking",
                        "trigger": "after_stage_output",
                        "completion_contract": "agent_gate_report",
                        "review_focus": ["claim traceability"],
                    }
                ],
            }
        ],
    }

    Draft202012Validator(schema).validate(minimal_manifest)



def iter_project_scripts() -> list[Path]:
    roots = [ROOT / "scripts"]
    paths: list[Path] = []
    for base in roots:
        if base.exists():
            paths.extend(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)
    return paths


@pytest.mark.parametrize("script", iter_project_scripts())
def test_scripts_do_not_encode_pipeline_governance_terms(script: Path) -> None:
    if script in ALLOWED_SCRIPT_EXCEPTIONS:
        return

    text = script.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        pytest.fail(f"script has syntax error: {script}")

    literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    haystack = "\n".join(literals)
    offenders = sorted(term for term in FORBIDDEN_PYTHON_ORCHESTRATION_TERMS if term in haystack)
    assert not offenders, (
        f"{script.relative_to(ROOT)} appears to encode pipeline governance terms {offenders}. "
        "Move orchestration/checkpoint/approval/promotion policy into YAML manifests and director skills."
    )
