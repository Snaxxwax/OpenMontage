"""Asymmetric video framework validator.

Validates scene plans (and optionally source_map + asset_manifest) for the
Asymmetric channel rules: device-driven scenes, motion cadence, sourcing,
fallback planning, and basic anti-pattern detection.

This module is:
- runnable from CLI: `python3 -m tools.analysis.asymmetric_video_validator ...`
- importable: use `validate_asymmetric_video(...)`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal


DEVICE_MANIFEST_DEFAULT = (
    "channel_assets/asymmetric/diagrams/devices/manifest.json"
)

FALLBACK_TYPES = {
    "svg_css",
    "hyperframes_native",
    "generated_image",
    "stock",
    "none",
}


@dataclass
class ValidationContext:
    stage: str
    strict: bool
    style_playbook: str
    device_manifest_path: Path
    files_checked: list[str]
    checks_run: list[str]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ValueError(f"File not found: {path}") from e
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid JSON at {path}: {e}") from e


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _norm_style(style_name_or_path: str) -> str:
    raw = (style_name_or_path or "asymmetric").strip()
    # Accept `styles/asymmetric.yaml` or `asymmetric`
    raw = raw.replace("\\", "/")
    if raw.endswith(".yaml") or raw.endswith(".yml"):
        raw = Path(raw).stem
    return raw.lower()


def _device_manifest(device_manifest_path: Path) -> dict[str, Any]:
    manifest = _load_json(device_manifest_path)
    if not isinstance(manifest.get("devices"), list):
        raise ValueError(f"Device manifest missing devices[]: {device_manifest_path}")
    return manifest


def _device_index(manifest: dict[str, Any]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    known: set[str] = set()
    index: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("devices", []):
        if not isinstance(entry, dict):
            continue
        device_id = entry.get("device_id")
        if isinstance(device_id, str) and device_id:
            known.add(device_id)
            index[device_id] = entry
    return known, index


def _load_device_required_params(spec_path: Path) -> set[str]:
    spec = _load_json(spec_path)
    required: set[str] = set()
    for p in spec.get("input_parameters", []) or []:
        if not isinstance(p, dict):
            continue
        if p.get("required") is True and isinstance(p.get("name"), str):
            required.add(p["name"])
    return required


def _scene_duration(scene: dict[str, Any]) -> float | None:
    try:
        start = float(scene.get("start_seconds"))
        end = float(scene.get("end_seconds"))
    except (TypeError, ValueError):
        return None
    return end - start


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _word_count(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\S+", text))


def _script_word_count(script: dict[str, Any]) -> int:
    sections = script.get("sections")
    if not isinstance(sections, list):
        return 0
    return sum(_word_count(str(s.get("text") or "")) for s in sections if isinstance(s, dict))


def _scene_plan_total_seconds(scene_plan: dict[str, Any]) -> float | None:
    scenes = scene_plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return None
    max_end: float = 0.0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        end = _coerce_float(scene.get("end_seconds"))
        if end is None:
            continue
        max_end = max(max_end, end)
    return max_end if max_end > 0 else None


def _extract_proposal_target_seconds(proposal_packet: dict[str, Any]) -> float | None:
    selected = proposal_packet.get("selected_concept")
    if isinstance(selected, dict):
        # Prefer the chosen concept's target duration.
        td = _coerce_float(selected.get("target_duration_seconds"))
        if td:
            return td
        # Sometimes stored as id only; look up in concept_options.
        cid = selected.get("concept_id")
        options = proposal_packet.get("concept_options") or []
        if isinstance(cid, str) and isinstance(options, list):
            for opt in options:
                if isinstance(opt, dict) and opt.get("id") == cid:
                    td2 = _coerce_float(opt.get("target_duration_seconds"))
                    if td2:
                        return td2
    # Fallback: first concept option.
    options = proposal_packet.get("concept_options") or []
    if isinstance(options, list):
        for opt in options:
            if isinstance(opt, dict):
                td = _coerce_float(opt.get("target_duration_seconds"))
                if td:
                    return td
    return None


def _extract_target_seconds(
    *,
    proposal_packet: dict[str, Any] | None,
    project_config: dict[str, Any] | None,
    script: dict[str, Any] | None,
    scene_plan: dict[str, Any] | None,
) -> tuple[float | None, list[tuple[str, float]]]:
    """Return preferred target duration plus all candidates found."""
    candidates: list[tuple[str, float]] = []

    if project_config and isinstance(project_config, dict):
        for path in (("target_duration_seconds",), ("timing", "target_duration_seconds"), ("video", "target_duration_seconds")):
            cur: Any = project_config
            ok = True
            for p in path:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    ok = False
                    break
            if ok:
                td = _coerce_float(cur)
                if td:
                    candidates.append(("project_config." + ".".join(path), td))
                    break

    if proposal_packet and isinstance(proposal_packet, dict):
        td = _extract_proposal_target_seconds(proposal_packet)
        if td:
            candidates.append(("proposal_packet.selected_concept.target_duration_seconds", td))

    if script and isinstance(script, dict):
        td = _coerce_float(script.get("total_duration_seconds"))
        if td:
            candidates.append(("script.total_duration_seconds", td))

    if scene_plan and isinstance(scene_plan, dict):
        td = _scene_plan_total_seconds(scene_plan)
        if td:
            candidates.append(("scene_plan.total_seconds", td))

    # Preference: project_config > proposal_packet > script > scene_plan
    def _prio(name: str) -> int:
        if name.startswith("project_config"):
            return 0
        if name.startswith("proposal_packet"):
            return 1
        if name.startswith("script"):
            return 2
        if name.startswith("scene_plan"):
            return 3
        return 9

    chosen = sorted(candidates, key=lambda x: _prio(x[0]))[0][1] if candidates else None
    return chosen, candidates


def _within_tolerance(value: float, target: float, tol: float) -> bool:
    if target <= 0:
        return False
    return abs(value - target) <= (target * tol)


def _validate_duration_alignment(
    *,
    scene_plan: dict[str, Any] | None,
    script: dict[str, Any] | None,
    proposal_packet: dict[str, Any] | None,
    project_config: dict[str, Any] | None,
    asset_manifest: dict[str, Any] | None,
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    """Cross-artifact duration + word-count checks for Asymmetric longform projects."""
    ctx.checks_run.append("duration_alignment")
    summary: dict[str, Any] = {}

    target_seconds, candidates = _extract_target_seconds(
        proposal_packet=proposal_packet,
        project_config=project_config,
        script=script,
        scene_plan=scene_plan,
    )
    summary["target_duration_seconds"] = target_seconds
    summary["target_duration_candidates"] = [{"source": n, "seconds": s} for (n, s) in candidates]

    if target_seconds is None:
        # No target configured; nothing to enforce.
        return summary

    tol = 0.15  # ±10–15% requested; use the upper bound for gating by default.

    if script:
        script_seconds = _coerce_float(script.get("total_duration_seconds")) or 0.0
        wc = _script_word_count(script)
        summary["script_total_duration_seconds"] = script_seconds
        summary["script_word_count"] = wc

        # Word count gate: documentary pacing 140–150 WPM (2.33–2.5 WPS).
        wpm_min, wpm_max = 140.0, 150.0
        expected_min_w = int((target_seconds / 60.0) * wpm_min)
        expected_max_w = int((target_seconds / 60.0) * wpm_max)
        summary["expected_word_count_range_wpm_140_150"] = [expected_min_w, expected_max_w]

        # Accept within ±15% of mid target.
        mid_target = (target_seconds / 60.0) * ((wpm_min + wpm_max) / 2.0)
        min_accept = int(mid_target * (1.0 - tol))
        max_accept = int(mid_target * (1.0 + tol))
        summary["accepted_word_count_range"] = [min_accept, max_accept]

        if wc < min_accept or wc > max_accept:
            msg = (
                f"Script word count {wc} is outside accepted range [{min_accept}, {max_accept}] "
                f"for target_duration_seconds={target_seconds:.0f} (doc pacing 140–150 WPM ~[{expected_min_w}, {expected_max_w}])."
            )
            if ctx.strict:
                errors.append(msg)
            else:
                warnings.append(msg)

        if script_seconds and not _within_tolerance(script_seconds, target_seconds, tol):
            msg = (
                f"script.total_duration_seconds={script_seconds:.1f}s is outside ±{int(tol*100)}% of target {target_seconds:.1f}s."
            )
            if ctx.strict:
                errors.append(msg)
            else:
                warnings.append(msg)

    if scene_plan:
        sp_seconds = _scene_plan_total_seconds(scene_plan)
        if sp_seconds is not None:
            summary["scene_plan_total_seconds"] = sp_seconds
            if not _within_tolerance(sp_seconds, target_seconds, tol):
                msg = (
                    f"scene_plan duration {sp_seconds:.1f}s is outside ±{int(tol*100)}% of target {target_seconds:.1f}s "
                    "(scene_plan must not silently compress a longform project)."
                )
                if ctx.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

    if asset_manifest and scene_plan:
        # At assets stage, narration should roughly match scene plan duration (or be intentionally silent).
        sp_seconds = _scene_plan_total_seconds(scene_plan)
        if sp_seconds is not None:
            narr_total = 0.0
            narr_assets = 0
            for a in (asset_manifest.get("assets") or []):
                if not isinstance(a, dict):
                    continue
                if str(a.get("type") or "").lower() != "narration":
                    continue
                dur = _coerce_float(a.get("duration_seconds"))
                if dur:
                    narr_total += dur
                    narr_assets += 1
            if narr_assets > 0:
                summary["narration_total_seconds"] = narr_total
                if not _within_tolerance(narr_total, sp_seconds, tol):
                    msg = (
                        f"Total narration duration {narr_total:.1f}s is outside ±{int(tol*100)}% of scene_plan {sp_seconds:.1f}s "
                        "(do not compose long scene plans against short narration)."
                    )
                    if ctx.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

    return summary


def _is_state_change_exempt(scene: dict[str, Any]) -> bool:
    # Schema-safe escape hatch: encode exemption as a texture keyword.
    kws = scene.get("texture_keywords") or []
    if isinstance(kws, list) and any(
        isinstance(k, str) and k.strip().lower() in {"state_change_exempt", "asymmetric_state_change_exempt"}
        for k in kws
    ):
        return True
    # Transitions are typically short and can be exempt.
    if str(scene.get("type") or "").strip().lower() == "transition":
        return True
    return False


def _normalize_claims(source_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    claims = source_map.get("claims")
    if isinstance(claims, list):
        out: dict[str, dict[str, Any]] = {}
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = None
            if isinstance(c.get("id"), str):
                cid = c.get("id")
            elif isinstance(c.get("claim_id"), str):
                cid = c.get("claim_id")
            if cid:
                out[cid] = c
        return out
    if isinstance(claims, dict):
        return {k: v for k, v in claims.items() if isinstance(k, str) and isinstance(v, dict)}
    return {}


def _detect_stat_scene(scene: dict[str, Any]) -> bool:
    # Scene schema does not have a dedicated `stat_card` type, so use heuristics.
    narrative_role = str(scene.get("narrative_role") or "").lower()
    if narrative_role == "evidence":
        return True
    desc = str(scene.get("description") or "").lower()
    if "stat card" in desc or "stat_card" in desc or "kpi" in desc:
        return True
    return False


def _detect_analyst_or_media_claim(claim: dict[str, Any]) -> bool:
    source_type = str(claim.get("source_type") or claim.get("source") or claim.get("kind") or "").lower()
    return source_type in {"analyst", "media", "press", "report"}


def _claim_confidence(claim: dict[str, Any]) -> str:
    val = claim.get("confidence") or claim.get("confidence_label") or ""
    return str(val).strip().lower()


def _validate_scene_plan_structure(
    scene_plan: dict[str, Any],
    known_device_ids: set[str],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    ctx.checks_run.append("scene_plan_structure")
    scenes = scene_plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scene_plan.scenes[] missing or empty")
        return {}

    summary = {
        "scene_count": len(scenes),
        "scenes_missing_state_changes": 0,
        "max_state_gap_seconds": 0.0,
    }

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"scene[{idx}] is not an object")
            continue

        sid = scene.get("id") or f"scene[{idx}]"
        st = _coerce_float(scene.get("start_seconds"))
        en = _coerce_float(scene.get("end_seconds"))
        if st is None or en is None:
            errors.append(f"{sid}: start_seconds/end_seconds must be numbers")
            continue
        if en <= st:
            errors.append(f"{sid}: start_seconds ({st}) >= end_seconds ({en})")
            continue

        if not str(scene.get("type") or "").strip():
            errors.append(f"{sid}: missing type")
        if not str(scene.get("description") or "").strip():
            errors.append(f"{sid}: missing description")

        dur = en - st
        if ctx.style_playbook == "asymmetric" and dur > 4.0 and not _is_state_change_exempt(scene):
            state_changes = scene.get("state_changes")
            if not isinstance(state_changes, list) or not state_changes:
                errors.append(
                    f"{sid}: duration {dur:.1f}s > 4s but state_changes[] missing "
                    "(add beats every 2–4s or mark exemption via texture_keywords=['state_change_exempt'])"
                )
                summary["scenes_missing_state_changes"] += 1
                continue

            times: list[float] = []
            last_t = -1.0
            for j, sc in enumerate(state_changes):
                if not isinstance(sc, dict):
                    errors.append(f"{sid}: state_changes[{j}] is not an object")
                    continue
                t = _coerce_float(sc.get("t"))
                if t is None:
                    errors.append(f"{sid}: state_changes[{j}].t must be a number")
                    continue
                if t < 0:
                    errors.append(f"{sid}: state_changes[{j}].t must be >= 0")
                    continue
                if t < last_t:
                    errors.append(f"{sid}: state_changes[] must be sorted by t (found {t} after {last_t})")
                last_t = t
                if t > dur + 1e-6:
                    errors.append(f"{sid}: state_changes[{j}].t ({t}) exceeds scene duration ({dur:.1f}s)")

                device_id = sc.get("device_id")
                if device_id is not None:
                    if not isinstance(device_id, str) or device_id not in known_device_ids:
                        errors.append(f"{sid}: state_changes[{j}].device_id unknown: {device_id!r}")

                if sc.get("visual_state_change") is True:
                    times.append(t)

            # Enforce gaps: from scene start (0) to first, between, and last to scene end.
            boundaries = [0.0] + sorted(set(times)) + [dur]
            for a, b in zip(boundaries, boundaries[1:]):
                gap = b - a
                summary["max_state_gap_seconds"] = max(summary["max_state_gap_seconds"], gap)
                if gap > 4.0 + 1e-6:
                    errors.append(
                        f"{sid}: visual state holds {gap:.1f}s (>4.0s) between beats at t={a:.1f}s and t={b:.1f}s"
                    )

    return summary


def _validate_scene_plan_retention_motion(
    scene_plan: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Retention-motion QA for Asymmetric scene plans.

    This is intentionally redundant with schema + director skills: it blocks
    plans that look like calm chart decks (text-only updates, no narrative
    reason to watch) even when the JSON structure is valid.
    """
    ctx.checks_run.append("scene_plan_retention_motion")
    if ctx.style_playbook != "asymmetric":
        return

    scenes = scene_plan.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        return

    required_fields = [
        "viewer_hook",
        "tension_type",
        "visual_event_cadence_seconds",
        "retention_function",
        "payoff_moment",
        "next_open_loop",
    ]
    valid_tensions = {
        "mystery",
        "contradiction",
        "escalation",
        "constraint",
        "substitution_failure",
        "consequence",
        "reversal",
        "hidden_actor",
        "bottleneck",
        "proof",
        "synthesis",
        "payoff",
    }

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id") or f"scene[{idx}]"

        # Required retention fields (strict for Asymmetric)
        for field in required_fields:
            val = scene.get(field)
            if field == "next_open_loop" and idx == len(scenes) - 1:
                # Final scene may intentionally close loops; allow empty.
                continue
            if val is None:
                errors.append(f"{sid}: missing required retention field '{field}'")
            elif isinstance(val, str) and not val.strip():
                errors.append(f"{sid}: retention field '{field}' is empty")

        tt = scene.get("tension_type")
        if isinstance(tt, str) and tt and tt not in valid_tensions:
            errors.append(f"{sid}: invalid tension_type '{tt}'")

        cadence = _coerce_float(scene.get("visual_event_cadence_seconds"))
        if cadence is None:
            errors.append(f"{sid}: visual_event_cadence_seconds must be a number")
        else:
            # Asymmetric contract: no long gaps without meaningful events.
            if cadence > 8.0 + 1e-6:
                msg = f"{sid}: visual_event_cadence_seconds={cadence:.1f} (>8.0s) violates Asymmetric retention cadence"
                if ctx.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        # Text-only / card-only change detection (diagram-heavy deck smell).
        dur = _scene_duration(scene) or 0.0
        if dur > 4.0 and not _is_state_change_exempt(scene):
            state_changes = scene.get("state_changes") or []
            if isinstance(state_changes, list) and state_changes:
                visual_beats = [
                    sc
                    for sc in state_changes
                    if isinstance(sc, dict) and sc.get("visual_state_change") is True
                ]
                device_beats = [
                    sc
                    for sc in visual_beats
                    if isinstance(sc.get("device_id"), str) and sc.get("device_id")
                ]

                stype = str(scene.get("type") or "").strip().lower()
                if stype in {"diagram", "animation", "generated", "screen_recording"}:
                    if not device_beats:
                        errors.append(
                            f"{sid}: {stype} scene has visual beats but none are device-driven "
                            "(looks like text/card-only updates; add route trace / reveal / contradiction / proof events)"
                        )
                    elif len(device_beats) / max(1, len(visual_beats)) < 0.5:
                        warnings.append(
                            f"{sid}: only {len(device_beats)}/{len(visual_beats)} visual beats are device-driven "
                            "(risk: calm deck energy)"
                        )

            # Stat scenes must be framed as proof/contradiction (retention_function should reflect it)
            if _detect_stat_scene(scene):
                rf = str(scene.get("retention_function") or "").lower()
                if rf and not any(k in rf for k in ("proof", "contradiction", "evidence", "refute", "verify")):
                    warnings.append(
                        f"{sid}: stat-card-like scene retention_function does not read as proof/contradiction "
                        "(risk: decorative numbers)"
                    )


