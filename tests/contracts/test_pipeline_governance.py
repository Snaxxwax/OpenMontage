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
MODERN_ARCHIVIST_PIPELINE = ROOT / "channels/modern-archivist/pipeline.yaml"
RUN_ASSET_GENERATION = ROOT / "scripts/comfyui/run_asset_generation.py"

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

ALLOWED_SCRIPT_EXCEPTIONS = {
    ROOT / "scripts/comfyui/run_asset_generation.py",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_modern_archivist_pipeline_is_full_manifest() -> None:
    manifest = load_yaml(MODERN_ARCHIVIST_PIPELINE)
    schema = json.loads(PIPELINE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(manifest)

    for top_level in [
        "version",
        "category",
        "stability",
        "default_checkpoint_policy",
        "orchestration",
        "required_skills",
        "extensions",
        "stages",
    ]:
        assert top_level in manifest

    for stage in manifest["stages"]:
        missing = REQUIRED_STAGE_FIELDS - set(stage)
        assert not missing, f"stage {stage.get('name')} is missing required contract fields: {sorted(missing)}"
        forbidden = FORBIDDEN_STAGE_FIELDS & set(stage)
        assert not forbidden, f"stage {stage.get('name')} still has prototype/script-flow fields: {sorted(forbidden)}"
        assert stage["produces"], f"stage {stage['name']} must declare produced artifacts"
        assert stage["review_focus"], f"stage {stage['name']} must declare review focus"
        assert stage["success_criteria"], f"stage {stage['name']} must declare success criteria"


def test_modern_archivist_required_skills_exist() -> None:
    manifest = load_yaml(MODERN_ARCHIVIST_PIPELINE)
    for skill_ref in manifest["required_skills"]:
        if skill_ref.startswith("meta/"):
            path = ROOT / "skills" / f"{skill_ref}.md"
        else:
            path = ROOT / skill_ref
        assert path.exists(), f"required skill missing: {skill_ref} -> {path}"


def test_modern_archivist_manifest_does_not_route_through_deprecated_runner() -> None:
    text = MODERN_ARCHIVIST_PIPELINE.read_text(encoding="utf-8")
    manifest = load_yaml(MODERN_ARCHIVIST_PIPELINE)

    assert "run_asset_generation.py" not in text or "deprecated_orchestration_shim" in text

    asset_stage = next(stage for stage in manifest["stages"] if stage["name"] == "asset_generation")
    assert asset_stage["skill"] == "channels/modern-archivist/skills/asset-generation-director.md"
    for routing_field in ["required_tools", "optional_tools", "tools_available"]:
        assert "run_asset_generation.py" not in asset_stage.get(routing_field, [])
    for legacy_field in ["provider", "lifecycle", "should_run_check", "saved_assets_policy", "output"]:
        assert legacy_field not in asset_stage


def test_deprecated_runner_blocks_non_dry_run_without_explicit_override() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUN_ASSET_GENERATION), "--intent", "expression_sheet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "blocked"
    assert "deprecated" in payload["reason"]


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
