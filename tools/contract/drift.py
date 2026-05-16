# tools/contract/drift.py
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

from tools.contract.sources import REPO_ROOT


@dataclass
class DriftIssue:
    severity: str  # "BLOCKING" or "WARNING"
    check: str
    detail: str
    source: str = ""

    @property
    def is_blocking(self) -> bool:
        return self.severity == "BLOCKING"

    def format_md(self) -> str:
        lines = [f"### {self.check} [{self.severity}]"]
        if self.source:
            lines.append(f"**Source:** `{self.source}`")
        lines.append(self.detail)
        if self.is_blocking:
            lines.append("\n**Resolution:** manual review required")
        else:
            lines.append("\n**Note:** advisory only — no blocking action required")
        return "\n".join(lines)


def check_bootstrap_gap(root: Path = REPO_ROOT) -> List[DriftIssue]:
    agents_md = root / "AGENTS.md"
    if not agents_md.exists():
        return [DriftIssue(
            "BLOCKING", "MISSING SOURCE FILE",
            "AGENTS.md not found on disk.",
            source="AGENTS.md",
        )]
    if ".agent_contract/agent_boot_packet.md" not in agents_md.read_text():
        return [DriftIssue(
            "BLOCKING", "BOOTSTRAP GAP",
            "AGENTS.md has no reference to `.agent_contract/agent_boot_packet.md`.\n"
            "Agents cannot find the compiled boot packet at startup.\n\n"
            "**Proposed patch:** Add after the opening role definition in AGENTS.md:\n\n"
            "> **Before any action:** read `.agent_contract/agent_boot_packet.md`.\n"
            "> If `contract_status.yaml` shows `stale: true` or `blocking_conflicts: true`, halt.",
            source="AGENTS.md",
        )]
    return []


def _resolve_stage_path(root: Path, path: str) -> bool:
    """Try four resolution strategies for manifest stage skill/director paths.

    Manifests use several shorthand conventions:
      1. exact path (e.g. skills/pipelines/foo/bar-director.md)
      2. missing skills/ prefix (e.g. pipelines/foo/bar-director.md)
      3. missing .md extension (e.g. skills/pipelines/foo/bar-director)
      4. missing both (e.g. pipelines/foo/bar-director)
    """
    return any(c.exists() for c in (
        root / path,
        root / "skills" / path,
        root / (path + ".md"),
        root / "skills" / (path + ".md"),
    ))


def check_pipeline_stage_skills(root: Path = REPO_ROOT) -> List[DriftIssue]:
    issues = []
    for manifest in sorted(root.glob("pipeline_defs/**/*.yaml")):
        try:
            data = yaml.safe_load(manifest.read_text())
            if not isinstance(data, dict):
                continue
        except Exception:
            continue
        for stage in data.get("stages", []):
            director = stage.get("skill") or stage.get("director")
            if not director:
                continue
            if not _resolve_stage_path(root, director):
                issues.append(DriftIssue(
                    "BLOCKING", "MISSING STAGE SKILL",
                    f"Stage `{stage.get('name', '?')}` director `{director}` not found on disk.",
                    source=str(manifest.relative_to(root)),
                ))
    return issues


def check_missing_schemas(root: Path = REPO_ROOT) -> List[DriftIssue]:
    issues = []
    for manifest in sorted(root.glob("pipeline_defs/**/*.yaml")):
        try:
            data = yaml.safe_load(manifest.read_text())
            if not isinstance(data, dict):
                continue
        except Exception:
            continue
        for stage in data.get("stages", []):
            schema_ref = stage.get("output_schema")
            if schema_ref and not (root / schema_ref).exists():
                issues.append(DriftIssue(
                    "BLOCKING", "MISSING SCHEMA",
                    f"Stage `{stage.get('name', '?')}` output_schema `{schema_ref}` not found on disk.",
                    source=str(manifest.relative_to(root)),
                ))
    return issues


def check_agent_skills_refs(root: Path = REPO_ROOT) -> List[DriftIssue]:
    issues = []
    block_re = re.compile(r'agent_skills\s*=\s*\[([^\]]*)\]', re.DOTALL)
    path_re = re.compile(r'["\']([^"\']+\.md)["\']')
    for tool_file in sorted(root.glob("tools/**/*.py")):
        if tool_file.parent.name == "contract":
            continue
        content = tool_file.read_text()
        for block in block_re.finditer(content):
            for skill_path in path_re.findall(block.group(1)):
                if not (root / skill_path).exists():
                    issues.append(DriftIssue(
                        "WARNING", "BROKEN AGENT_SKILLS REF",
                        f"`agent_skills` references `{skill_path}` which does not exist on disk.",
                        source=str(tool_file.relative_to(root)),
                    ))
    return issues


def check_path_overlaps(root: Path = REPO_ROOT) -> List[DriftIssue]:
    policy = root / ".agent" / "allowed_paths.yaml"
    if not policy.exists():
        return []
    data = yaml.safe_load(policy.read_text()) or {}
    allowed = set(data.get("allowed_write_paths", []))
    forbidden = set(data.get("forbidden_write_paths", []))
    overlaps = sorted(allowed & forbidden)
    if overlaps:
        return [DriftIssue(
            "BLOCKING", "PATH POLICY OVERLAP",
            f"Paths listed as both allowed and forbidden: {overlaps}",
            source=".agent/allowed_paths.yaml",
        )]
    return []


def run_all_checks(root: Path = REPO_ROOT) -> List[DriftIssue]:
    issues: List[DriftIssue] = []
    issues.extend(check_bootstrap_gap(root))
    issues.extend(check_pipeline_stage_skills(root))
    issues.extend(check_missing_schemas(root))
    issues.extend(check_agent_skills_refs(root))
    issues.extend(check_path_overlaps(root))
    return issues
