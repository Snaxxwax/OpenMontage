#!/usr/bin/env python3
"""
rig_spec_validator.py — Validate a puppet_action_timeline.json against rig_spec.json.

Usage:
    python tools/character/rig_spec_validator.py <timeline.json> [options]

Options:
    --rig-spec PATH     Path to rig_spec.json (auto-discovered if omitted)
    --schema PATH       Path to puppet_action_timeline.schema.json (auto-discovered)
    --json              Output machine-readable JSON report instead of human text
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Repo root discovery
# ---------------------------------------------------------------------------

def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* until we find a directory containing CLAUDE.md or .git."""
    current = start.resolve()
    for _ in range(20):
        if (current / "CLAUDE.md").exists() or (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_RIG_SPEC_REL = "channels/modern-archivist/assets/character/rig/rig_spec.json"
_SCHEMA_REL = "channels/modern-archivist/schemas/puppet_action_timeline.schema.json"

_VALIDATED_TRACK_TYPES = {"action", "expression", "eyes", "mouth"}


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def validate_timeline(
    timeline_path: Path,
    rig_spec_path: Path,
    schema_path: Path | None,
) -> dict[str, Any]:
    """
    Run all checks and return a structured report dict:

    {
        "timeline_path": str,
        "rig_spec_path": str,
        "checks": [
            {"name": str, "status": "pass"|"fail"|"warn"|"skip", "detail": str | None}
        ],
        "overall": "pass" | "fail"
    }
    """
    report: dict[str, Any] = {
        "timeline_path": str(timeline_path),
        "rig_spec_path": str(rig_spec_path),
        "checks": [],
        "overall": "pass",
    }
    checks = report["checks"]

    def _add(name: str, status: str, detail: str | None = None) -> None:
        checks.append({"name": name, "status": status, "detail": detail})
        if status == "fail":
            report["overall"] = "fail"

    # -----------------------------------------------------------------------
    # Check 1 — Valid JSON (timeline)
    # -----------------------------------------------------------------------
    try:
        with open(timeline_path, "r", encoding="utf-8") as fh:
            timeline = json.load(fh)
        _add("Valid JSON", "pass")
    except (json.JSONDecodeError, OSError) as exc:
        _add("Valid JSON", "fail", str(exc))
        # Cannot continue without parseable timeline
        return report

    tracks: list[dict] = timeline.get("tracks", [])
    track_count = len(tracks)

    # -----------------------------------------------------------------------
    # Check 2 — JSON Schema validation (optional; skip if jsonschema missing)
    # -----------------------------------------------------------------------
    if schema_path is not None and schema_path.exists():
        try:
            import jsonschema  # type: ignore

            with open(schema_path, "r", encoding="utf-8") as fh:
                schema = json.load(fh)
            try:
                jsonschema.validate(timeline, schema)
                _add(
                    "Schema validation",
                    "pass",
                    f"{track_count} track{'s' if track_count != 1 else ''}",
                )
            except jsonschema.ValidationError as exc:
                _add("Schema validation", "fail", exc.message)
        except ImportError:
            _add(
                "Schema validation",
                "skip",
                "jsonschema not installed — skipping (pip install jsonschema to enable)",
            )
    else:
        _add(
            "Schema validation",
            "skip",
            "Schema file not found — skipping",
        )

    # -----------------------------------------------------------------------
    # Load rig_spec for remaining checks
    # -----------------------------------------------------------------------
    try:
        with open(rig_spec_path, "r", encoding="utf-8") as fh:
            rig_spec = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        _add("Load rig_spec", "fail", str(exc))
        return report

    rig_states: dict[str, list[str]] = rig_spec.get("states", {})

    # -----------------------------------------------------------------------
    # Check 3 — All track values exist in rig_spec states
    # -----------------------------------------------------------------------
    bad_tracks: list[str] = []
    for i, track in enumerate(tracks):
        ttype = track.get("type")
        tvalue = track.get("value")
        if ttype in _VALIDATED_TRACK_TYPES:
            valid_values = rig_states.get(ttype, [])
            if tvalue not in valid_values:
                bad_tracks.append(
                    f"track[{i}] type={ttype!r} value={tvalue!r} "
                    f"(valid: {valid_values})"
                )

    if bad_tracks:
        _add(
            "Track values in rig_spec states",
            "fail",
            "; ".join(bad_tracks),
        )
    else:
        _add("Track values in rig_spec states", "pass")

    # -----------------------------------------------------------------------
    # Check 4 — No zero-duration tracks (from >= to)
    # -----------------------------------------------------------------------
    zero_dur: list[str] = []
    for i, track in enumerate(tracks):
        frm = track.get("from")
        to = track.get("to")
        if frm is not None and to is not None and frm >= to:
            zero_dur.append(
                f"track[{i}] type={track.get('type')!r} from={frm} to={to}"
            )

    if zero_dur:
        _add(
            "No zero-duration tracks",
            "fail",
            "; ".join(zero_dur),
        )
    else:
        _add("No zero-duration tracks", "pass")

    # -----------------------------------------------------------------------
    # Check 5 — Overlapping tracks of same type (warning only)
    # -----------------------------------------------------------------------
    # Group by type, sort by from, detect overlaps
    by_type: dict[str, list[tuple[float, float, int]]] = {}
    for i, track in enumerate(tracks):
        ttype = track.get("type")
        frm = track.get("from")
        to = track.get("to")
        if ttype and frm is not None and to is not None:
            by_type.setdefault(ttype, []).append((frm, to, i))

    overlap_count = 0
    overlap_details: list[str] = []
    for ttype, segments in by_type.items():
        segments_sorted = sorted(segments, key=lambda x: x[0])
        for idx in range(len(segments_sorted) - 1):
            a_from, a_to, a_i = segments_sorted[idx]
            b_from, b_to, b_i = segments_sorted[idx + 1]
            if b_from < a_to:  # overlap
                overlap_count += 1
                overlap_details.append(
                    f"type={ttype!r} track[{a_i}]({a_from}-{a_to}) "
                    f"overlaps track[{b_i}]({b_from}-{b_to})"
                )

    if overlap_count > 0:
        _add(
            "No overlapping tracks (same type)",
            "warn",
            f"{overlap_count} overlap{'s' if overlap_count != 1 else ''}: "
            + "; ".join(overlap_details),
        )
    else:
        _add("No overlapping tracks (same type)", "pass")

    return report


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

_STATUS_ICON = {
    "pass": "✓",   # ✓
    "fail": "✗",   # ✗
    "warn": "⚠ ",  # ⚠
    "skip": "○",   # ○
}


def _print_report(report: dict[str, Any]) -> None:
    timeline_name = Path(report["timeline_path"]).name
    rig_spec_path = report["rig_spec_path"]

    print("Modern Archivist Rig Spec Validator")
    print("=====================================")
    print(f"Timeline: {timeline_name}")
    print(f"Rig spec: {rig_spec_path}")
    print()

    for check in report["checks"]:
        icon = _STATUS_ICON.get(check["status"], "?")
        detail = check["detail"]
        if check["status"] == "warn":
            line = f"⚠  {check['name']}"
            if detail:
                # Summarise: show count only in the main line
                # e.g. "⚠  2 overlapping track segments (warning only)"
                count_prefix = detail.split(":")[0].strip()
                line = f"⚠  {count_prefix} (warning only)"
            print(line)
            if detail and ":" in detail:
                sub_detail = detail.split(":", 1)[1].strip()
                for seg in sub_detail.split("; "):
                    print(f"     {seg}")
        elif check["status"] in ("fail",):
            print(f"{icon} {check['name']}")
            if detail:
                for seg in detail.split("; "):
                    print(f"     {seg}")
        elif check["status"] == "skip":
            print(f"{icon} {check['name']} — skipped")
            if detail:
                print(f"     {detail}")
        else:
            line = f"{icon} {check['name']}"
            if detail:
                line += f" ({detail})"
            print(line)

    print()
    if report["overall"] == "pass":
        print("All required checks passed.")
    else:
        print("One or more required checks FAILED.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a puppet_action_timeline.json against the rig_spec.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "timeline",
        metavar="TIMELINE",
        help="Path to the puppet_action_timeline.json file to validate",
    )
    parser.add_argument(
        "--rig-spec",
        metavar="PATH",
        default=None,
        help="Path to rig_spec.json (auto-discovered from repo root if omitted)",
    )
    parser.add_argument(
        "--schema",
        metavar="PATH",
        default=None,
        help="Path to puppet_action_timeline.schema.json (auto-discovered if omitted)",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output machine-readable JSON report",
    )

    args = parser.parse_args(argv)

    timeline_path = Path(args.timeline)
    if not timeline_path.exists():
        print(f"Error: timeline file not found: {timeline_path}", file=sys.stderr)
        return 1

    # Auto-discover repo root
    repo_root = _find_repo_root(Path(__file__).parent)

    # Resolve rig_spec
    if args.rig_spec:
        rig_spec_path = Path(args.rig_spec)
    elif repo_root:
        rig_spec_path = repo_root / _RIG_SPEC_REL
    else:
        print(
            "Error: could not auto-discover repo root; "
            "please supply --rig-spec explicitly.",
            file=sys.stderr,
        )
        return 1

    if not rig_spec_path.exists():
        print(f"Error: rig_spec not found: {rig_spec_path}", file=sys.stderr)
        return 1

    # Resolve schema (optional)
    if args.schema:
        schema_path: Path | None = Path(args.schema)
    elif repo_root:
        schema_path = repo_root / _SCHEMA_REL
    else:
        schema_path = None

    report = validate_timeline(timeline_path, rig_spec_path, schema_path)

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)

    return 0 if report["overall"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
