from __future__ import annotations

from pathlib import Path

from lib.artifact_bus import ArtifactBus
from lib.pipeline_run import PipelineRun, PipelineRunMode, RenderPhaseResult, RunContext, StageOutcome


def test_pipeline_run_records_shared_stage_sequence_once(tmp_path: Path) -> None:
    paths = ArtifactBus.for_project("episode_001", projects_dir=tmp_path)

    def render_phase(context: RunContext) -> RenderPhaseResult:
        render = {"ok": True, "render": str(context.paths.renders / "out.mp4")}
        context.paths.renders.mkdir(parents=True, exist_ok=True)
        (context.paths.renders / "out.mp4").write_text("mp4", encoding="utf-8")
        return RenderPhaseResult(render=render, stages=(StageOutcome("mode_render", True, render),))

    runner = PipelineRun(
        episode_id="episode_001",
        topic="AI browser agent trust boundary failure",
        paths=paths,
        mode=PipelineRunMode("unit", "unit_artifacts", render_phase),
        approved=True,
        overwrite=True,
        preflight=lambda: {"ok": True, "checks": []},
        write_source_artifacts=lambda *_, **__: {"ok": True, "artifacts": []},
        validate_artifacts=lambda _: {"ok": True, "artifacts": []},
        gate_render_readiness=lambda _: {"ok": True, "reasons": []},
        qc=lambda *_, **__: {"ok": True, "qc_report": "qc.json", "gate": {"ok": True, "reasons": []}},
    )

    result = runner.run()

    assert result["status"] == "success"
    manifest = paths.load_json(paths.manifest)
    assert [stage["name"] for stage in manifest["stages"]] == [
        "preflight",
        "unit_artifacts",
        "artifact_validation",
        "render_readiness_gate",
        "mode_render",
        "qc",
    ]


def test_pipeline_run_stops_at_approval_gate(tmp_path: Path) -> None:
    paths = ArtifactBus.for_project("episode_001", projects_dir=tmp_path)

    def render_phase(_: RunContext) -> RenderPhaseResult:
        raise AssertionError("render phase must not run")

    runner = PipelineRun(
        episode_id="episode_001",
        topic="AI browser agent trust boundary failure",
        paths=paths,
        mode=PipelineRunMode("unit", "unit_artifacts", render_phase),
        approved=False,
        overwrite=True,
        preflight=lambda: {"ok": True, "checks": []},
        write_source_artifacts=lambda *_, **__: {"ok": True, "artifacts": []},
        validate_artifacts=lambda _: {"ok": True, "artifacts": []},
        gate_render_readiness=lambda _: {"ok": False, "reasons": ["operator approval is required before render"]},
        qc=lambda *_, **__: {"ok": True},
    )

    result = runner.run()

    assert result["status"] == "approval_required"
    assert result["stage"] == "render_readiness_gate"
    manifest = paths.load_json(paths.manifest)
    assert [stage["name"] for stage in manifest["stages"]] == [
        "preflight",
        "unit_artifacts",
        "artifact_validation",
        "render_readiness_gate",
    ]
