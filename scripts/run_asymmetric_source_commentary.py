#!/usr/bin/env python3
"""Run the Asymmetric source-commentary production contract in fixture mode."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from lib.artifact_bus import ArtifactBus, DEFAULT_PROJECTS_DIR
from lib.asymmetric_gate_policy import GatePolicy
from lib.pipeline_contract import PipelineContract
from lib.pipeline_run import PipelineRun, PipelineRunMode, RenderPhaseResult, RunContext, StageOutcome

DEFAULT_COMFY_HOST = "http://100.70.12.4:8188"
REQUIRED_COMFY_NODE_CLASSES = {
    "FishS2TTS",
    "SaveAudioMP3",
    "UNETLoader",
    "DualCLIPLoader",
    "TextEncodeAceStepAudio1.5",
    "EmptyAceStep1.5LatentAudio",
    "KSampler",
    "VAELoader",
    "VAEDecodeAudio",
}

PIPELINE_ID = "asymmetric-source-commentary"
PIPELINE_CONTRACT = PipelineContract.load(PIPELINE_ID)
ARTIFACT_SCHEMAS = {
    artifact_name: schema_path.name
    for artifact_name, schema_path in PIPELINE_CONTRACT.artifact_schemas.items()
}


class PipelineError(RuntimeError):
    """Expected operator-facing pipeline failure."""


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def resolve_comfy_host(raw: str | None = None) -> str:
    return raw or os.environ.get("COMFYUI_SERVER_URL") or DEFAULT_COMFY_HOST


def run_paths(base_dir: Path, episode_id: str) -> ArtifactBus:
    return ArtifactBus.for_project(episode_id, projects_dir=base_dir)


def ensure_dirs(paths: ArtifactBus) -> None:
    paths.ensure_dirs()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"JSON file must contain an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def check_python_module(module_name: str) -> tuple[bool, str]:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return False, f"missing Python module: {module_name}"
    return True, str(spec.origin or "built-in")


def check_command(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    if not path:
        return False, f"{name} not found on PATH"
    return True, path


def fetch_comfy_object_info(host: str) -> dict[str, Any]:
    try:
        response = requests.get(host.rstrip("/") + "/object_info", timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise PipelineError(f"ComfyUI is not reachable at {host}: {exc}") from exc
    except ValueError as exc:
        raise PipelineError(f"ComfyUI returned non-JSON /object_info at {host}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"ComfyUI /object_info must return an object at {host}")
    return data


def preflight(*, comfy_host: str, check_comfy: bool = True) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, **data: Any) -> None:
        checks.append({"name": name, "ok": ok, **data})

    for module in ["yaml", "jsonschema", "requests"]:
        ok, detail = check_python_module(module)
        add(f"python_module_{module}", ok, detail=detail)

    ok, detail = check_python_module("tools._comfyui.client")
    add("python_module_tools._comfyui.client", ok, detail=detail)

    for command in ["ffmpeg", "ffprobe"]:
        ok, detail = check_command(command)
        add(command, ok, detail=detail)

    try:
        yaml.safe_load(PIPELINE_CONTRACT.path.read_text(encoding="utf-8"))
        yaml.safe_load((REPO_ROOT / "styles/asymmetric.yaml").read_text(encoding="utf-8"))
        add("yaml_files", True)
    except Exception as exc:
        add("yaml_files", False, error=str(exc))

    contract_issues = PIPELINE_CONTRACT.validate_references()
    add("pipeline_contract_references", True, issues=contract_issues)

    for schema_name in ARTIFACT_SCHEMAS.values():
        try:
            load_json(REPO_ROOT / "schemas/artifacts" / schema_name)
            add(f"schema_{schema_name}", True)
        except Exception as exc:
            add(f"schema_{schema_name}", False, error=str(exc))

    if check_comfy:
        try:
            object_info = fetch_comfy_object_info(comfy_host)
            missing = sorted(REQUIRED_COMFY_NODE_CLASSES - set(object_info))
            add(
                "comfyui_object_info",
                not missing,
                host=comfy_host,
                node_class_count=len(object_info),
                missing_required=missing,
            )
        except Exception as exc:
            add("comfyui_object_info", False, host=comfy_host, error=str(exc))

    return {"ok": all(item["ok"] for item in checks), "checks": checks}


def validate_artifact(path: Path, schema_path: Path) -> list[str]:
    data = load_json(path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    return [f"{'/'.join(map(str, error.path))}: {error.message}" for error in validator.iter_errors(data)]


def validate_artifacts(paths: ArtifactBus) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for artifact_name, schema_name in ARTIFACT_SCHEMAS.items():
        artifact_path = paths.artifacts / artifact_name
        schema_path = REPO_ROOT / "schemas/artifacts" / schema_name
        if not artifact_path.exists():
            results.append({"artifact": artifact_name, "ok": False, "errors": [f"missing artifact: {artifact_path}"]})
            continue
        errors = validate_artifact(artifact_path, schema_path)
        results.append({"artifact": artifact_name, "ok": not errors, "errors": errors})
    return {"ok": all(item["ok"] for item in results), "artifacts": results}


def gate_render_readiness(paths: ArtifactBus) -> dict[str, Any]:
    policy = GatePolicy.asymmetric_source_commentary()
    result = policy.validate(
        "render-readiness",
        {
            "capture_plan": load_json(paths.artifacts / "source_capture_plan.json"),
            "segment_approval": load_json(paths.artifacts / "source_segment_approval_manifest.json"),
            "visual_rhythm": load_json(paths.artifacts / "visual_rhythm_plan.json"),
        },
    )
    payload = result.payload()
    write_json(policy.receipt_path("render-readiness", paths.qc), payload)
    return payload


def fixture_artifacts(episode_id: str, topic: str, *, approved: bool) -> dict[str, dict[str, Any]]:
    return {
        "asymmetric_greenlight.json": {
            "topic": topic,
            "primary_function": "education",
            "delivery_mechanism": "source-led short commentary",
            "viewer_problem": "AI browser agents inherit hidden trust boundaries from the surrounding platform.",
            "viewer_outcome": "Viewers can identify where agent permissions become platform risk.",
            "positioning": {"first": 4, "better": 4, "different": 4, "more": 3},
            "audience_equity_score": 4,
            "sauce_integrity_score": 4,
            "consistency_score": 5,
            "greenlight": True,
            "notes": "Fixture topic for deterministic pipeline validation.",
        },
        "source_query_plan.json": {
            "topic": topic,
            "queries": [
                {
                    "intent": "Find vendor documentation for browser agent permissions.",
                    "query": "AI browser agent permissions security documentation",
                    "platform": "web",
                    "preferred_sources": ["vendor documentation", "security disclosure"],
                },
                {
                    "intent": "Find original researcher demonstration footage.",
                    "query": "browser agent trust boundary researcher demo",
                    "platform": "youtube",
                    "preferred_sources": ["researcher demo", "conference talk"],
                },
            ],
        },
        "source_candidate_manifest.json": {
            "topic": topic,
            "sources": [
                {
                    "id": "src-vendor-doc",
                    "url": "https://example.com/vendor/browser-agent-permissions",
                    "kind": "documentation",
                    "relevance": "Defines the permission model and platform boundary.",
                    "capture_potential": "screenshot",
                    "credibility_notes": "Fixture primary vendor source.",
                },
                {
                    "id": "src-researcher-demo",
                    "url": "https://example.com/researcher/browser-agent-demo",
                    "kind": "technical_disclosure",
                    "relevance": "Shows the mechanism and reproduction path.",
                    "capture_potential": "screenshot_and_clip",
                    "credibility_notes": "Fixture researcher source.",
                },
            ],
        },
        "youtube_source_manifest.json": {
            "episode": episode_id,
            "videos": [
                {
                    "id": "yt-researcher-demo",
                    "url": "https://www.youtube.com/watch?v=fixture",
                    "title": "Browser Agent Trust Boundary Demo",
                    "channel": "Fixture Research Lab",
                    "upload_date": "2026-05-01",
                    "source_role": "researcher_demo",
                    "transcript_available": True,
                    "candidate_ranges": [
                        {
                            "start": "00:00:04",
                            "end": "00:00:11",
                            "purpose": "First proof of the trust-boundary failure mode.",
                            "claim_ids": ["claim-1"],
                        }
                    ],
                    "rights_risk": "low",
                    "notes": "Fixture metadata only.",
                }
            ],
        },
        "source_capture_plan.json": {
            "episode": episode_id,
            "operator_approved_for_acquisition": approved,
            "captures": [
                {
                    "id": "cap-proof-demo",
                    "source_id": "src-researcher-demo",
                    "claim_ids": ["claim-1"],
                    "capture_type": "youtube_clip",
                    "url": "https://www.youtube.com/watch?v=fixture",
                    "timestamp_range": {"start": "00:00:04", "end": "00:00:11"},
                    "purpose": "Show the first receipt before the 10-second mark.",
                    "rights_risk": "low",
                    "approved": approved,
                },
                {
                    "id": "cap-vendor-doc",
                    "source_id": "src-vendor-doc",
                    "claim_ids": ["claim-2"],
                    "capture_type": "web_screenshot",
                    "url": "https://example.com/vendor/browser-agent-permissions",
                    "purpose": "Show the official permission boundary language.",
                    "rights_risk": "low",
                    "approved": approved,
                },
            ],
        },
        "asymmetric_claim_map.json": {
            "topic": topic,
            "claims": [
                {
                    "id": "claim-1",
                    "claim": "The agent can act across a boundary the viewer may not recognize.",
                    "status": "researcher_reported",
                    "source_ids": ["src-researcher-demo"],
                    "mechanism_relevance": "Primary mechanism proof.",
                    "overstatement_risk": "Do not imply all browser agents share this exact behavior.",
                },
                {
                    "id": "claim-2",
                    "claim": "The platform permission model is part of the risk surface.",
                    "status": "vendor_stated",
                    "source_ids": ["src-vendor-doc"],
                    "mechanism_relevance": "Explains why the boundary exists.",
                    "overstatement_risk": "Keep the explanation tied to documented behavior.",
                },
            ],
        },
        "evidence_candidate_manifest.json": {
            "episode": episode_id,
            "evidence": [
                {
                    "id": "ev-proof-demo",
                    "claim_id": "claim-1",
                    "asset_type": "youtube_clip",
                    "source_id": "src-researcher-demo",
                    "purpose": "First proof event.",
                    "timestamp_range": {"start": "00:00:04", "end": "00:00:11"},
                    "priority": "high",
                },
                {
                    "id": "ev-vendor-doc",
                    "claim_id": "claim-2",
                    "asset_type": "web_screenshot",
                    "source_id": "src-vendor-doc",
                    "purpose": "Source label and permission context.",
                    "priority": "high",
                },
            ],
        },
        "rights_risk_manifest.json": {
            "episode": episode_id,
            "items": [
                {
                    "evidence_id": "ev-proof-demo",
                    "rights_status": "fixture fair-use review required before real acquisition",
                    "risk_level": "low",
                    "notes": "Fixture clip is not downloaded.",
                },
                {
                    "evidence_id": "ev-vendor-doc",
                    "rights_status": "fixture screenshot review required before real acquisition",
                    "risk_level": "low",
                    "notes": "Fixture screenshot is not captured.",
                },
            ],
        },
        "visual_rhythm_plan.json": {
            "episode": episode_id,
            "operator_approved_for_render": approved,
            "segments": [
                {
                    "id": "seg-proof",
                    "purpose": "First proof hit.",
                    "visual_mode": "source_clip",
                    "starts_at_seconds": 6,
                    "event_type": "proof",
                    "approved": approved,
                    "source_label_present": True,
                    "source_label": "Fixture Research Lab, 2026",
                    "evidence_ids": ["ev-proof-demo"],
                    "transition_note": "Cut directly from consequence into receipt.",
                },
                {
                    "id": "seg-source",
                    "purpose": "Platform permission context.",
                    "visual_mode": "source_clip",
                    "starts_at_seconds": 12,
                    "event_type": "source",
                    "approved": approved,
                    "source_label_present": True,
                    "source_label": "Vendor permissions doc, 2026",
                    "evidence_ids": ["ev-vendor-doc"],
                    "transition_note": "Source wall with claim-status overlay.",
                },
            ],
        },
        "source_segment_approval_manifest.json": {
            "episode": episode_id,
            "segments": [
                {
                    "segment_id": "seg-proof",
                    "approved": approved,
                    "reason": "Mechanism proof supported by researcher fixture.",
                    "required_evidence_ids": ["ev-proof-demo"],
                },
                {
                    "segment_id": "seg-source",
                    "approved": approved,
                    "reason": "Permission context supported by vendor fixture.",
                    "required_evidence_ids": ["ev-vendor-doc"],
                },
            ],
        },
    }


def write_fixture_artifacts(paths: ArtifactBus, episode_id: str, topic: str, *, approved: bool) -> dict[str, Any]:
    artifacts = fixture_artifacts(episode_id, topic, approved=approved)
    for filename, data in artifacts.items():
        write_json(paths.artifacts / filename, data)
    return {"ok": True, "artifacts": sorted(artifacts)}


def run_cmd(cmd: list[str], *, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "$ " + " ".join(cmd) + "\n\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
            encoding="utf-8",
        )
    if proc.returncode != 0:
        raise PipelineError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc


def ffprobe_duration(path: Path) -> float:
    proc = run_cmd([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    try:
        return float(proc.stdout.strip())
    except ValueError as exc:
        raise PipelineError(f"Could not parse duration for {path}: {proc.stdout!r}") from exc


def render_smoke(paths: ArtifactBus, episode_id: str, *, overwrite: bool) -> dict[str, Any]:
    output = paths.renders / f"{episode_id}_fixture_smoke.mp4"
    if output.exists() and not overwrite:
        raise PipelineError(f"render already exists; pass --overwrite: {output}")
    overwrite_flag = "-y" if overwrite else "-n"
    run_cmd(
        [
            "ffmpeg",
            overwrite_flag,
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x720:rate=30:duration=16",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=16",
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(output),
        ],
        log_path=paths.logs / "ffmpeg_render_smoke.log",
    )
    duration = ffprobe_duration(output)
    return {"ok": True, "render": str(output), "duration_seconds": duration}


def run_silencedetect(paths: ArtifactBus, render_path: Path) -> dict[str, Any]:
    log_path = paths.logs / "ffmpeg_silencedetect.log"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(render_path),
            "-af",
            "silencedetect=noise=-45dB:d=1",
            "-f",
            "null",
            "-",
        ],
        text=True,
        capture_output=True,
    )
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise PipelineError(f"FFmpeg silencedetect failed: {proc.stderr.strip()}")
    duration = ffprobe_duration(render_path)
    return {"ok": True, "log": str(log_path), "duration_seconds": duration}


def qc(
    paths: ArtifactBus,
    episode_id: str,
    *,
    creative_pass: bool,
    operator_approved: bool,
    render_path: Path | None = None,
) -> dict[str, Any]:
    from lib.asymmetric_gate_policy import parse_silencedetect_log

    render_path = render_path or paths.renders / f"{episode_id}_fixture_smoke.mp4"
    if not render_path.exists():
        raise PipelineError(f"missing smoke render: {render_path}")
    silence = run_silencedetect(paths, render_path)
    log_text = Path(silence["log"]).read_text(encoding="utf-8")
    parsed = parse_silencedetect_log(log_text, duration_seconds=float(silence["duration_seconds"]))
    max_silence = max((item["duration"] for item in parsed["silences"]), default=0.0)
    report = {
        "episode": episode_id,
        "creative_pass": creative_pass,
        "operator_approved_for_creative_pass": operator_approved,
        "audio": {
            "duration_seconds": silence["duration_seconds"],
            "max_silence_seconds": max_silence,
            "tail_silence_seconds": parsed["tail_silence_seconds"],
        },
    }
    write_json(paths.artifacts / "qc_report.json", report)
    policy = GatePolicy.asymmetric_source_commentary()
    gate = policy.validate("qc", {"qc_report": report}, ffmpeg_log_text=log_text)
    payload = gate.payload()
    write_json(policy.receipt_path("qc", paths.qc), payload)
    return {"ok": payload["ok"], "qc_report": str(paths.artifacts / "qc_report.json"), "gate": payload}


def fixture_render_phase(context: RunContext) -> RenderPhaseResult:
    render = render_smoke(context.paths, context.episode_id, overwrite=context.overwrite)
    return RenderPhaseResult(
        render=render,
        stages=(StageOutcome("render_smoke", True, render),),
    )


def real_smoke_render_phase(context: RunContext) -> RenderPhaseResult:
    from scripts.asymmetric_ffmpeg_renderer import render_episode
    from scripts.asymmetric_real_smoke_acquisition import write_source_cards

    acquisition = write_source_cards(run_dir=context.paths.root, captured_at="2026-05-13T00:00:00Z")

    render = render_episode(
        run_dir=context.paths.root,
        episode_id=context.episode_id,
        overwrite=context.overwrite,
    )
    return RenderPhaseResult(
        render=render,
        stages=(
            StageOutcome("real_smoke_acquisition", True, acquisition),
            StageOutcome("source_proof_render", render["ok"], render),
        ),
    )


def build_run_mode(mode: str) -> PipelineRunMode:
    if mode == "fixture":
        return PipelineRunMode(
            name="fixture",
            artifact_stage_name="fixture_artifacts",
            render_phase=fixture_render_phase,
        )
    if mode == "real-smoke":
        return PipelineRunMode(
            name="real-smoke",
            artifact_stage_name="source_commentary_artifacts",
            render_phase=real_smoke_render_phase,
        )
    raise PipelineError(f"unknown run mode: {mode}")


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    paths = run_paths(args.run_base_dir, args.episode_id)
    mode = build_run_mode(args.mode)
    runner = PipelineRun(
        episode_id=args.episode_id,
        topic=args.topic,
        paths=paths,
        mode=mode,
        approved=bool(args.auto_approve_fixture),
        overwrite=args.overwrite,
        preflight=lambda: preflight(comfy_host=resolve_comfy_host(args.comfy_host), check_comfy=args.check_comfy),
        write_source_artifacts=write_fixture_artifacts,
        validate_artifacts=validate_artifacts,
        gate_render_readiness=gate_render_readiness,
        qc=qc,
    )
    return runner.run()


def run_fixture(args: argparse.Namespace) -> dict[str, Any]:
    args.mode = "fixture"
    return run_pipeline(args)


def run_real_smoke(args: argparse.Namespace) -> dict[str, Any]:
    args.mode = "real-smoke"
    return run_pipeline(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Asymmetric source-commentary pipeline")
    parser.add_argument("--comfy-host", default=None)
    parser.add_argument("--run-base-dir", type=Path, default=DEFAULT_PROJECTS_DIR)
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Validate local dependencies and ComfyUI readiness")
    pre.add_argument("--skip-comfy", action="store_true")

    validate = sub.add_parser("validate", help="Validate artifacts and render readiness gate")
    validate.add_argument("--episode-id", required=True)

    render = sub.add_parser("render-smoke", help="Create deterministic FFmpeg smoke render")
    render.add_argument("--episode-id", required=True)
    render.add_argument("--overwrite", action="store_true")

    qc_parser = sub.add_parser("qc", help="Run FFmpeg silence QC and QC gate")
    qc_parser.add_argument("--episode-id", required=True)
    qc_parser.add_argument("--creative-pass", action="store_true")
    qc_parser.add_argument("--operator-approved", action="store_true")

    run = sub.add_parser("run", help="Run the pipeline end to end")
    run.add_argument("--mode", choices=["fixture", "real-smoke"], default="fixture")
    run.add_argument("--episode-id", required=True)
    run.add_argument("--topic", required=True)
    run.add_argument("--auto-approve-fixture", action="store_true")
    run.add_argument("--check-comfy", action="store_true")
    run.add_argument("--overwrite", action="store_true")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "preflight":
            result = preflight(comfy_host=resolve_comfy_host(args.comfy_host), check_comfy=not args.skip_comfy)
            print_json(result)
            return 0 if result["ok"] else 2
        if args.command == "validate":
            paths = run_paths(args.run_base_dir, args.episode_id)
            validation = validate_artifacts(paths)
            gate = gate_render_readiness(paths) if validation["ok"] else {"ok": False, "reasons": ["artifact validation failed"]}
            result = {"ok": validation["ok"] and gate["ok"], "validation": validation, "render_readiness_gate": gate}
            print_json(result)
            return 0 if result["ok"] else 2
        if args.command == "render-smoke":
            paths = run_paths(args.run_base_dir, args.episode_id)
            ensure_dirs(paths)
            result = render_smoke(paths, args.episode_id, overwrite=args.overwrite)
            print_json(result)
            return 0
        if args.command == "qc":
            paths = run_paths(args.run_base_dir, args.episode_id)
            result = qc(
                paths,
                args.episode_id,
                creative_pass=args.creative_pass,
                operator_approved=args.operator_approved,
            )
            print_json(result)
            return 0 if result["ok"] else 2
        result = run_pipeline(args)
        print_json(result)
        return 0 if result["status"] == "success" else 2
    except PipelineError as exc:
        print_json({"status": "error", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
