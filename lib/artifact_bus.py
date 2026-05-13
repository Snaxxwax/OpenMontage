"""Artifact Bus paths and JSON helpers.

The Artifact Bus is the repo-wide project storage interface:
``shared_studio/projects/<project_slug>/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTS_DIR = REPO_ROOT / "shared_studio" / "projects"


class ArtifactBusError(RuntimeError):
    """Expected Artifact Bus failure."""


@dataclass(frozen=True)
class ArtifactBus:
    """Canonical paths for one production project."""

    root: Path

    @classmethod
    def for_project(cls, project_slug: str, *, projects_dir: Path | None = None) -> "ArtifactBus":
        base = projects_dir or DEFAULT_PROJECTS_DIR
        return cls(root=base / project_slug)

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def receipts(self) -> Path:
        return self.root / "receipts"

    @property
    def clips(self) -> Path:
        return self.root / "clips"

    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def audio(self) -> Path:
        return self.assets / "audio"

    @property
    def renders(self) -> Path:
        return self.root / "renders"

    @property
    def qc(self) -> Path:
        return self.root / "qc"

    @property
    def logs(self) -> Path:
        """Compatibility alias for operational logs; canonical folder is qc/."""

        return self.qc

    @property
    def manifest(self) -> Path:
        return self.root / "run_manifest.json"

    def ensure_dirs(self) -> None:
        for path in [
            self.root,
            self.artifacts,
            self.receipts,
            self.clips,
            self.assets,
            self.audio,
            self.renders,
            self.qc,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def artifact_path(self, filename: str) -> Path:
        return self.artifacts / filename

    def load_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ArtifactBusError(f"missing JSON file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ArtifactBusError(f"invalid JSON in {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ArtifactBusError(f"JSON file must contain an object: {path}")
        return data

    def load_artifact(self, filename: str) -> dict[str, Any]:
        return self.load_json(self.artifact_path(filename))

    def write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def write_artifact(self, filename: str, data: dict[str, Any]) -> None:
        self.write_json(self.artifact_path(filename), data)
