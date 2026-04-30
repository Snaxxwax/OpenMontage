#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path when executed as a script (sys.path[0] is tools/scripts).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.analysis.audio_probe import probe_duration  # noqa: E402
from tools.audio.tts_selector import TTSSelector  # noqa: E402


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _bool_arg(value: str) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean: {value!r}")


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_project_path(repo_root: Path, project_arg: str) -> Path:
    p = Path(project_arg)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    return p


def _health_check(base_url: str, *, timeout_s: float = 5.0, attempts: int = 2) -> tuple[bool, str]:
    import requests

    base = base_url.rstrip("/")
    last_error = ""
    for i in range(attempts):
        try:
            r = requests.get(f"{base}/v1/health", timeout=timeout_s)
            if r.ok:
                return True, r.text.strip()
            last_error = f"HTTP {r.status_code}: {r.text[:200]!r}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        if i < attempts - 1:
            time.sleep(0.25)
    return False, last_error or "unknown"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _is_section_audio_acceptable(
    *,
    audio_path: Path,
    expected_seconds: float,
    min_ratio: float = 0.85,
    max_ratio: float = 1.30,
) -> tuple[bool, float | None, str | None]:
    dur = probe_duration(audio_path)
    if dur is None:
        return False, None, "duration_probe_failed"
    if dur <= 0:
        return False, dur, "non_positive_duration"
    if expected_seconds <= 0:
        return True, dur, None
    ratio = dur / expected_seconds
    if ratio < min_ratio:
        return False, dur, f"too_short_ratio_{ratio:.3f}"
    if ratio > max_ratio:
        return False, dur, f"too_long_ratio_{ratio:.3f}"
    if 47.0 <= dur <= 49.5 and expected_seconds >= 55.0:
        return False, dur, "duration_cluster_48s"
    return True, dur, None


def _archive_existing_pilot_audio(*, narration_dir: Path, archive_dir: Path) -> list[dict[str, str]]:
    moved: list[dict[str, str]] = []
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    _ensure_dir(archive_dir)

    for p in sorted(narration_dir.glob("s*.mp3")):
        # Preserve deterministic names in archive by suffixing with timestamp to avoid clobber.
        dest = archive_dir / f"{p.stem}_{ts}{p.suffix}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        p.replace(dest)
        moved.append({"from": str(p), "to": str(dest)})
    return moved


@dataclass(frozen=True)
class Section:
    section_id: str
    start_seconds: float
    end_seconds: float
    text: str

    @property
    def expected_seconds(self) -> float:
        return float(self.end_seconds) - float(self.start_seconds)


def _load_sections(script: dict[str, Any]) -> list[Section]:
    out: list[Section] = []
    for sec in script.get("sections", []):
        out.append(
            Section(
                section_id=str(sec["id"]),
                start_seconds=float(sec.get("start_seconds") or 0.0),
                end_seconds=float(sec.get("end_seconds") or 0.0),
                text=str(sec.get("text") or ""),
            )
        )
    return out


