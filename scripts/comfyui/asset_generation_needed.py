#!/usr/bin/env python3
"""Decide whether ComfyUI asset generation is needed.

This script is deliberately read-only. It does not launch ComfyUI, download
models, or modify files. Pipeline agents should run it before touching the
Dockerized ComfyUI lifecycle.

Examples:
    python3 scripts/comfyui/asset_generation_needed.py --profile mvp
    python3 scripts/comfyui/asset_generation_needed.py --profile props_backgrounds
    python3 scripts/comfyui/asset_generation_needed.py --intent props --intent thumbnail_base
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REQUIREMENTS = ROOT / "channels" / "modern-archivist" / "assets" / "comfyui_workflows" / "asset_requirements.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def existing_paths(patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        full_pattern = str(resolve(pattern))
        for match in sorted(glob.glob(full_pattern)):
            p = Path(match)
            if p.exists() and p.is_file() and p.stat().st_size > 0:
                try:
                    found.append(str(p.relative_to(ROOT)))
                except ValueError:
                    found.append(str(p))
    return sorted(set(found))


def evaluate_requirement(req: dict[str, Any]) -> dict[str, Any]:
    paths = [str(p) for p in req.get("paths", [])]
    globs = [str(p) for p in req.get("glob", [])]
    found: list[str] = []
    for path in paths:
        p = resolve(path)
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            try:
                found.append(str(p.relative_to(ROOT)))
            except ValueError:
                found.append(str(p))
    found.extend(existing_paths(globs))
    found = sorted(set(found))
    min_count = int(req.get("min_count", 1))
    return {
        "id": req.get("id"),
        "satisfied": len(found) >= min_count,
        "min_count": min_count,
        "found_count": len(found),
        "found": found,
        "checked_paths": paths,
        "checked_globs": globs,
    }


def profile_requirements(config: dict[str, Any], profile_name: str, seen: set[str] | None = None) -> list[dict[str, Any]]:
    seen = seen or set()
    if profile_name in seen:
        raise ValueError(f"cycle in profile includes: {profile_name}")
    seen.add(profile_name)
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        raise KeyError(f"unknown profile: {profile_name}")
    profile = profiles[profile_name] or {}
    reqs: list[dict[str, Any]] = []
    for included in profile.get("includes", []) or []:
        reqs.extend(profile_requirements(config, str(included), seen))
    reqs.extend(profile.get("requirements", []) or [])
    return reqs


def profile_for_intent(config: dict[str, Any], intent: str) -> str:
    intents = config.get("generation_intents", {})
    if intent not in intents:
        raise KeyError(f"unknown generation intent: {intent}")
    return str(intents[intent]["profile"])


def evaluate(config: dict[str, Any], profiles: list[str], intents: list[str]) -> dict[str, Any]:
    selected_profiles = list(profiles)
    for intent in intents:
        selected_profiles.append(profile_for_intent(config, intent))
    if not selected_profiles:
        selected_profiles = ["mvp"]

    results = []
    for profile in selected_profiles:
        req_results = [evaluate_requirement(req) for req in profile_requirements(config, profile)]
        missing = [r for r in req_results if not r["satisfied"]]
        profile_cfg = config.get("profiles", {}).get(profile, {})
        results.append({
            "profile": profile,
            "description": profile_cfg.get("description"),
            "satisfied": not missing,
            "requirements": req_results,
            "missing": missing,
        })

    missing_any = [r for profile in results for r in profile["missing"]]
    return {
        "needs_generation": bool(missing_any),
        "selected_profiles": selected_profiles,
        "requested_intents": intents,
        "profiles": results,
        "missing_requirement_ids": sorted({str(r.get("id")) for r in missing_any}),
        "policy": "saved-assets-first: launch/load ComfyUI only when needs_generation is true",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--profile", action="append", default=[], help="Asset profile to require; defaults to mvp")
    parser.add_argument("--intent", action="append", default=[], help="Named generation intent from asset_requirements.yaml")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    config = load_yaml(args.requirements)
    result = evaluate(config, args.profile, args.intent)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if result["needs_generation"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
