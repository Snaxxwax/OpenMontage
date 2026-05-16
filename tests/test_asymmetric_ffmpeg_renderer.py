from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from scripts.asymmetric_ffmpeg_renderer import (
    RenderError,
    build_render_segments,
    load_staged_manifest,
    resolve_staged_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


# ── shared helpers ────────────────────────────────────────────────────────────

def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_ppm(path: Path, rgb: tuple[int, int, int]) -> None:
    width, height = 320, 180
    row = bytes(rgb) * width
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        for _ in range(height):
            handle.write(row)


def png_bytes(width: int = 10, height: int = 8) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype: bytes, data: bytes) -> bytes:
        crc_payload = ctype + data
        return (
            struct.pack(">I", len(data))
            + ctype
            + data
            + struct.pack(">I", zlib.crc32(crc_payload) & 0xFFFFFFFF)
        )

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    row = b"\x00" + b"\xFF\xFF\xFF" * width
    idat = chunk(b"IDAT", zlib.compress(row * height))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def visual_rhythm(*, include_label: bool = True) -> dict:
    proof = {
        "id": "seg-proof",
        "purpose": "Proof hit",
        "visual_mode": "source_clip",
        "starts_at_seconds": 0,
        "event_type": "proof",
        "approved": True,
        "source_label_present": include_label,
        "evidence_ids": ["ev-proof"],
    }
    if include_label:
        proof["source_label"] = "Fixture Research Lab, 2026"
    return {
        "episode": "fixture_render",
        "operator_approved_for_render": True,
        "segments": [
            proof,
            {
                "id": "seg-source",
                "purpose": "Source context",
                "visual_mode": "source_clip",
                "starts_at_seconds": 1.25,
                "event_type": "source",
                "approved": True,
                "source_label_present": True,
                "source_label": "Vendor permissions doc, 2026",
                "evidence_ids": ["ev-source"],
            },
        ],
    }


def _staged_manifest(
    staging_root: Path,
    assets: list[dict],
    *,
    gate_passed: bool = True,
    render_id: str = "ep001-r001",
) -> Path:
    """Write staged files and manifest. Returns manifest_path."""
    staged_assets = []
    for asset in assets:
        content = asset.pop("_content", b"fake-content")
        staged_path = asset["staged_path"]
        dest = staging_root / staged_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        asset = {**asset, "sha256": hashlib.sha256(content).hexdigest()}
        staged_assets.append(asset)

    manifest = {
        "render_id": render_id,
        "episode_id": "ep001",
        "staged_at": "2026-05-15T12:00:00Z",
        "gate_passed": gate_passed,
        "assets": staged_assets,
    }
    manifest_path = staging_root / "staged_asset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _screenshot_asset(asset_id: str = "sc001", w: int = 10, h: int = 8) -> dict:
    return {
        "asset_id": asset_id,
        "asset_type": "screenshot",
        "role": "proof",
        "source_path": "/prepared/frame.png",
        "staged_path": f"media/{asset_id}.png",
        "source_label_required": False,
        "qc_status": "pass",
        "dimensions": {"width": w, "height": h},
        "_content": png_bytes(w, h),
    }


# ── legacy renderer tests ─────────────────────────────────────────────────────

