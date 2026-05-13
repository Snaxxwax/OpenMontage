#!/usr/bin/env python3
"""Create local real-smoke source card assets from approved metadata.

This helper intentionally does not fetch pages, drive a browser, or download
media. It turns already-reviewed source/evidence metadata into deterministic
local source cards plus JSON sidecars for pipeline smoke tests.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from lib.artifact_bus import DEFAULT_PROJECTS_DIR
from lib.source_proof import SourceProofAsset, SourceProofManifest

DEFAULT_RUN_BASE_DIR = DEFAULT_PROJECTS_DIR
SUPPORTED_FORMATS = {"html", "txt"}


class AcquisitionError(RuntimeError):
    """Expected operator-facing acquisition failure."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AcquisitionError(f"missing JSON artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AcquisitionError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AcquisitionError(f"JSON artifact must contain an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:80] or "source-card"


def normalize_claim_ids(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [value]
    return []


def read_optional_artifact(artifact_dir: Path, filename: str) -> dict[str, Any]:
    path = artifact_dir / filename
    if not path.exists():
        return {}
    return load_json(path)


def index_sources(source_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(source["id"]): source
        for source in source_manifest.get("sources") or []
        if isinstance(source, dict) and source.get("id")
    }


def index_rights(rights_manifest: dict[str, Any]) -> dict[str, str]:
    rights: dict[str, str] = {}
    for item in rights_manifest.get("items") or []:
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("evidence_id")
        if evidence_id:
            rights[str(evidence_id)] = str(item.get("risk_level") or item.get("rights_risk") or "unknown")
    return rights


def youtube_metadata(youtube_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in youtube_manifest.get("videos") or [] if isinstance(item, dict)]


def find_youtube_details(*, url: str, source_id: str, videos: list[dict[str, Any]]) -> dict[str, str]:
    for video in videos:
        if video.get("url") == url or video.get("source_id") == source_id:
            return {
                key: str(video[key])
                for key in ["title", "channel", "upload_date"]
                if video.get(key) is not None
            }
    return {}


def claim_ids_overlap(left: list[str], right: list[str]) -> bool:
    return bool(set(left) & set(right)) if left and right else False


def find_capture_for_evidence(evidence: dict[str, Any], captures: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_claim_ids = normalize_claim_ids(evidence.get("claim_ids")) or normalize_claim_ids(evidence.get("claim_id"))
    source_id = evidence.get("source_id")
    for capture in captures:
        if not isinstance(capture, dict) or capture.get("approved") is not True:
            continue
        if capture.get("source_id") != source_id:
            continue
        capture_claim_ids = normalize_claim_ids(capture.get("claim_ids"))
        if claim_ids_overlap(evidence_claim_ids, capture_claim_ids) or not evidence_claim_ids:
            return capture
    for capture in captures:
        if isinstance(capture, dict) and capture.get("approved") is True and capture.get("source_id") == source_id:
            return capture
    return {}


def build_asset_items(
    *,
    capture_plan: dict[str, Any],
    source_manifest: dict[str, Any],
    evidence_manifest: dict[str, Any],
    rights_manifest: dict[str, Any],
    youtube_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    if capture_plan.get("operator_approved_for_acquisition") is not True:
        raise AcquisitionError("operator approval is required before real-smoke acquisition")

    captures = [item for item in capture_plan.get("captures") or [] if isinstance(item, dict)]
    sources = index_sources(source_manifest)
    rights_by_evidence = index_rights(rights_manifest)
    videos = youtube_metadata(youtube_manifest)
    items: list[dict[str, Any]] = []

    for evidence in evidence_manifest.get("evidence") or []:
        if not isinstance(evidence, dict):
            continue
        source_id = str(evidence.get("source_id") or "")
        if not source_id:
            continue
        capture = find_capture_for_evidence(evidence, captures)
        source = sources.get(source_id, {})
        url = str(capture.get("url") or source.get("url") or "")
        claim_ids = normalize_claim_ids(evidence.get("claim_ids")) or normalize_claim_ids(evidence.get("claim_id"))
        rights_risk = str(
            capture.get("rights_risk")
            or rights_by_evidence.get(str(evidence.get("id") or ""))
            or "unknown"
        )
        details = find_youtube_details(url=url, source_id=source_id, videos=videos)
        items.append(
            {
                "source_id": source_id,
                "url": url,
                "title": str(source.get("title") or details.get("title") or ""),
                "channel": str(source.get("channel") or details.get("channel") or ""),
                "upload_date": details.get("upload_date"),
                "claim_ids": claim_ids,
                "evidence_id": str(evidence.get("id") or ""),
                "capture_id": str(capture.get("id") or ""),
                "capture_type": str(capture.get("capture_type") or evidence.get("asset_type") or "source_card"),
                "purpose": str(evidence.get("purpose") or capture.get("purpose") or source.get("relevance") or ""),
                "rights_risk": rights_risk,
            }
        )

    if items:
        return sorted(items, key=lambda item: (item["source_id"], item["evidence_id"], item["capture_id"]))

    for capture in captures:
        if capture.get("approved") is not True:
            continue
        source_id = str(capture.get("source_id") or "")
        source = sources.get(source_id, {})
        url = str(capture.get("url") or source.get("url") or "")
        details = find_youtube_details(url=url, source_id=source_id, videos=videos)
        items.append(
            {
                "source_id": source_id,
                "url": url,
                "title": str(source.get("title") or details.get("title") or ""),
                "channel": str(source.get("channel") or details.get("channel") or ""),
                "upload_date": details.get("upload_date"),
                "claim_ids": normalize_claim_ids(capture.get("claim_ids")),
                "evidence_id": "",
                "capture_id": str(capture.get("id") or ""),
                "capture_type": str(capture.get("capture_type") or "source_card"),
                "purpose": str(capture.get("purpose") or source.get("relevance") or ""),
                "rights_risk": str(capture.get("rights_risk") or "unknown"),
            }
        )
    return sorted(items, key=lambda item: (item["source_id"], item["capture_id"]))


def render_text_card(item: dict[str, Any], captured_at: str) -> str:
    lines = [
        "Asymmetric source card",
        f"Source ID: {item['source_id']}",
        f"URL: {item['url']}",
    ]
    if item.get("title"):
        lines.append(f"Title: {item['title']}")
    if item.get("channel"):
        lines.append(f"Channel: {item['channel']}")
    if item.get("upload_date"):
        lines.append(f"Upload date: {item['upload_date']}")
    if item.get("evidence_id"):
        lines.append(f"Evidence ID: {item['evidence_id']}")
    if item.get("claim_ids"):
        lines.append(f"Claim IDs: {', '.join(item['claim_ids'])}")
    lines.extend(
        [
            f"Capture type: {item['capture_type']}",
            f"Rights risk: {item['rights_risk']}",
            f"Captured at: {captured_at}",
        ]
    )
    if item.get("purpose"):
        lines.append("")
        lines.append(item["purpose"])
    return "\n".join(lines) + "\n"


def render_html_card(item: dict[str, Any], captured_at: str) -> str:
    rows = [
        ("Source ID", item["source_id"]),
        ("URL", item["url"]),
        ("Title", item.get("title")),
        ("Channel", item.get("channel")),
        ("Upload date", item.get("upload_date")),
        ("Evidence ID", item.get("evidence_id")),
        ("Claim IDs", ", ".join(item["claim_ids"])),
        ("Capture type", item["capture_type"]),
        ("Rights risk", item["rights_risk"]),
        ("Captured at", captured_at),
    ]
    body = "\n".join(
        f"      <tr><th>{html.escape(label)}</th><td>{html.escape(str(value))}</td></tr>"
        for label, value in rows
        if value
    )
    purpose = html.escape(item.get("purpose") or "")
    title = html.escape(item.get("title") or item["source_id"])
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #111; }}
      main {{ max-width: 760px; }}
      h1 {{ font-size: 1.5rem; margin-bottom: 1rem; }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #bbb; padding: 0.5rem; text-align: left; vertical-align: top; }}
      th {{ width: 9rem; background: #f2f2f2; }}
      p {{ line-height: 1.45; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Asymmetric source card</h1>
      <table>
{body}
      </table>
      <p>{purpose}</p>
    </main>
  </body>
</html>
"""


def write_ppm_card(path: Path, item: dict[str, Any]) -> None:
    seed = sum(ord(char) for char in item["source_id"] + item.get("evidence_id", ""))
    rgb = (
        40 + seed % 120,
        45 + (seed // 3) % 120,
        60 + (seed // 7) % 120,
    )
    width, height = 1280, 720
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    row = bytes(rgb) * width
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(header)
        for _ in range(height):
            handle.write(row)


def write_source_cards(
    *,
    run_dir: Path,
    asset_format: str = "html",
    captured_at: str | None = None,
) -> dict[str, Any]:
    if asset_format not in SUPPORTED_FORMATS:
        raise AcquisitionError(f"unsupported asset format: {asset_format}")

    artifact_dir = run_dir / "artifacts"
    assets_dir = run_dir / "assets"
    captured_at = captured_at or utc_timestamp()

    items = build_asset_items(
        capture_plan=load_json(artifact_dir / "source_capture_plan.json"),
        source_manifest=load_json(artifact_dir / "source_candidate_manifest.json"),
        evidence_manifest=read_optional_artifact(artifact_dir, "evidence_candidate_manifest.json"),
        rights_manifest=read_optional_artifact(artifact_dir, "rights_risk_manifest.json"),
        youtube_manifest=read_optional_artifact(artifact_dir, "youtube_source_manifest.json"),
    )

    assets: list[dict[str, Any]] = []
    proof_assets: list[SourceProofAsset] = []
    for item in items:
        stem_parts = [item["source_id"]]
        if item.get("evidence_id"):
            stem_parts.append(item["evidence_id"])
        elif item.get("capture_id"):
            stem_parts.append(item["capture_id"])
        stem = safe_slug("__".join(stem_parts))
        asset_path = assets_dir / f"{stem}.{asset_format}"
        sidecar_path = assets_dir / f"{stem}.json"
        image_stems = []
        if item.get("evidence_id"):
            image_stems.append(f"source_card_{safe_slug(item['evidence_id'])}")
        if item.get("capture_id"):
            image_stems.append(f"source_card_{safe_slug(item['capture_id'])}")
        image_stems.append(stem)
        assets_dir.mkdir(parents=True, exist_ok=True)
        if asset_format == "html":
            asset_path.write_text(render_html_card(item, captured_at), encoding="utf-8")
        else:
            asset_path.write_text(render_text_card(item, captured_at), encoding="utf-8")
        image_paths = []
        for image_stem in dict.fromkeys(image_stems):
            image_path = assets_dir / f"{image_stem}.ppm"
            write_ppm_card(image_path, item)
            image_paths.append(str(image_path))

        sidecar = {
            "asset_path": str(asset_path),
            "image_paths": image_paths,
            "asset_type": f"source_card_{asset_format}",
            "capture_timestamp": captured_at,
            "claim_ids": item["claim_ids"],
            "evidence_id": item.get("evidence_id") or None,
            "rights_risk": item["rights_risk"],
            "source_id": item["source_id"],
            "url": item["url"],
        }
        if item.get("title"):
            sidecar["title"] = item["title"]
        if item.get("channel"):
            sidecar["channel"] = item["channel"]
        write_json(sidecar_path, sidecar)
        asset_record = {
            "asset": str(asset_path),
            "asset_path": str(asset_path),
            "capture_id": item.get("capture_id") or None,
            "claim_ids": item["claim_ids"],
            "evidence_id": item.get("evidence_id") or None,
            "id": item.get("evidence_id") or item.get("capture_id") or item["source_id"],
            "images": image_paths,
            "image_paths": image_paths,
            "sidecar": str(sidecar_path),
            "sidecar_path": str(sidecar_path),
            "source_id": item["source_id"],
        }
        assets.append(asset_record)
        proof_assets.append(
            SourceProofAsset(
                id=str(asset_record["id"]),
                source_id=item["source_id"],
                asset_path=asset_path,
                image_paths=tuple(Path(path) for path in image_paths),
                sidecar_path=sidecar_path,
                evidence_id=item.get("evidence_id") or None,
                capture_id=item.get("capture_id") or None,
                claim_ids=tuple(item["claim_ids"]),
            )
        )

    proof_manifest = SourceProofManifest(
        assets=tuple(proof_assets),
        asset_format=asset_format,
        capture_timestamp=captured_at,
    )
    proof_manifest.write(assets_dir)
    manifest = proof_manifest.payload()
    write_json(assets_dir / "source_card_manifest.json", manifest)
    return manifest


def resolve_run_dir(args: argparse.Namespace) -> Path:
    if args.run_dir:
        return args.run_dir
    if not args.episode_id:
        raise AcquisitionError("provide --run-dir or --episode-id")
    return args.run_base_dir / args.episode_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create real-smoke source card assets from local artifacts")
    parser.add_argument("--run-base-dir", type=Path, default=DEFAULT_RUN_BASE_DIR)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--episode-id")
    parser.add_argument("--format", choices=sorted(SUPPORTED_FORMATS), default="html")
    parser.add_argument("--captured-at", help="UTC ISO timestamp override for deterministic tests/replays")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = write_source_cards(
            run_dir=resolve_run_dir(args),
            asset_format=args.format,
            captured_at=args.captured_at,
        )
    except AcquisitionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
