from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

_SAFE_COMPONENT = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_slug(value: str) -> str:
    slug = _SAFE_COMPONENT.sub("-", value.strip()).strip(".-_").lower()
    return slug or "asset"


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "image"
    if suffix in {".mp4", ".mov", ".webm", ".mkv"}:
        return "video"
    if suffix in {".wav", ".mp3", ".m4a", ".flac"}:
        return "audio"
    if suffix == ".json":
        return "json"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix == ".svg":
        return "svg"
    return "other"


def _relative_project_path(project_dir: Path, path: Path) -> str:
    return path.relative_to(project_dir).as_posix()


def stage_content_collection_assets(content_collection: dict[str, Any], project_dir: str | Path) -> dict[str, Any]:
    """Copy declared local content_collection inputs into deterministic project asset paths.

    This is a narrow deterministic utility: it does not choose opportunities, download URLs,
    render HyperFrames segments, or decide creative fallback behavior. Director skills decide
    what belongs in content_collection; this function only materializes local_path files.
    """

    project_root = Path(project_dir)
    staged_assets: list[dict[str, Any]] = []
    staged_metadata: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for opportunity in sorted(content_collection.get("opportunities", []), key=lambda item: item.get("id", "")):
        opportunity_id = str(opportunity.get("id", "")).strip()
        local_path = opportunity.get("local_path")
        if not opportunity_id or not local_path:
            if opportunity_id:
                skipped.append({"id": opportunity_id, "reason": "no local_path"})
            continue

        source = Path(str(local_path)).expanduser()
        if not source.is_absolute():
            source = (project_root / source).resolve()
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"content_collection opportunity {opportunity_id} local_path not found: {source}")

        digest = _hash_file(source)
        safe_name = _safe_slug(source.stem) + source.suffix.lower()
        dest_dir = project_root / "assets" / "content_collection" / _safe_slug(opportunity_id)
        dest = dest_dir / f"{digest[:8]}-{safe_name}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or _hash_file(dest) != digest:
            shutil.copy2(source, dest)

        staged_assets.append(
            {
                "id": f"content_{opportunity_id}",
                "type": _asset_type(dest),
                "path": _relative_project_path(project_root, dest),
                "source_tool": "content_asset_staging",
                "scene_id": opportunity_id,
                "subtype": str(opportunity.get("kind", "content_collection")),
                "generation_summary": f"Deterministically staged from content_collection opportunity {opportunity_id}",
                "license": str(opportunity.get("rights_status", "unknown")),
                "original_url": str(opportunity.get("source_url", "")),
            }
        )
        staged_metadata.append(
            {
                "asset_id": f"content_{opportunity_id}",
                "sha256": digest,
                "content_opportunity_refs": [opportunity_id],
                "runtime_affinity": opportunity.get("runtime_affinity"),
                "evidence_refs": opportunity.get("evidence_refs", []),
            }
        )

    return {
        "version": "1.0",
        "assets": staged_assets,
        "total_cost_usd": 0,
        "metadata": {
            "content_collection_staging": {
                "episode_id": content_collection.get("episode_id"),
                "staged_count": len(staged_assets),
                "staged_assets": staged_metadata,
                "skipped": skipped,
            }
        },
    }


def _available_opportunity_ids(content_collection: dict[str, Any]) -> list[str]:
    return sorted(str(item["id"]) for item in content_collection.get("opportunities", []) if item.get("id"))


def _iter_refs(value: Any, prefix: str):
    if isinstance(value, dict):
        refs = value.get("content_opportunity_refs")
        if isinstance(refs, list):
            for index, ref in enumerate(refs):
                yield f"{prefix}.content_opportunity_refs[{index}]", str(ref)
        for key, child in value.items():
            if key == "content_opportunity_refs":
                continue
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_refs(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_refs(child, f"{prefix}[{index}]")


def validate_content_opportunity_refs(
    content_collection: dict[str, Any],
    episode: dict[str, Any] | None = None,
    media_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate that episode/media references point at content_collection opportunities."""

    available = set(_available_opportunity_ids(content_collection))
    unresolved: list[dict[str, str]] = []
    for artifact_name, artifact in (("episode", episode), ("media_manifest", media_manifest)):
        if artifact is None:
            continue
        for path, ref in _iter_refs(artifact, ""):
            if ref not in available:
                unresolved.append({"artifact": artifact_name, "path": path, "ref": ref})

    return {
        "valid": not unresolved,
        "available_opportunity_ids": sorted(available),
        "unresolved_refs": unresolved,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Stage Modern Archivist content_collection local assets or validate refs.")
    parser.add_argument("content_collection", type=Path)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--episode", type=Path)
    parser.add_argument("--media-manifest", type=Path)
    parser.add_argument("--validate-refs", action="store_true")
    args = parser.parse_args()

    collection = json.loads(args.content_collection.read_text(encoding="utf-8"))
    if args.validate_refs:
        episode = json.loads(args.episode.read_text(encoding="utf-8")) if args.episode else None
        media = json.loads(args.media_manifest.read_text(encoding="utf-8")) if args.media_manifest else None
        print(json.dumps(validate_content_opportunity_refs(collection, episode, media), indent=2))
    else:
        if not args.project_dir:
            raise SystemExit("--project-dir is required unless --validate-refs is used")
        print(json.dumps(stage_content_collection_assets(collection, args.project_dir), indent=2))


if __name__ == "__main__":
    main()