class AsymmetricFFmpegRendererTests(unittest.TestCase):
    def test_missing_source_label_fails_before_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            assets = Path(temp_dir) / "assets"
            write_ppm(assets / "seg-proof.ppm", (180, 20, 40))
            write_ppm(assets / "seg-source.ppm", (20, 80, 160))

            with self.assertRaisesRegex(RenderError, "source_label_present=true and source_label"):
                build_render_segments(visual_rhythm(include_label=False), assets)

    def test_cli_renders_labeled_smoke_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_base = Path(temp_dir)
            run_dir = run_base / "fixture_render"
            write_json(run_dir / "artifacts/visual_rhythm_plan.json", visual_rhythm())
            proof_image = run_dir / "assets/proof-image.ppm"
            source_image = run_dir / "assets/source-image.ppm"
            write_ppm(proof_image, (180, 20, 40))
            write_ppm(source_image, (20, 80, 160))
            write_json(
                run_dir / "assets/source_proof_manifest.json",
                {
                    "asset_format": "html",
                    "capture_timestamp": "2026-05-13T12:00:00Z",
                    "assets": [
                        {
                            "id": "ev-proof",
                            "source_id": "src-proof",
                            "asset_path": str(run_dir / "assets/proof.html"),
                            "image_paths": [str(proof_image)],
                            "sidecar_path": str(run_dir / "assets/proof.json"),
                            "evidence_id": "ev-proof",
                            "claim_ids": ["claim-1"],
                        },
                        {
                            "id": "ev-source",
                            "source_id": "src-source",
                            "asset_path": str(run_dir / "assets/source.html"),
                            "image_paths": [str(source_image)],
                            "sidecar_path": str(run_dir / "assets/source.json"),
                            "evidence_id": "ev-source",
                            "claim_ids": ["claim-2"],
                        },
                    ],
                },
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/asymmetric_ffmpeg_renderer.py",
                    "--legacy-no-staging",           # required now for legacy path
                    "--run-base-dir",
                    str(run_base),
                    "--episode-id",
                    "fixture_render",
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            render = Path(payload["render"])
            self.assertTrue(render.exists())
            self.assertGreater(render.stat().st_size, 1000)
            self.assertEqual([item["id"] for item in payload["segments"]], ["seg-proof", "seg-source"])
            self.assertEqual(Path(payload["segments"][0]["asset"]), proof_image)
            self.assertEqual(Path(payload["segments"][1]["asset"]), source_image)
            self.assertTrue((run_dir / "qc/ffmpeg_source_proof_smoke.log").exists())


# ── staged renderer tests ─────────────────────────────────────────────────────

class StagedRendererTests(unittest.TestCase):

    def test_staged_refuses_gate_passed_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(
                staging_root,
                [_screenshot_asset()],
                gate_passed=False,
            )
            with self.assertRaisesRegex(RenderError, "gate_passed"):
                load_staged_manifest(manifest_path)

    def test_staged_resolves_paths_relative_to_manifest_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(
                staging_root,
                [_screenshot_asset("sc001")],
                gate_passed=True,
            )
            manifest = load_staged_manifest(manifest_path)
            resolved = resolve_staged_paths(manifest, staging_root)

            self.assertEqual(len(resolved), 1)
            expected = (staging_root / "media/sc001.png").resolve()
            self.assertEqual(resolved[0]["_resolved_path"], expected)

    def test_staged_fails_if_staged_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(
                staging_root,
                [_screenshot_asset("sc001")],
                gate_passed=True,
            )
            # Delete the staged file after manifest is written
            (staging_root / "media" / "sc001.png").unlink()

            manifest = load_staged_manifest(manifest_path)
            with self.assertRaisesRegex(RenderError, "not found"):
                resolve_staged_paths(manifest, staging_root)

    def test_staged_does_not_use_legacy_asset_resolution(self) -> None:
        """resolve_staged_paths reads staged_path directly; never calls resolve_asset/asset_candidates."""
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(
                staging_root,
                [_screenshot_asset("sc001")],
                gate_passed=True,
            )
            # No assets/ directory — if legacy resolution was called it would fail
            assets_dir = staging_root / "assets"
            self.assertFalse(assets_dir.exists())

            manifest = load_staged_manifest(manifest_path)
            # resolve_staged_paths must succeed without any assets/ directory
            resolved = resolve_staged_paths(manifest, staging_root)

            self.assertEqual(len(resolved), 1)
            # Resolved path must be inside staging_root/media/, not assets/
            rp = resolved[0]["_resolved_path"]
            self.assertIn("media", str(rp))
            self.assertNotIn("assets", str(rp))

    def test_legacy_path_works_with_legacy_flag(self) -> None:
        """--legacy-no-staging still routes to the legacy render_episode path."""
        with tempfile.TemporaryDirectory() as tmp:
            run_base = Path(tmp)
            run_dir = run_base / "fixture_render"
            write_json(run_dir / "artifacts/visual_rhythm_plan.json", visual_rhythm())
            proof_image = run_dir / "assets/proof-image.ppm"
            source_image = run_dir / "assets/source-image.ppm"
            write_ppm(proof_image, (180, 20, 40))
            write_ppm(source_image, (20, 80, 160))
            write_json(
                run_dir / "assets/source_proof_manifest.json",
                {
                    "asset_format": "html",
                    "capture_timestamp": "2026-05-13T12:00:00Z",
                    "assets": [
                        {
                            "id": "ev-proof",
                            "source_id": "src-proof",
                            "asset_path": str(run_dir / "assets/proof.html"),
                            "image_paths": [str(proof_image)],
                            "sidecar_path": str(run_dir / "assets/proof.json"),
                            "evidence_id": "ev-proof",
                            "claim_ids": ["claim-1"],
                        },
                        {
                            "id": "ev-source",
                            "source_id": "src-source",
                            "asset_path": str(run_dir / "assets/source.html"),
                            "image_paths": [str(source_image)],
                            "sidecar_path": str(run_dir / "assets/source.json"),
                            "evidence_id": "ev-source",
                            "claim_ids": ["claim-2"],
                        },
                    ],
                },
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/asymmetric_ffmpeg_renderer.py",
                    "--legacy-no-staging",
                    "--run-base-dir", str(run_base),
                    "--episode-id", "fixture_render",
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(Path(payload["render"]).exists())

    def test_missing_staged_manifest_raises_render_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ghost_path = Path(tmp) / "staging" / "ep001-r001" / "staged_asset_manifest.json"
            with self.assertRaisesRegex(RenderError, "missing JSON file"):
                load_staged_manifest(ghost_path)

    def test_invalid_json_in_staged_manifest_raises_render_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "staged_asset_manifest.json"
            manifest_path.write_text("not json {{{", encoding="utf-8")
            with self.assertRaisesRegex(RenderError, "invalid JSON"):
                load_staged_manifest(manifest_path)

    def test_staged_crf_flag_overrides_default(self) -> None:
        """--crf 18 is passed through to the FFmpeg command."""
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(staging_root, [_screenshot_asset()])
            output_path = staging_root / "out_crf18.mp4"

            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/asymmetric_ffmpeg_renderer.py",
                    "--staging-manifest", str(manifest_path),
                    "--output", str(output_path),
                    "--crf", "18",
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            log = (staging_root / "logs" / "ffmpeg_staged_render.log").read_text()
            self.assertIn("-crf 18", log)

    def test_staged_default_crf_is_28(self) -> None:
        """Without --crf, the FFmpeg command uses the default -crf 28."""
        with tempfile.TemporaryDirectory() as tmp:
            staging_root = Path(tmp)
            manifest_path = _staged_manifest(staging_root, [_screenshot_asset()])
            output_path = staging_root / "out_default.mp4"

            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/asymmetric_ffmpeg_renderer.py",
                    "--staging-manifest", str(manifest_path),
                    "--output", str(output_path),
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            log = (staging_root / "logs" / "ffmpeg_staged_render.log").read_text()
            self.assertIn("-crf 28", log)

    def test_no_mode_specified_returns_error(self) -> None:
        """Calling without --staging-manifest or --legacy-no-staging exits nonzero."""
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/asymmetric_ffmpeg_renderer.py",
                "--episode-id", "ep001",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("No render mode specified", payload["error"])


if __name__ == "__main__":
    unittest.main()
