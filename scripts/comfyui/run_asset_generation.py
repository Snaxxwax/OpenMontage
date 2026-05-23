#!/usr/bin/env python3
"""DEPRECATED legacy ComfyUI asset-generation orchestration shim.

Do not use this script as the Modern Archivist `asset_generation` pipeline.
The pipeline contract lives in `channels/modern-archivist/pipeline.yaml` and
`channels/modern-archivist/skills/asset-generation-director.md`.

This file is retained only as a temporary compatibility helper for manually
submitting an already-approved ComfyUI workflow. It must not choose pipeline
intent, provider, checkpoint policy, review policy, or asset promotion. Normal
stage execution should use:

- `asset_generation_needed.py` as a read-only saved-assets preflight utility.
- `ensure_comfyui_docker.py` as a narrow lifecycle utility (`status|ensure|free`).
- The stage director skill for orchestration and approval decisions.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL_RUN_BATCH = Path("/home/pop/.hermes/skills/creative/comfyui/scripts/run_batch.py")
ASSET_NEED = ROOT / "scripts" / "comfyui" / "asset_generation_needed.py"
ENSURE_COMFY = ROOT / "scripts" / "comfyui" / "ensure_comfyui_docker.py"
REQS = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows" / "asset_requirements.yaml"
TEMPLATES = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows" / "prompts" / "asset_sheet_prompt_templates.json"
STYLE = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows" / "prompts" / "modern_archivist_style.md"
NEGATIVE = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows" / "prompts" / "negative_prompt.md"
WORKFLOW_DIR = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows"
OUTPUT_ROOT = ROOT / "channels" / "modern-archivist" / "assets" / "source" / "comfyui_generated"

DEFAULT_WORKFLOWS = {
    "expression_sheet": WORKFLOW_DIR / "expression_sheet_sdxl_ipadapter_api.json",
    "mouth_phonemes": WORKFLOW_DIR / "mouth_phonemes_sdxl_ipadapter_api.json",
    "arm_mug_poses": WORKFLOW_DIR / "arm_mug_poses_sdxl_ipadapter_api.json",
    "props": WORKFLOW_DIR / "props_sdxl_api.json",
    "archive_background": WORKFLOW_DIR / "archive_background_sdxl_api.json",
    "thumbnail_base": WORKFLOW_DIR / "thumbnail_base_sdxl_api.json",
}

SELECTED_OUTPUTS = {
    "expression_sheet": OUTPUT_ROOT / "selected" / "modern_archivist_expression_sheet.png",
    "mouth_phonemes": OUTPUT_ROOT / "selected" / "modern_archivist_mouth_phoneme_sheet.png",
    "arm_mug_poses": OUTPUT_ROOT / "selected" / "modern_archivist_arm_mug_pose_sheet.png",
    "props": OUTPUT_ROOT / "selected" / "failure_ledger_props_sheet.png",
    "archive_background": OUTPUT_ROOT / "selected" / "failure_ledger_archive_room_background.png",
    "thumbnail_base": OUTPUT_ROOT / "selected" / "failure_ledger_thumbnail_base.png",
}


def run(cmd: list[str], *, timeout: int = 600, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def need_check(intent: str) -> dict[str, Any]:
    proc = run([sys.executable, str(ASSET_NEED), "--intent", intent, "--pretty"], timeout=60)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"asset need check did not return JSON: {proc.stdout}\n{proc.stderr}") from exc
    payload["exit_code"] = proc.returncode
    return payload


def workflow_is_api_format(path: Path) -> bool:
    try:
        data = load_json(path)
    except Exception:
        return False
    if not isinstance(data, dict) or not data:
        return False
    return all(isinstance(v, dict) and "class_type" in v for v in data.values())


def template_for_intent(intent: str) -> tuple[str, dict[str, Any]]:
    reqs = load_yaml(REQS)
    intents = reqs.get("generation_intents", {})
    if intent not in intents:
        raise KeyError(f"Unknown intent {intent!r}; known: {sorted(intents)}")
    template_name = intents[intent]["template"]
    templates = load_json(TEMPLATES)
    if template_name not in templates:
        raise KeyError(f"Intent {intent!r} maps to missing template {template_name!r}")
    return template_name, templates[template_name]


def build_args(intent: str, *, steps: int) -> dict[str, Any]:
    _, template = template_for_intent(intent)
    style = STYLE.read_text(encoding="utf-8").strip()
    negative = NEGATIVE.read_text(encoding="utf-8").strip()
    return {
        "prompt": f"{style}\n\n{template['prompt']}",
        "negative_prompt": negative,
        "steps": steps,
        "seed": -1,
    }


def output_dir_for(intent: str) -> Path:
    _, template = template_for_intent(intent)
    subdir = template.get("output_subdir") or f"raw/{intent}"
    out = OUTPUT_ROOT / subdir
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_manifest(intent: str, payload: dict[str, Any]) -> Path:
    manifest_dir = OUTPUT_ROOT / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"{intent}_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def extract_output_files(payload: Any) -> list[Path]:
    files: list[Path] = []
    def visit(x: Any) -> None:
        if isinstance(x, dict):
            value = x.get("file") or x.get("path")
            if isinstance(value, str):
                p = Path(value)
                files.append(p if p.is_absolute() else ROOT / p)
            for v in x.values():
                visit(v)
        elif isinstance(x, list):
            for v in x:
                visit(v)
    visit(payload)
    return [p for p in files if p.exists() and p.is_file()]


def run_generation(intent: str, workflow: Path, *, count: int, steps: int, auto_select_first: bool, dry_run: bool) -> dict[str, Any]:
    need = need_check(intent)
    if not need.get("needs_generation"):
        return {"status": "skipped", "reason": "saved assets satisfy requested intent", "need_check": need}

    if not workflow.exists():
        return {
            "status": "blocked",
            "reason": "missing executable ComfyUI API workflow for requested intent",
            "intent": intent,
            "expected_workflow": str(workflow.relative_to(ROOT) if workflow.is_relative_to(ROOT) else workflow),
            "need_check": need,
            "next_step": "Create/export the workflow in ComfyUI API format, then rerun this command.",
        }
    if not workflow_is_api_format(workflow):
        return {
            "status": "blocked",
            "reason": "workflow exists but is not ComfyUI API format; export with Workflow -> Export (API)",
            "workflow": str(workflow),
            "need_check": need,
        }

    args = build_args(intent, steps=steps)
    out_dir = output_dir_for(intent)
    if dry_run:
        return {
            "status": "dry_run",
            "would_generate": True,
            "intent": intent,
            "workflow": str(workflow),
            "count": count,
            "output_dir": str(out_dir),
            "args": args,
            "need_check": need,
        }

    ensure = run([sys.executable, str(ENSURE_COMFY), "ensure"], timeout=360)
    if ensure.returncode != 0:
        return {"status": "blocked", "reason": "ComfyUI lifecycle ensure failed", "ensure_stdout": ensure.stdout, "ensure_stderr": ensure.stderr, "need_check": need}

    cmd = [
        sys.executable,
        str(SKILL_RUN_BATCH),
        "--workflow",
        str(workflow),
        "--args",
        json.dumps(args),
        "--count",
        str(count),
        "--randomize-seed",
        "--output-dir",
        str(out_dir),
    ]
    started = time.time()
    proc = run(cmd, timeout=1800)
    duration = time.time() - started
    free_proc = run([sys.executable, str(ENSURE_COMFY), "free"], timeout=60)

    try:
        run_payload: Any = json.loads(proc.stdout)
    except json.JSONDecodeError:
        run_payload = {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode}
    output_files = extract_output_files(run_payload)

    selected = None
    if auto_select_first and output_files:
        dest = SELECTED_OUTPUTS[intent]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_files[0], dest)
        selected = str(dest)

    manifest_payload = {
        "intent": intent,
        "workflow": str(workflow),
        "count": count,
        "steps": steps,
        "output_dir": str(out_dir),
        "duration_seconds": duration,
        "run_exit_code": proc.returncode,
        "run_stdout_json": run_payload,
        "run_stderr": proc.stderr,
        "outputs": [str(p) for p in output_files],
        "selected": selected,
        "free_exit_code": free_proc.returncode,
        "free_stdout": free_proc.stdout,
        "free_stderr": free_proc.stderr,
        "need_check_before": need,
        "need_check_after": need_check(intent),
    }
    manifest_path = write_manifest(intent, manifest_payload)
    manifest_payload["manifest_path"] = str(manifest_path)
    return {"status": "success" if proc.returncode == 0 else "error", **manifest_payload}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", required=True, choices=sorted(DEFAULT_WORKFLOWS))
    parser.add_argument("--workflow", type=Path, help="Override API-format workflow path")
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--auto-select-first", action="store_true", help="Deprecated compatibility option; do not use for pipeline promotion")
    parser.add_argument(
        "--allow-deprecated-orchestration",
        action="store_true",
        help="Required for non-dry-run execution. Confirms this is a manual compatibility call, not pipeline orchestration.",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.allow_deprecated_orchestration:
        print(json.dumps({
            "status": "blocked",
            "reason": "run_asset_generation.py is deprecated as pipeline orchestration; use the Modern Archivist asset-generation director and pass --allow-deprecated-orchestration only for an already-approved manual compatibility call.",
        }, indent=2, sort_keys=True))
        return 2

    workflow = args.workflow or DEFAULT_WORKFLOWS[args.intent]
    if not workflow.is_absolute():
        workflow = ROOT / workflow
    result = run_generation(args.intent, workflow, count=args.count, steps=args.steps, auto_select_first=args.auto_select_first, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"success", "skipped", "dry_run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
