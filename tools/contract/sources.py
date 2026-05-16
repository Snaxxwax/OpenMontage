# tools/contract/sources.py
import hashlib
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FIXED_SOURCES = [
    "AGENTS.md",
    "AGENT_GUIDE.md",
    "skills/INDEX.md",
    ".agent/repo_policy.yaml",
    ".agent/allowed_paths.yaml",
    "tools/tool_registry.py",
]

GLOB_PATTERNS = [
    "pipeline_defs/**/*.yaml",
    "skills/pipelines/**/CONTRACT.md",
    "schemas/artifacts/*.json",
    "schemas/pipelines/*.json",
]


def discover_sources(root: Path = REPO_ROOT) -> List[Path]:
    seen, result = set(), []
    for name in FIXED_SOURCES:
        p = root / name
        if p.exists() and p.resolve() not in seen:
            seen.add(p.resolve())
            result.append(p)
    for pattern in GLOB_PATTERNS:
        for p in sorted(root.glob(pattern)):
            resolved = p.resolve()
            if not p.is_file():
                continue
            try:
                p.relative_to(root)
            except ValueError:
                continue
            if resolved not in seen:
                seen.add(resolved)
                result.append(p)
    return result


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_sources(root: Path = REPO_ROOT) -> Dict[str, str]:
    """Returns {relative_path_str: sha256_hex} for all discovered sources."""
    return {
        str(p.relative_to(root)): hash_file(p)
        for p in discover_sources(root)
    }
