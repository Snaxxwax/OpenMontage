# tools/contract/checker.py
import sys
from pathlib import Path

import yaml

from tools.contract.sources import REPO_ROOT, hash_sources


def check_contract(root: Path = REPO_ROOT) -> int:
    """Returns 0=valid, 1=invalid/stale/blocking, 2=malformed/unreadable."""
    contract_dir = root / ".agent_contract"
    status_path = contract_dir / "contract_status.yaml"
    boot_path = contract_dir / "agent_boot_packet.md"
    drift_path = contract_dir / "drift_report.md"

    if not status_path.exists():
        print("FAIL: contract_status.yaml missing — run 'make contract-compile'")
        return 1
    if not boot_path.exists():
        print("FAIL: agent_boot_packet.md missing — run 'make contract-compile'")
        return 1
    if not drift_path.exists():
        print("FAIL: drift_report.md missing — run 'make contract-compile'")
        return 1

    try:
        status = yaml.safe_load(status_path.read_text())
        if not isinstance(status, dict):
            print("FAIL: contract_status.yaml is malformed (not a dict)")
            return 2
    except Exception as e:
        print(f"FAIL: contract_status.yaml unreadable: {e}")
        return 2

    if status.get("missing_sources"):
        print(f"FAIL: missing_sources={status['missing_sources']}")
        return 1

    if not status.get("bootstrap_ok", False):
        print("FAIL: bootstrap_ok=false — AGENTS.md missing reference to agent_boot_packet.md")
        return 1

    if status.get("blocking_conflicts"):
        print("FAIL: blocking_conflicts=true — see .agent_contract/drift_report.md")
        return 1

    try:
        current = hash_sources(root)
    except Exception as e:
        print(f"FAIL: could not hash sources: {e}")
        return 2

    stored = {k: v["sha256"] for k, v in status.get("sources", {}).items()}
    changed   = [k for k in current if k in stored and stored[k] != current[k]]
    new_files = [k for k in current if k not in stored]
    removed   = [k for k in stored if k not in current]
    stale_files = changed + new_files + removed

    if stale_files:
        print(f"FAIL: contract is stale — {len(stale_files)} source(s) changed since compile:")
        for f in stale_files[:10]:
            print(f"  {f}")
        return 1

    return 0


def main() -> None:
    sys.exit(check_contract())


if __name__ == "__main__":
    main()
