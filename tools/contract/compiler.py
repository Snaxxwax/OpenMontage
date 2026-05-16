# tools/contract/compiler.py
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import yaml

from tools.contract.drift import DriftIssue, run_all_checks
from tools.contract.sources import REPO_ROOT, hash_sources


def _load_path_lists(root: Path) -> Tuple[List[str], List[str]]:
    policy = root / ".agent" / "allowed_paths.yaml"
    if not policy.exists():
        return [], []
    data = yaml.safe_load(policy.read_text()) or {}
    return (
        data.get("allowed_write_paths", []),
        data.get("forbidden_write_paths", []),
    )


def _render_boot_packet(
    compiled_at: str,
    allowed: List[str],
    forbidden: List[str],
    blocking_count: int,
) -> str:
    allowed_lines = "\n".join(f"- `{p}`" for p in allowed) or "_(check .agent/allowed_paths.yaml)_"
    forbidden_lines = "\n".join(f"- `{p}`" for p in forbidden) or "_(check .agent/allowed_paths.yaml)_"
    conflict_note = "See `.agent_contract/drift_report.md`." if blocking_count > 0 else "No action required."
    return f"""# Agent Boot Packet
**Compiled:** {compiled_at}

## Stop Conditions
- If `contract_status.yaml` shows `stale: true` or `blocking_conflicts: true`: **halt and report to operator**.
- If `bootstrap_ok: false`: **halt and report bootstrap gap**.
- Current conflicts: {blocking_count} blocking. {conflict_note}

## Role
Orchestrator. Not renderer. Not schema improviser.

## Operational Rules
1. Read active task packet before any action.
2. Stay inside allowed paths listed in this packet.
3. Discover tools through `tool_registry` only. Do not invent tool names.
4. Use selector tools (`tts_selector`, `image_selector`, `video_selector`) when provider is unspecified.
5. Load stage-specific skills only when the task requires them.
6. Required receipts vary by pipeline — read `skills/pipelines/<pipeline>/CONTRACT.md` on entry.
7. Checkpoint state after each stage.

## Allowed Paths
{allowed_lines}

## Forbidden Paths
{forbidden_lines}

## Conflict Status
{blocking_count} blocking conflict(s). {conflict_note}
"""


def _render_drift_report(issues: List[DriftIssue], compiled_at: str) -> str:
    blocking = [i for i in issues if i.is_blocking]
    warnings = [i for i in issues if not i.is_blocking]
    lines = [
        "# Drift Report",
        f"**Generated:** {compiled_at}",
        f"\n**Summary:** {len(blocking)} blocking, {len(warnings)} warning(s)\n",
    ]
    if not issues:
        lines.append("No issues detected.")
        return "\n".join(lines)
    if blocking:
        lines.append(f"## Blocking Issues ({len(blocking)})\n")
        lines.extend(i.format_md() + "\n" for i in blocking)
    if warnings:
        lines.append(f"## Warnings ({len(warnings)})\n")
        lines.extend(i.format_md() + "\n" for i in warnings)
    return "\n".join(lines)


def compile_contract(root: Path = REPO_ROOT) -> int:
    """Write three files to root/.agent_contract/. Returns 0 always."""
    contract_dir = root / ".agent_contract"
    contract_dir.mkdir(exist_ok=True)

    compiled_at = datetime.now(timezone.utc).isoformat()
    source_hashes = hash_sources(root)

    missing = [
        s for s in [
            "AGENTS.md", "AGENT_GUIDE.md", "skills/INDEX.md",
            ".agent/repo_policy.yaml", ".agent/allowed_paths.yaml",
        ]
        if not (root / s).exists()
    ]

    issues = run_all_checks(root)
    blocking = [i for i in issues if i.is_blocking]

    agents_md = root / "AGENTS.md"
    bootstrap_ok = (
        agents_md.exists()
        and ".agent_contract/agent_boot_packet.md" in agents_md.read_text()
    )

    status = {
        "compiled_at": compiled_at,
        "sources": {k: {"sha256": v} for k, v in source_hashes.items()},
        "stale": False,
        "missing_sources": missing,
        "blocking_conflicts": bool(blocking),
        "bootstrap_ok": bootstrap_ok,
    }
    (contract_dir / "contract_status.yaml").write_text(
        yaml.dump(status, default_flow_style=False, sort_keys=True, allow_unicode=True)
    )
    (contract_dir / "drift_report.md").write_text(_render_drift_report(issues, compiled_at))

    allowed, forbidden = _load_path_lists(root)
    (contract_dir / "agent_boot_packet.md").write_text(
        _render_boot_packet(compiled_at, allowed, forbidden, len(blocking))
    )
    return 0


def main() -> None:
    print("Compiling contract...")
    compile_contract()
    print("Written to .agent_contract/")
    for name in ("agent_boot_packet.md", "contract_status.yaml", "drift_report.md"):
        print(f"  {name}")


if __name__ == "__main__":
    main()
