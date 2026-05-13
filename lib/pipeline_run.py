"""Pipeline run orchestration.

Owns the Golden Loop sequence for a concrete run while concrete adapters supply
mode-specific production actions.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from lib.artifact_bus import ArtifactBus


@dataclass
class RunManifest:
    episode_id: str
    topic: str
    mode: str
    run_dir: Path
    stages: list[dict[str, Any]] = field(default_factory=list)

    def record(self, name: str, ok: bool, **data: Any) -> None:
        self.stages.append({"name": name, "ok": ok, **data})
        self.write()

    def write(self) -> None:
        payload = {
            "episode_id": self.episode_id,
            "topic": self.topic,
            "mode": self.mode,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stages": self.stages,
        }
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "run_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


@dataclass(frozen=True)
class RunContext:
    paths: ArtifactBus
    manifest: RunManifest
    episode_id: str
    topic: str
    approved: bool
    overwrite: bool


@dataclass(frozen=True)
class StageOutcome:
    name: str
    ok: bool
    result: dict[str, Any]


@dataclass(frozen=True)
class RenderPhaseResult:
    render: dict[str, Any]
    stages: tuple[StageOutcome, ...]


@dataclass(frozen=True)
class PipelineRunMode:
    name: str
    artifact_stage_name: str
    render_phase: Callable[[RunContext], RenderPhaseResult]


@dataclass(frozen=True)
class PipelineRun:
    episode_id: str
    topic: str
    paths: ArtifactBus
    mode: PipelineRunMode
    approved: bool
    overwrite: bool
    preflight: Callable[[], dict[str, Any]]
    write_source_artifacts: Callable[[ArtifactBus, str, str, bool], dict[str, Any]]
    validate_artifacts: Callable[[ArtifactBus], dict[str, Any]]
    gate_render_readiness: Callable[[ArtifactBus], dict[str, Any]]
    qc: Callable[[ArtifactBus, str, bool, bool, Path | None], dict[str, Any]]

    def run(self) -> dict[str, Any]:
        self.paths.ensure_dirs()
        manifest = RunManifest(self.episode_id, self.topic, self.mode.name, self.paths.root)
        context = RunContext(
            paths=self.paths,
            manifest=manifest,
            episode_id=self.episode_id,
            topic=self.topic,
            approved=self.approved,
            overwrite=self.overwrite,
        )

        preflight = self.preflight()
        manifest.record("preflight", preflight["ok"], result=preflight)
        if not preflight["ok"]:
            return self._failure("error", "preflight", preflight=preflight)

        artifacts = self.write_source_artifacts(
            self.paths,
            self.episode_id,
            self.topic,
            approved=self.approved,
        )
        manifest.record(self.mode.artifact_stage_name, True, result=artifacts)

        validation = self.validate_artifacts(self.paths)
        manifest.record("artifact_validation", validation["ok"], result=validation)
        if not validation["ok"]:
            return self._failure("error", "artifact_validation", validation=validation)

        gate = self.gate_render_readiness(self.paths)
        manifest.record("render_readiness_gate", gate["ok"], result=gate)
        if not gate["ok"]:
            status = "approval_required" if not self.approved else "error"
            return self._failure(status, "render_readiness_gate", gate=gate)

        render_phase = self.mode.render_phase(context)
        for stage in render_phase.stages:
            manifest.record(stage.name, stage.ok, result=stage.result)

        qc_result = self.qc(
            self.paths,
            self.episode_id,
            creative_pass=self.approved,
            operator_approved=self.approved,
            render_path=Path(render_phase.render["render"]),
        )
        manifest.record("qc", qc_result["ok"], result=qc_result)
        if not qc_result["ok"]:
            status = "approval_required" if not self.approved else "error"
            return self._failure(status, "qc", qc=qc_result)

        return {
            "status": "success",
            "episode_id": self.episode_id,
            "run_dir": str(self.paths.root),
            "render": render_phase.render["render"],
            "manifest": str(self.paths.manifest),
        }

    def _failure(self, status: str, stage: str, **data: Any) -> dict[str, Any]:
        return {"status": status, "stage": stage, "run_dir": str(self.paths.root), **data}