def _first_scene_per_section(scene_plan: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for sc in scene_plan.get("scenes", []):
        sid = sc.get("script_section_id")
        if sid and sid not in mapping:
            mapping[str(sid)] = str(sc.get("id") or "")
    return mapping


def _manifest_upsert_asset(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    assets = manifest.setdefault("assets", [])
    for i, a in enumerate(assets):
        if a.get("id") == entry.get("id"):
            assets[i] = entry
            return
    assets.append(entry)


def _manifest_get_provider_block(manifest: dict[str, Any], *, provider: str) -> dict[str, Any] | None:
    for pb in manifest.get("provider_blocks", []) or []:
        if pb.get("provider") == provider:
            return pb
    return None


def _manifest_start_provider_block(manifest: dict[str, Any], *, provider: str, tool_name: str, runtime: str) -> dict[str, Any]:
    manifest.setdefault("provider_blocks", [])
    existing = _manifest_get_provider_block(manifest, provider=provider)
    if existing:
        return existing
    pb = {
        "block_id": f"pb-tts-v2-{int(time.time())}",
        "provider": provider,
        "tool_name": tool_name,
        "runtime": runtime,
        "status": "success",
        "start_time": _utc_now_iso(),
        "end_time": None,
        "lock_acquired": True,
        "artifacts_produced": [],
        "notes": "Fish Speech narration generation via tts_selector (chunked 25–40s).",
    }
    manifest["provider_blocks"].append(pb)
    return pb


def _manifest_fail_provider_block(
    manifest: dict[str, Any],
    *,
    provider: str,
    failure_reason: str,
) -> None:
    pb = _manifest_get_provider_block(manifest, provider=provider)
    if not pb:
        pb = _manifest_start_provider_block(manifest, provider=provider, tool_name="tts_selector", runtime="local_gpu")
    pb["status"] = "failed"
    pb["failure_reason"] = failure_reason
    pb["end_time"] = _utc_now_iso()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate chunked Fish Speech narration via tts_selector.")
    parser.add_argument("--project", required=True, help="Project directory under repo, e.g. projects/xyz")
    parser.add_argument("--fish-speech-base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--allow-paid-providers", type=_bool_arg, default=False)
    parser.add_argument("--resume", action="store_true", help="Resume by reusing already-acceptable section audio.")
    parser.add_argument("--force", action="store_true", help="Force regeneration (archives existing narration and clears receipts).")
    args = parser.parse_args()

    if args.allow_paid_providers:
        print("Refusing: allow_paid_providers must be false for this pipeline.", file=sys.stderr)
        return 2

    repo_root = _resolve_repo_root()
    project_dir = _resolve_project_path(repo_root, args.project)
    if not project_dir.is_dir():
        print(f"Project not found: {project_dir}", file=sys.stderr)
        return 2

    artifacts_dir = project_dir / "artifacts"
    script_path = artifacts_dir / "script.json"
    scene_plan_path = artifacts_dir / "scene_plan.json"
    manifest_path = artifacts_dir / "asset_manifest.json"
    log_path = artifacts_dir / "tts_generation_v2_log.json"

    for required in (script_path, scene_plan_path, manifest_path):
        if not required.is_file():
            print(f"Missing required artifact: {required}", file=sys.stderr)
            return 2

    # Confirm Fish Speech health (2 attempts, 5s each). Do not restart here.
    healthy, health_payload = _health_check(args.fish_speech_base_url, timeout_s=5.0, attempts=2)
    if not healthy:
        manifest = _read_json(manifest_path)
        _manifest_fail_provider_block(manifest, provider="fish_speech", failure_reason="server_unavailable")
        manifest.setdefault("metadata", {})
        manifest["metadata"].setdefault("generation_status", {})
        manifest["metadata"]["generation_status"]["narration"] = "failed"
        manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
        _write_json(manifest_path, manifest)

        _write_json(
            log_path,
            {
                "run_started_at": _utc_now_iso(),
                "run_status": "server_unavailable",
                "fish_speech_base_url": args.fish_speech_base_url,
                "health_error": health_payload,
                "sections": [],
            },
        )
        print(f"Fish Speech server unavailable after 2 attempts: {health_payload}", file=sys.stderr)
        return 2

    script = _read_json(script_path)
    scene_plan = _read_json(scene_plan_path)
    manifest = _read_json(manifest_path)

    # Resolve asset dirs
    narration_dir = project_dir / "assets" / "audio" / "narration"
    chunks_dir = narration_dir / "_chunks"
    archive_dir = narration_dir / "_archive_short_pilot"
    _ensure_dir(narration_dir)
    _ensure_dir(chunks_dir)
    _ensure_dir(archive_dir)

    sections = _load_sections(script)
    if not sections:
        print("No sections found in script.json", file=sys.stderr)
        return 2

    # Map section -> scene for asset manifest entries.
    section_scene = _first_scene_per_section(scene_plan)

    # Initialize log.
    run_meta: dict[str, Any] = {
        "run_started_at": _utc_now_iso(),
        "run_status": "in_progress",
        "fish_speech_base_url": args.fish_speech_base_url.rstrip("/"),
        "fish_speech_health": health_payload,
        "chunking": {
            "enabled": True,
            "threshold_seconds": 40,
            "target_chunk_seconds_min": 25,
            "target_chunk_seconds_max": 40,
            "words_per_second": 2.8,
        },
        "sections": [],
    }

    # Supersede/clear receipts when forcing.
    if args.force:
        manifest.setdefault("metadata", {})
        meta = manifest["metadata"]
        meta.setdefault("superseded_tts_chunk_receipts", [])
        meta.setdefault("superseded_provider_blocks", [])
        if manifest.get("tts_chunk_receipts"):
            meta["superseded_tts_chunk_receipts"].append(
                {
                    "superseded_at": _utc_now_iso(),
                    "reason": "forced_regeneration",
                    "receipts": manifest.get("tts_chunk_receipts", []),
                }
            )
        if manifest.get("provider_blocks"):
            fish_blocks = [pb for pb in manifest["provider_blocks"] if pb.get("provider") == "fish_speech"]
            if fish_blocks:
                meta["superseded_provider_blocks"].append(
                    {
                        "superseded_at": _utc_now_iso(),
                        "reason": "forced_regeneration",
                        "provider_blocks": fish_blocks,
                    }
                )

        manifest["tts_chunk_receipts"] = []
        # Remove prior chunk assets to avoid duplicates.
        manifest["assets"] = [a for a in (manifest.get("assets") or []) if not str(a.get("id", "")).startswith("nar-chunk-")]
        # Remove prior fish provider blocks; new one will be appended.
        manifest["provider_blocks"] = [pb for pb in (manifest.get("provider_blocks") or []) if pb.get("provider") != "fish_speech"]

        # Archive any existing narration mp3s, including partials.
        run_meta["archived_narration"] = _archive_existing_pilot_audio(
            narration_dir=narration_dir,
            archive_dir=archive_dir,
        )
        # Clear chunks dir to avoid mismatched concat lists.
        for p in sorted(chunks_dir.glob("*")):
            try:
                p.unlink()
            except Exception:
                pass

    # Provider block receipt.
    provider_block = _manifest_start_provider_block(
        manifest,
        provider="fish_speech",
        tool_name="tts_selector",
        runtime="local_gpu",
    )

    manifest.setdefault("metadata", {})
    manifest["metadata"].setdefault("generation_status", {})
    manifest["metadata"]["generation_status"]["narration"] = "in_progress"
    manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
    _write_json(manifest_path, manifest)
    _write_json(log_path, run_meta)

    selector = TTSSelector()
    # Ensure provider selection is constrained to Fish Speech only.
    preferred_provider = "fish_speech"

    run_start = time.time()
    try:
        for sec in sections:
            section_id = sec.section_id
            out_mp3 = (narration_dir / f"{section_id}.mp3").resolve()

            # Resume path: reuse already good audio.
            if args.resume and out_mp3.is_file() and not args.force:
                ok, dur, reason = _is_section_audio_acceptable(
                    audio_path=out_mp3,
                    expected_seconds=sec.expected_seconds,
                )
                if ok:
                    run_meta["sections"].append(
                        {
                            "section_id": section_id,
                            "status": "skipped_resume",
                            "final_output_path": str(out_mp3.relative_to(project_dir)),
                            "final_duration_seconds": round(float(dur or 0.0), 3),
                        }
                    )
                    _write_json(log_path, run_meta)
                    continue

                # Not acceptable: archive and regenerate.
                archive_dest = archive_dir / f"{out_mp3.stem}_resume_rejected_{int(time.time())}{out_mp3.suffix}"
                out_mp3.replace(archive_dest)
                run_meta.setdefault("resume_rejected", []).append(
                    {
                        "section_id": section_id,
                        "path": str(out_mp3),
                        "archived_to": str(archive_dest),
                        "reason": reason,
                        "duration_seconds": dur,
                    }
                )
                _write_json(log_path, run_meta)

            # Generate with chunking enforced.
            t0 = time.time()
            result = selector.execute(
                {
                    "text": sec.text,
                    "output_path": str(out_mp3),
                    "preferred_provider": preferred_provider,
                    "allowed_providers": [preferred_provider],
                    "allow_paid_providers": False,
                    "server_url": args.fish_speech_base_url,
                    "chunk_dir": str(chunks_dir),
                    "chunk_prefix": section_id,
                    "chunking": {
                        "enabled": True,
                        "threshold_seconds": 40,
                        "target_chunk_seconds_min": 25,
                        "target_chunk_seconds_max": 40,
                        "words_per_second": 2.8,
                    },
                }
            )
            wall_s = time.time() - t0

            if not result.success:
                _manifest_fail_provider_block(manifest, provider="fish_speech", failure_reason=str(result.error or "tts_failed"))
                manifest["metadata"]["generation_status"]["narration"] = "failed"
                manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
                _write_json(manifest_path, manifest)

                run_meta["run_status"] = "failed"
                run_meta["failure_section_id"] = section_id
                run_meta["failure_error"] = result.error
                run_meta["failure_data"] = result.data
                _write_json(log_path, run_meta)
                print(f"TTS failed for {section_id}: {result.error}", file=sys.stderr)
                return 1

            data = result.data or {}
            merged_duration = data.get("merged_duration_seconds")
            if merged_duration is None:
                merged_duration = probe_duration(out_mp3)
            merged_duration = float(merged_duration or 0.0)

            # Sanity check against expected ~60s.
            ok, checked_dur, reason = _is_section_audio_acceptable(
                audio_path=out_mp3,
                expected_seconds=sec.expected_seconds,
            )
            if not ok:
                _manifest_fail_provider_block(manifest, provider="fish_speech", failure_reason=f"final_audio_rejected:{reason}")
                manifest["metadata"]["generation_status"]["narration"] = "failed"
                manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
                _write_json(manifest_path, manifest)

                run_meta["run_status"] = "failed"
                run_meta["failure_section_id"] = section_id
                run_meta["failure_error"] = f"final_audio_rejected:{reason}"
                run_meta["failure_duration_seconds"] = checked_dur
                _write_json(log_path, run_meta)
                print(f"Final audio rejected for {section_id}: {reason} (dur={checked_dur})", file=sys.stderr)
                return 1

            chunks = data.get("chunks") or []
            receipt_chunks: list[dict[str, Any]] = []
            total_chunk_wall = 0.0
            for c in chunks:
                idx = int(c.get("index") or 0)
                total_chunk_wall += float(c.get("wall_time_seconds") or 0.0)
                chunk_abs = Path(str(c.get("output_path") or "")).resolve()
                receipt_chunks.append(
                    {
                        "chunk_id": f"{section_id}_c{idx:02d}",
                        "output_path": str(chunk_abs.relative_to(project_dir)),
                        "word_count": int(c.get("word_count") or 0),
                        "estimated_seconds": float(c.get("estimated_seconds") or 0.0),
                        "duration_seconds": float(c.get("duration_seconds") or 0.0),
                        "wall_time_seconds": float(c.get("wall_time_seconds") or 0.0),
                        "realtime_factor": float(c.get("realtime_factor") or 0.0),
                        "suspected_truncation": bool(c.get("suspected_truncation") or False),
                    }
                )

                _manifest_upsert_asset(
                    manifest,
                    {
                        "id": f"nar-chunk-{section_id}-c{idx:02d}",
                        "type": "audio",
                        "path": str(chunk_abs.relative_to(project_dir)),
                        "source_tool": "tts_selector",
                        "scene_id": section_scene.get(section_id) or "",
                        "provider": "fish_speech",
                        "format": "wav",
                        "duration_seconds": float(c.get("duration_seconds") or 0.0),
                        "subtype": "tts_chunk",
                        "generation_summary": "Fish Speech chunk via tts_selector (chunking_enabled=true).",
                        "generation_status": "generated",
                    },
                )

            merged_rt = (total_chunk_wall / merged_duration) if merged_duration > 0 else None

            # Receipt entry (schema-conformant)
            manifest.setdefault("tts_chunk_receipts", [])
            manifest["tts_chunk_receipts"] = [r for r in manifest["tts_chunk_receipts"] if r.get("section_id") != section_id]
            manifest["tts_chunk_receipts"].append(
                {
                    "section_id": section_id,
                    "provider": "fish_speech",
                    "final_output_path": str(out_mp3.relative_to(project_dir)),
                    "final_duration_seconds": round(float(merged_duration), 3),
                    "chunk_count": len(receipt_chunks),
                    "chunks": receipt_chunks,
                }
            )

            _manifest_upsert_asset(
                manifest,
                {
                    "id": f"nar-{section_id}",
                    "type": "narration",
                    "path": str(out_mp3.relative_to(project_dir)),
                    "source_tool": "tts_selector",
                    "scene_id": section_scene.get(section_id) or "",
                    "provider": "fish_speech",
                    "format": "mp3",
                    "duration_seconds": round(float(merged_duration), 3),
                    "generation_summary": (
                        "Fish Speech (local) via tts_selector chunking "
                        f"(chunks={len(receipt_chunks)}, realtime_factor={None if merged_rt is None else round(merged_rt, 3)})."
                    ),
                    "generation_status": "generated",
                }
            )

            provider_block.setdefault("artifacts_produced", []).append(f"nar-{section_id}")
            manifest["assets"] = sorted(manifest.get("assets") or [], key=lambda a: str(a.get("id") or ""))
            manifest["tts_chunk_receipts"] = sorted(
                manifest.get("tts_chunk_receipts") or [],
                key=lambda r: str(r.get("section_id") or ""),
            )
            manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
            _write_json(manifest_path, manifest)

            run_meta["sections"].append(
                {
                    "section_id": section_id,
                    "status": "success",
                    "wall_time_seconds": round(float(wall_s), 3),
                    "final_duration_seconds": round(float(merged_duration), 3),
                    "realtime_factor": None if merged_rt is None else round(float(merged_rt), 3),
                    "chunk_count": len(receipt_chunks),
                    "truncation_flags": data.get("truncation_flags") or [],
                    "final_output_path": str(out_mp3.relative_to(project_dir)),
                }
            )
            _write_json(log_path, run_meta)

            rtf_str = "n/a" if merged_rt is None else f"{merged_rt:.3f}"
            print(f"OK {section_id}: {merged_duration:.2f}s chunks={len(receipt_chunks)} wall={wall_s:.1f}s rtf={rtf_str}", flush=True)

    finally:
        # Always finalize provider block times if it exists.
        pb = _manifest_get_provider_block(manifest, provider="fish_speech")
        if pb and pb.get("end_time") is None:
            pb["end_time"] = _utc_now_iso()
        _write_json(manifest_path, manifest)

    manifest["metadata"]["generation_status"]["narration"] = "complete"
    manifest["metadata"]["generation_status"]["updated_at"] = _utc_now_iso()
    _write_json(manifest_path, manifest)

    run_meta["run_status"] = "complete"
    run_meta["run_wall_time_seconds"] = round(time.time() - run_start, 2)
    _write_json(log_path, run_meta)

    print(f"DONE: generated {len(sections)} sections in {run_meta['run_wall_time_seconds']}s", flush=True)
    print(f"log: {log_path.relative_to(project_dir)}", flush=True)
    print(f"manifest: {manifest_path.relative_to(project_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
