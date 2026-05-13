"""Deep pipeline contract interface.

Normalizes legacy manifests (``name``/``skill``/``produces``) and newer
stage-definition manifests (``id``/``director``/``outputs``) behind one seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DEFS_DIR = REPO_ROOT / "pipeline_defs"


class PipelineContractError(RuntimeError):
    """Expected pipeline contract failure."""


@dataclass(frozen=True)
class StageContract:
    name: str
    director: Path | None
    produced_artifacts: tuple[str, ...]
    output_schemas: tuple[Path, ...]
    required_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class PipelineContract:
    pipeline_id: str
    path: Path
    manifest: dict[str, Any]
    stages: tuple[StageContract, ...]

    @classmethod
    def load(cls, pipeline_id: str, *, defs_dir: Path | None = None) -> "PipelineContract":
        defs = defs_dir or PIPELINE_DEFS_DIR
        path = defs / f"{pipeline_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Pipeline manifest not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise PipelineContractError(f"Pipeline manifest must be an object: {path}")
        stages = tuple(_stage_contract(stage) for stage in data.get("stages") or [])
        return cls(
            pipeline_id=str(data.get("id") or data.get("name") or pipeline_id),
            path=path,
            manifest=data,
            stages=stages,
        )

    @property
    def stage_names(self) -> list[str]:
        return [stage.name for stage in self.stages]

    @property
    def artifact_schemas(self) -> dict[str, Path]:
        schemas: dict[str, Path] = {}
        for stage in self.stages:
            for schema_path in stage.output_schemas:
                schemas[_artifact_filename_for_schema(schema_path)] = schema_path
        return schemas

    def stage(self, name: str) -> StageContract:
        for stage in self.stages:
            if stage.name == name:
                return stage
        raise PipelineContractError(f"unknown stage {name!r} in pipeline {self.pipeline_id!r}")

    def missing_directors(self) -> list[Path]:
        return [
            stage.director
            for stage in self.stages
            if stage.director is not None and not stage.director.exists()
        ]

    def missing_schemas(self) -> list[Path]:
        return [
            schema
            for schema in self.artifact_schemas.values()
            if not schema.exists()
        ]

    def validate_references(self) -> list[str]:
        issues = []
        for director in self.missing_directors():
            issues.append(f"missing director skill: {director}")
        for schema in self.missing_schemas():
            issues.append(f"missing artifact schema: {schema}")
        return issues


def _stage_contract(stage: Any) -> StageContract:
    if not isinstance(stage, dict):
        raise PipelineContractError(f"stage must be an object: {stage!r}")
    name = stage.get("name") or stage.get("id")
    if not name:
        raise PipelineContractError(f"stage is missing name/id: {stage!r}")

    raw_director = stage.get("director") or stage.get("skill")
    director = _director_path(str(raw_director)) if raw_director else None
    produced = tuple(str(item) for item in stage.get("produces") or ())
    output_schemas = tuple(_repo_path(item) for item in stage.get("outputs") or ())
    if not output_schemas and produced:
        output_schemas = tuple(REPO_ROOT / "schemas" / "artifacts" / f"{item}.schema.json" for item in produced)
    elif output_schemas and not produced:
        produced = tuple(_artifact_name_for_schema(path) for path in output_schemas)

    return StageContract(
        name=str(name),
        director=director,
        produced_artifacts=produced,
        output_schemas=output_schemas,
        required_artifacts=tuple(str(item) for item in stage.get("required_artifacts_in") or ()),
    )


def _director_path(value: str) -> Path:
    path = Path(value)
    if path.suffix:
        return _repo_path(value)
    return REPO_ROOT / "skills" / f"{value}.md"


def _repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _artifact_name_for_schema(path: Path) -> str:
    name = path.name
    return name.removesuffix(".schema.json")


def _artifact_filename_for_schema(path: Path) -> str:
    return f"{_artifact_name_for_schema(path)}.json"