def _validate_device_references(
    scene_plan: dict[str, Any],
    device_manifest_path: Path,
    known_device_ids: set[str],
    device_index: dict[str, dict[str, Any]],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> None:
    ctx.checks_run.append("device_references")
    scenes = scene_plan.get("scenes") or []
    if not isinstance(scenes, list):
        return

    spec_required_cache: dict[str, set[str]] = {}

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id") or f"scene[{idx}]"
        devices = scene.get("devices") or []
        if devices is None:
            continue
        if not isinstance(devices, list):
            errors.append(f"{sid}: devices must be an array")
            continue
        for j, dev in enumerate(devices):
            if not isinstance(dev, dict):
                errors.append(f"{sid}: devices[{j}] is not an object")
                continue
            device_id = dev.get("device_id")
            if not isinstance(device_id, str) or device_id not in known_device_ids:
                errors.append(f"{sid}: devices[{j}].device_id unknown: {device_id!r}")
                continue

            params = dev.get("params") or {}
            if params is None:
                params = {}
            if not isinstance(params, dict):
                errors.append(f"{sid}: devices[{j}].params must be an object")
                continue

            entry = device_index.get(device_id, {})
            spec_path_str = entry.get("spec_path")
            if isinstance(spec_path_str, str) and spec_path_str:
                spec_path = Path(spec_path_str)
                if not spec_path.is_absolute():
                    # Most manifests store repo-relative paths like
                    # "channel_assets/asymmetric/...". Resolve those from CWD
                    # (repo root in normal runs). Otherwise, resolve relative
                    # to the manifest directory.
                    if spec_path_str.replace("\\", "/").startswith(("channel_assets/", "tools/", "schemas/", "skills/", "styles/")):
                        spec_path = (Path.cwd() / spec_path).resolve()
                    else:
                        spec_path = (device_manifest_path.parent / spec_path).resolve()
                if device_id not in spec_required_cache:
                    try:
                        spec_required_cache[device_id] = _load_device_required_params(spec_path)
                    except ValueError as e:
                        warnings.append(f"{sid}: could not load spec for {device_id}: {e}")
                        spec_required_cache[device_id] = set()

                missing = sorted(p for p in spec_required_cache[device_id] if p not in params)
                if missing:
                    errors.append(f"{sid}: device {device_id} missing required params: {', '.join(missing)}")


def _validate_required_device_coverage(
    scene_plan: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    ctx.checks_run.append("required_device_coverage")
    scenes = scene_plan.get("scenes") or []
    devices_seen: set[str] = set()
    if isinstance(scenes, list):
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            for dev in scene.get("devices") or []:
                if isinstance(dev, dict) and isinstance(dev.get("device_id"), str):
                    devices_seen.add(dev["device_id"])

    coverage = {
        "devices_seen": sorted(devices_seen),
        "missing": [],
        "satisfied": [],
    }

    if ctx.style_playbook != "asymmetric":
        return coverage

    required_groups = {
        "system_map": {"route-trace", "dependency-tree-stop-point"},
        "chokepoint_reveal": {"amber-pivot-marker", "chokepoint-ring", "collapse-to-one-node"},
        "surface_vs_structure": {"surface-vs-structure-split", "xray-layer-reveal", "blueprint-reveal"},
        "source_evidence_moment": {"source-card-reveal"},
        "final_leverage_map": {"final-leverage-map"},
    }

    for group, options in required_groups.items():
        if devices_seen.intersection(options):
            coverage["satisfied"].append(group)
        else:
            coverage["missing"].append(group)
            errors.append(
                f"Missing required Asymmetric device coverage '{group}': add one of {sorted(options)}"
            )

    return coverage


def _validate_fallbacks(
    scene_plan: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> None:
    ctx.checks_run.append("generated_image_fallbacks")
    scenes = scene_plan.get("scenes") or []
    if not isinstance(scenes, list):
        return

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id") or f"scene[{idx}]"
        for j, ra in enumerate(scene.get("required_assets") or []):
            if not isinstance(ra, dict):
                continue
            src = str(ra.get("source") or "").lower()
            asset_type = str(ra.get("type") or "").lower()
            fallback_type = ra.get("fallback_type")
            if fallback_type is not None and str(fallback_type) not in FALLBACK_TYPES:
                errors.append(f"{sid}: required_assets[{j}].fallback_type invalid: {fallback_type!r}")

            is_generated = src == "generate"
            looks_like_image = asset_type in {"image", "generated_image", "illustration"} or (
                "image" in asset_type and asset_type
            )

            if ctx.style_playbook == "asymmetric" and is_generated and looks_like_image:
                # Require a non-generated fallback path/type.
                ft = str(fallback_type or "").strip()
                if ft not in {"svg_css", "hyperframes_native"}:
                    msg = (
                        f"{sid}: required_assets[{j}] is generated image but has no SVG/CSS or HyperFrames-native fallback "
                        f"(set fallback_type to 'svg_css' or 'hyperframes_native')"
                    )
                    if ctx.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

            if str(fallback_type or "") == "stock":
                warnings.append(
                    f"{sid}: required_assets[{j}] uses stock fallback_type; Asymmetric prefers interface-native SVG/CSS (stock is not default)"
                )

            if ra.get("fallback_required") is True:
                fp = ra.get("fallback_path") or ra.get("file")
                if not fp:
                    errors.append(f"{sid}: required_assets[{j}] fallback_required=true but no fallback_path/file provided")
                else:
                    # Allow "planned:" sentinel.
                    if isinstance(fp, str) and fp.strip().lower().startswith("planned:"):
                        continue
                    if isinstance(fp, str):
                        if not Path(fp).exists():
                            warnings.append(f"{sid}: required_assets[{j}] fallback path does not exist yet: {fp}")


def _validate_evidence_and_stats(
    scene_plan: dict[str, Any],
    source_map: dict[str, Any] | None,
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    ctx.checks_run.append("evidence_and_stats")
    claims_by_id = _normalize_claims(source_map or {})
    scenes = scene_plan.get("scenes") or []
    if not isinstance(scenes, list):
        return {"claims_referenced": [], "claims_missing": []}

    referenced: set[str] = set()
    missing: set[str] = set()

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id") or f"scene[{idx}]"

        claim_ids = scene.get("source_claim_ids") or []
        if claim_ids and not isinstance(claim_ids, list):
            errors.append(f"{sid}: source_claim_ids must be an array of strings")
            continue

        is_stat_scene = _detect_stat_scene(scene)
        if is_stat_scene and (not claim_ids) and ctx.style_playbook == "asymmetric":
            errors.append(f"{sid}: stat/evidence scene missing source_claim_ids[] for hard claims")

        qualifier_required = scene.get("qualifier_required") is True
        desc = str(scene.get("description") or "")
        desc_l = desc.lower()
        has_qualifier_text = any(k in desc_l for k in ["estimate", "estimated", "approx", "roughly", "reportedly", "according to"])

        for cid in claim_ids if isinstance(claim_ids, list) else []:
            if not isinstance(cid, str):
                continue
            referenced.add(cid)
            claim = claims_by_id.get(cid)
            if not claim:
                missing.add(cid)
                errors.append(f"{sid}: source_claim_id not found in source_map.claims[]: {cid}")
                continue

            if _detect_analyst_or_media_claim(claim):
                if not qualifier_required and not has_qualifier_text:
                    errors.append(
                        f"{sid}: analyst/media-sourced claim '{cid}' requires qualifier_required=true or an on-screen qualifier in description"
                    )

            permitted = claim.get("hard_stat_card_permitted")
            if permitted is False and is_stat_scene:
                errors.append(f"{sid}: claim '{cid}' is not permitted as a hard stat card (hard_stat_card_permitted=false)")

            conf = _claim_confidence(claim)
            if conf in {"low", "unknown"} and is_stat_scene:
                errors.append(f"{sid}: low-confidence claim '{cid}' cannot be presented as a hard stat card (confidence={conf})")

    if source_map is None and referenced:
        warnings.append("source_map not provided; source_claim_ids validation is limited")

    return {
        "claims_referenced": sorted(referenced),
        "claims_missing": sorted(missing),
    }


def _validate_color_semantics_and_antipatterns(
    scene_plan: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> None:
    ctx.checks_run.append("color_semantics_and_antipatterns")
    scenes = scene_plan.get("scenes") or []
    if not isinstance(scenes, list):
        return

    # Very light heuristics (avoid overfitting).
    misuse_red = re.compile(r"\bred\b.*\b(accent|highlight|decorative|brand)\b", re.I)
    decorative_amber = re.compile(r"\bamber\b.*\b(accent|decorative|brand)\b", re.I)

    antipattern_terms = [
        ("cyberpunk", "cyberpunk"),
        ("spy", "spy"),
        ("intelligence", "intelligence-roleplay"),
        ("control room", "control-room fantasy"),
        ("neon", "neon overload"),
        ("life hack", "life-hack framing"),
        ("gamer", "gamer-meta language"),
        ("stock photo", "stock-photo documentary default"),
        ("talking head", "recurring human host"),
        ("host", "recurring human host"),
    ]

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id") or f"scene[{idx}]"
        desc = str(scene.get("description") or "")
        if misuse_red.search(desc):
            errors.append(f"{sid}: red appears used as a general accent; red must be consequence/failure/exposure only")
        if decorative_amber.search(desc):
            warnings.append(f"{sid}: amber appears described as decorative; amber must mark leverage/chokepoint only")

        if ctx.style_playbook == "asymmetric":
            stype = str(scene.get("type") or "").lower()
            if stype == "talking_head":
                msg = f"{sid}: talking_head scene in Asymmetric (no recurring human host by default)"
                if ctx.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

            dl = desc.lower()
            for needle, label in antipattern_terms:
                if needle in dl:
                    warnings.append(f"{sid}: possible anti-pattern language: {label}")


def _asset_manifest_project_root(asset_manifest_path: Path) -> Path:
    # Convention: projects/<name>/artifacts/asset_manifest.json
    parent = asset_manifest_path.parent
    if parent.name == "artifacts":
        return parent.parent
    return parent


def _validate_asset_manifest(
    asset_manifest_path: Path,
    asset_manifest: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    ctx.checks_run.append("asset_manifest")
    assets = asset_manifest.get("assets")
    if not isinstance(assets, list):
        errors.append("asset_manifest.assets[] missing or not an array")
        return {}

    root = _asset_manifest_project_root(asset_manifest_path)
    missing_files: list[str] = []
    suspect_truncation: list[str] = []
    truncation_receipts: list[str] = []

    provider_blocks = asset_manifest.get("provider_blocks")
    if provider_blocks is None:
        # Backward-compatible location used by older runs/tests.
        meta = asset_manifest.get("metadata") or {}
        if isinstance(meta, dict):
            provider_blocks = meta.get("provider_block_receipts") or meta.get("provider_blocks")

    if ctx.style_playbook == "asymmetric":
        if not provider_blocks:
            msg = "asset_manifest missing provider_blocks receipts for local GPU/provider sequencing"
            if ctx.strict:
                errors.append(msg)
            else:
                warnings.append(msg)

    for a in assets:
        if not isinstance(a, dict):
            continue
        apath = a.get("path")
        if isinstance(apath, str) and apath:
            resolved = (root / apath).resolve()
            if not resolved.exists():
                generation_status = str(a.get("generation_status") or "").strip().lower()
                fallback_type = str(a.get("fallback_type") or "").strip()
                fallback_path = a.get("fallback_path")
                # If generation was deferred/failed and a valid fallback is present, do not fail for the missing primary.
                if generation_status in {"failed", "deferred", "skipped"} and fallback_type in {"svg_css", "hyperframes_native"}:
                    if isinstance(fallback_path, str) and fallback_path.strip().lower().startswith("planned:"):
                        continue
                    if isinstance(fallback_path, str) and Path(fallback_path).exists():
                        continue
                missing_files.append(apath)

        # Fish Speech truncation detection: fail if any narration/audio is capped ~48s.
        atype = str(a.get("type") or "").lower()
        dur = _coerce_float(a.get("duration_seconds"))
        if dur is not None and 47.0 <= dur <= 49.5 and atype in {"narration", "audio"}:
            suspect_truncation.append(str(a.get("id") or apath or "<unknown>"))

        # Generated imagery fallback governance (asset-level).
        generation_status = str(a.get("generation_status") or "").strip().lower()
        fallback_type = str(a.get("fallback_type") or "").strip()
        if ctx.style_playbook == "asymmetric" and atype in {"image", "diagram", "animation"}:
            if generation_status in {"failed", "deferred"}:
                if fallback_type not in {"svg_css", "hyperframes_native"}:
                    msg = (
                        f"asset_manifest asset '{a.get('id') or apath}': generation_status={generation_status} "
                        "but missing svg_css/hyperframes_native fallback_type"
                    )
                    if ctx.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

    # Chunked TTS receipts (formal field).
    receipts = asset_manifest.get("tts_chunk_receipts") or []
    if isinstance(receipts, list):
        for r in receipts:
            if not isinstance(r, dict):
                continue
            section_id = str(r.get("section_id") or "<unknown>")
            for c in r.get("chunks") or []:
                if not isinstance(c, dict):
                    continue
                cdur = _coerce_float(c.get("duration_seconds"))
                suspected = c.get("suspected_truncation") is True
                if suspected:
                    truncation_receipts.append(f"{section_id}:{c.get('chunk_id')}")
                if cdur is not None and 47.0 <= cdur <= 49.5:
                    truncation_receipts.append(f"{section_id}:{c.get('chunk_id')}")

    if missing_files:
        errors.append(f"asset_manifest references missing files ({len(missing_files)}): {missing_files[:5]}")

    if suspect_truncation or truncation_receipts:
        errors.append(
            "Suspected Fish Speech truncation: narration/audio duration ~48s or truncation receipts present for "
            f"assets={suspect_truncation} receipts={truncation_receipts}"
        )

    # Provider status term scan (best-effort).
    meta = asset_manifest.get("metadata") or {}
    if isinstance(meta, dict):
        meta_text = json.dumps(meta).lower()
        for term in ["busy", "failed_after_isolation", "compatibility_failure", "deferred_svg_css_fallback"]:
            if term in meta_text:
                # good: term present somewhere
                continue

    return {
        "asset_count": len(assets),
        "missing_files_count": len(missing_files),
        "suspected_truncation_count": len(suspect_truncation) + len(truncation_receipts),
        "project_root": str(root),
    }


def _validate_script_retention_rules(
    script: dict[str, Any],
    ctx: ValidationContext,
    errors: list[str],
    warnings: list[str],
) -> None:
    ctx.checks_run.append("script_retention_rules")
    sections = script.get("sections")
    if not isinstance(sections, list) or not sections:
        return

    # 1. Hook Rule (First 20s)
    # Only enforce if style is asymmetric
    is_asymmetric = ctx.style_playbook == "asymmetric"
    
    if is_asymmetric:
        first_section = sections[0]
        first_text = str(first_section.get("text") or "").lower()
        bad_hooks = [
            "in this video", 
            "welcome back", 
            "let's dive", 
            "to understand this",
            "today we're going to",
            "we're going to look at",
            "this video is about"
        ]
        for bh in bad_hooks:
            if bh in first_text:
                msg = f"Script hook contains forbidden throat-clearing: '{bh}'"
                if ctx.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

    # 2. Section Retention Fields
    for idx, s in enumerate(sections):
        sid = s.get("id") or f"section[{idx}]"
        
        if is_asymmetric:
            required_retention = [
                "viewer_question", "tension_type", "open_loop", 
                "proof_moment", "consequence", "payoff", 
                "next_open_loop", "visual_event_plan"
            ]
            
            # next_open_loop can be empty for the last section
            for field in required_retention:
                val = s.get(field)
                if idx == len(sections) - 1 and field == "next_open_loop":
                    continue
                if val is None or (isinstance(val, str) and not val.strip()):
                    errors.append(f"{sid}: missing required retention field '{field}'")
            
            # Tension Type Enum Check
            valid_tensions = {
                "mystery", "contradiction", "escalation", "constraint",
                "substitution_failure", "consequence", "reversal",
                "hidden_actor", "bottleneck", "proof", "synthesis", "payoff"
            }
            tt = s.get("tension_type")
            if tt and tt not in valid_tensions:
                errors.append(f"{sid}: invalid tension_type '{tt}'")

        # 3. Visual Event Plan Cadence (5-8s)
        ve_plan = s.get("visual_event_plan")
        if isinstance(ve_plan, list):
            dur = _coerce_float(s.get("end_seconds")) - _coerce_float(s.get("start_seconds"))
            times = sorted([_coerce_float(ve.get("t")) for ve in ve_plan if _coerce_float(ve.get("t")) is not None])
            
            # Add implicit boundaries
            boundaries = [0.0] + times + [dur]
            for i in range(len(boundaries) - 1):
                gap = boundaries[i+1] - boundaries[i]
                if gap > 8.0:
                    msg = f"{sid}: visual event gap too large ({gap:.1f}s > 8s) between t={boundaries[i]:.1f} and t={boundaries[i+1]:.1f}"
                    if is_asymmetric and ctx.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
        elif not ve_plan and is_asymmetric and ctx.strict:
            errors.append(f"{sid}: missing visual_event_plan")

        # 4. Source Claim IDs for Asymmetric
        if is_asymmetric:
            claim_ids = s.get("source_claim_ids")
            if not isinstance(claim_ids, list) or not claim_ids:
                # Asymmetric sections are built around proof; strict mode requires grounding.
                msg = f"{sid}: missing required source_claim_ids (Asymmetric requires proof grounding per section)"
                if ctx.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)


def validate_asymmetric_video(
    *,
    scene_plan_path: Path | None,
    script_path: Path | None = None,
    proposal_packet_path: Path | None = None,
    project_config_path: Path | None = None,
    source_map_path: Path | None,
    asset_manifest_path: Path | None,
    style_playbook: str,
    device_manifest_path: Path,
    stage: str,
    strict: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    ctx = ValidationContext(
        stage=stage,
        strict=strict,
        style_playbook=_norm_style(style_playbook),
        device_manifest_path=device_manifest_path,
        files_checked=[],
        checks_run=[],
    )

    manifest = _device_manifest(device_manifest_path)
    known_ids, device_index = _device_index(manifest)
    ctx.files_checked.append(str(device_manifest_path))

    scene_plan: dict[str, Any] | None = None
    if scene_plan_path is not None:
        scene_plan = _load_json(scene_plan_path)
        ctx.files_checked.append(str(scene_plan_path))
    script: dict[str, Any] | None = None
    if script_path is not None:
        script = _load_json(script_path)
        ctx.files_checked.append(str(script_path))
    proposal_packet: dict[str, Any] | None = None
    if proposal_packet_path is not None:
        proposal_packet = _load_json(proposal_packet_path)
        ctx.files_checked.append(str(proposal_packet_path))
    project_config: dict[str, Any] | None = None
    if project_config_path is not None:
        project_config = _load_json(project_config_path)
        ctx.files_checked.append(str(project_config_path))
    source_map: dict[str, Any] | None = None
    if source_map_path is not None:
        source_map = _load_json(source_map_path)
        ctx.files_checked.append(str(source_map_path))
    asset_manifest: dict[str, Any] | None = None
    if asset_manifest_path is not None:
        asset_manifest = _load_json(asset_manifest_path)
        ctx.files_checked.append(str(asset_manifest_path))

    device_coverage: dict[str, Any] = {}
    source_claim_coverage: dict[str, Any] = {}
    scene_state_change_summary: dict[str, Any] = {}
    duration_alignment: dict[str, Any] = {}
    asset_manifest_summary: dict[str, Any] = {}

    if script is not None:
        _validate_script_retention_rules(script, ctx, errors, warnings)

    # Script-only validation path (used to hard-gate retention + word budget before scene planning).
    if stage == "script" and script is not None:
        duration_alignment = _validate_duration_alignment(
            scene_plan=None,
            script=script,
            proposal_packet=proposal_packet,
            project_config=project_config,
            asset_manifest=None,
            ctx=ctx,
            errors=errors,
            warnings=warnings,
        )

    if scene_plan is None:
        if stage in {"scene_plan", "assets", "final"}:
            errors.append("scene_plan is required for stage=scene_plan/assets/final")
    else:
        scene_state_change_summary = _validate_scene_plan_structure(
            scene_plan, known_ids, ctx, errors, warnings
        )
        _validate_scene_plan_retention_motion(scene_plan, ctx, errors, warnings)
        _validate_device_references(
            scene_plan, device_manifest_path, known_ids, device_index, ctx, errors, warnings
        )
        device_coverage = _validate_required_device_coverage(scene_plan, ctx, errors, warnings)
        _validate_fallbacks(scene_plan, ctx, errors, warnings)
        source_claim_coverage = _validate_evidence_and_stats(scene_plan, source_map, ctx, errors, warnings)
        _validate_color_semantics_and_antipatterns(scene_plan, ctx, errors, warnings)
        duration_alignment = _validate_duration_alignment(
            scene_plan=scene_plan,
            script=script,
            proposal_packet=proposal_packet,
            project_config=project_config,
            asset_manifest=asset_manifest if stage in {"assets", "final"} else None,
            ctx=ctx,
            errors=errors,
            warnings=warnings,
        )

    if asset_manifest is not None and asset_manifest_path is not None and stage in {"assets", "final"}:
        asset_manifest_summary = _validate_asset_manifest(
            asset_manifest_path, asset_manifest, ctx, errors, warnings
        )

    passed = len(errors) == 0
    receipt = {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "checks_run": ctx.checks_run,
        "files_checked": ctx.files_checked,
        "device_coverage": device_coverage,
        "source_claim_coverage": source_claim_coverage,
        "scene_state_change_summary": scene_state_change_summary,
        "duration_alignment": duration_alignment,
        "asset_manifest_summary": asset_manifest_summary,
    }
    return receipt


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="asymmetric_video_validator",
        description="Validate Asymmetric scene plans / assets for device-driven, source-aware, fallback-safe planning.",
    )
    p.add_argument("--scene-plan", dest="scene_plan", type=str, default=None)
    p.add_argument("--script", dest="script", type=str, default=None)
    p.add_argument("--proposal-packet", dest="proposal_packet", type=str, default=None)
    p.add_argument("--project-config", dest="project_config", type=str, default=None)
    p.add_argument("--source-map", dest="source_map", type=str, default=None)
    p.add_argument("--asset-manifest", dest="asset_manifest", type=str, default=None)
    p.add_argument("--style-playbook", dest="style_playbook", type=str, default="asymmetric")
    p.add_argument(
        "--device-manifest",
        dest="device_manifest",
        type=str,
        default=DEVICE_MANIFEST_DEFAULT,
    )
    p.add_argument("--output", dest="output", type=str, default=None)
    p.add_argument(
        "--stage",
        dest="stage",
        type=str,
        choices=["script", "scene_plan", "assets", "final"],
        default="scene_plan",
    )
    p.add_argument("--strict", dest="strict", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    scene_plan_path = Path(args.scene_plan).resolve() if args.scene_plan else None
    script_path = Path(args.script).resolve() if args.script else None
    proposal_packet_path = Path(args.proposal_packet).resolve() if args.proposal_packet else None
    project_config_path = Path(args.project_config).resolve() if args.project_config else None
    source_map_path = Path(args.source_map).resolve() if args.source_map else None
    asset_manifest_path = Path(args.asset_manifest).resolve() if args.asset_manifest else None
    device_manifest_path = Path(args.device_manifest).resolve()

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        proposal_packet_path=proposal_packet_path,
        project_config_path=project_config_path,
        source_map_path=source_map_path,
        asset_manifest_path=asset_manifest_path,
        style_playbook=args.style_playbook,
        device_manifest_path=device_manifest_path,
        stage=args.stage,
        strict=bool(args.strict),
    )

    if args.output:
        _write_json(Path(args.output).resolve(), receipt)

    # Human-friendly summary to stderr; full detail in JSON output.
    if receipt["passed"]:
        print("Asymmetric validation: PASS", file=sys.stderr)
        if receipt["warnings"]:
            print(f"Warnings: {len(receipt['warnings'])}", file=sys.stderr)
        return 0

    print("Asymmetric validation: FAIL", file=sys.stderr)
    for e in receipt["errors"][:20]:
        print(f"- {e}", file=sys.stderr)
    if len(receipt["errors"]) > 20:
        print(f"... ({len(receipt['errors']) - 20} more errors)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
