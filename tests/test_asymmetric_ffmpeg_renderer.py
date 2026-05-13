from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.asymmetric_ffmpeg_renderer import RenderError, build_render_segments


REPO_ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
