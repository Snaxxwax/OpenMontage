#!/usr/bin/env python3
"""Compose source proof card images from raw screenshots.

Reads source_card_manifest.json, crops each source image, and pastes
it onto a white canvas. Writes a QC report. Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIN_QUOTE_PROOF_BOTTOM_MARGIN = 90


def _safe_output_path(output_path_str: str, project_root: Path) -> Path:
    """Resolve output_path. Raise ValueError if it escapes project root or assets/composed/."""
    if not output_path_str.startswith("assets/composed/"):
        raise ValueError(
            f"output_path must be under assets/composed/: {output_path_str!r}"
        )
    if ".." in output_path_str:
        raise ValueError(f"output_path must not contain ..: {output_path_str!r}")
    resolved = (project_root / output_path_str).resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        raise ValueError(f"output_path escapes project root: {output_path_str!r}")
    return resolved


def _compose_card(card: dict[str, Any], project_root: Path) -> list[str]:
    """Compose one card. Returns list of failure strings (empty = success)."""
    from PIL import Image  # type: ignore

    card_id = card.get("card_id", "?")
    card_type = card.get("card_type", "unknown")
    failures: list[str] = []

    # Validate and resolve output_path
    output_path_str = card.get("output_path", "")
    try:
        output_path = _safe_output_path(output_path_str, project_root)
    except ValueError as exc:
        failures.append(f"{card_id}: {exc}")
        return failures

    # Resolve source_path — must stay inside project root
    source_path_str = card.get("source_path", "")
    if ".." in source_path_str:
        failures.append(f"{card_id}: source_path must not contain ..: {source_path_str!r}")
        return failures
    source_path = (project_root / source_path_str).resolve()
    try:
        source_path.relative_to(project_root.resolve())
    except ValueError:
        failures.append(f"{card_id}: source_path escapes project root: {source_path_str!r}")
        return failures
    if not source_path.exists():
        failures.append(f"{card_id}: source_path does not exist: {source_path_str}")
        return failures

    # Open source image
    try:
        img = Image.open(source_path).convert("RGB")
        img_w, img_h = img.size
    except Exception as exc:
        failures.append(f"{card_id}: could not open source image: {exc}")
        return failures

    # Parse crop
    crop = card.get("crop", {})
    cx, cy = crop.get("x", 0), crop.get("y", 0)
    cw, ch = crop.get("w", 0), crop.get("h", 0)

    if cx + cw > img_w or cy + ch > img_h:
        failures.append(
            f"{card_id}: crop ({cx},{cy})+({cw}x{ch}) exceeds image bounds "
            f"({img_w}x{img_h})"
        )
        return failures

    # Parse canvas
    canvas = card.get("canvas", {})
    canvas_w = canvas.get("w", 0)
    canvas_h = canvas.get("h", 0)
    top_margin = canvas.get("top_margin", 0)
    bottom_safe_margin_px = canvas.get("bottom_safe_margin_px")

    # quote_proof: bottom_safe_margin_px required and >= MIN
    if card_type == "quote_proof":
        if bottom_safe_margin_px is None:
            failures.append(
                f"{card_id}: quote_proof requires canvas.bottom_safe_margin_px"
            )
            return failures
        if bottom_safe_margin_px < MIN_QUOTE_PROOF_BOTTOM_MARGIN:
            failures.append(
                f"{card_id}: quote_proof canvas.bottom_safe_margin_px "
                f"{bottom_safe_margin_px} < {MIN_QUOTE_PROOF_BOTTOM_MARGIN}"
            )
            return failures
        computed_bottom = canvas_h - top_margin - ch
        if computed_bottom < bottom_safe_margin_px:
            failures.append(
                f"{card_id}: quote_proof computed bottom clear {computed_bottom}px "
                f"< required {bottom_safe_margin_px}px "
                f"(canvas_h={canvas_h}, top_margin={top_margin}, crop_h={ch})"
            )
            return failures

    # Compose: paste crop onto white canvas at top_margin
    cropped = img.crop((cx, cy, cx + cw, cy + ch))
    canvas_img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    canvas_img.paste(cropped, (0, top_margin))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas_img.save(output_path)

    return failures


def compose_source_cards(
    manifest: dict[str, Any],
    project_root: Path,
    output_path: Path,
) -> int:
    """Compose all cards. Always writes output_path. Returns 0 (pass) or 1 (fail)."""
    episode_id = manifest.get("episode_id", "unknown")
    cards = manifest.get("cards", [])
    checked_at = datetime.now(timezone.utc).isoformat()

    all_failures: list[str] = []
    rows: list[tuple[str, str, str, str]] = []

    for card in cards:
        card_id = card.get("card_id", "?")
        card_type = card.get("card_type", "unknown")
        out_str = card.get("output_path", "—")

        failures = _compose_card(card, project_root)
        all_failures.extend(failures)
        status = "FAIL" if failures else "PASS"
        rows.append((card_id, card_type, out_str, status))

    overall = "PASS" if not all_failures else "FAIL"

    lines = [
        f"# Source Card Composition QC — {episode_id}",
        "",
        f"**checked_at:** {checked_at}  ",
        f"**verdict:** {overall}  ",
        "",
        "| card_id | type | output | status |",
        "|---|---|---|---|",
    ]
    for card_id, card_type, out, status in rows:
        lines.append(f"| {card_id} | {card_type} | {out} | {status} |")

    lines += ["", "## Failures"]
    if all_failures:
        for msg in all_failures:
            lines.append(f"- {msg}")
    else:
        lines.append("(none)")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0 if not all_failures else 1


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compose source proof card images from raw screenshots."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = _load_json(args.manifest)
    # manifest lives at <project>/artifacts/source_card_manifest.json
    project_root = args.manifest.resolve().parent.parent
    return compose_source_cards(
        manifest=manifest,
        project_root=project_root,
        output_path=args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
