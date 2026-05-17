from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
FFPROBE = shutil.which("ffprobe")


def _make_png(path: Path, w: int = 752, h: int = 422) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), color=(200, 200, 200)).save(str(path))


def _plan(overrides: dict | None = None) -> dict:
    shot: dict = {
        "shot_id": "SC-02-motion",
        "source_card_id": "SC-02",
        "input_path": "assets/composed/SC-02-card.png",
        "output_path": "assets/motion/SC-02-motion.mp4",
        "duration_seconds": 1.0,
        "motion_type": "push_in",
    }
    if overrides:
        shot.update(overrides)
    return {"version": "1.0", "episode_id": "fixture-test", "shots": [shot]}


def _write_manifest(root: Path, plan: dict) -> Path:
    manifest = root / "artifacts" / "visual_motion_plan.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(plan), encoding="utf-8")
    return manifest


def _run(manifest: Path, qc_out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/asymmetric_motion_cards.py",
         "--manifest", str(manifest),
         "--output", str(qc_out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class MotionCardsTests(unittest.TestCase):

    def test_script_is_importable(self) -> None:
        from scripts.asymmetric_motion_cards import run, MotionError, build_parser
        self.assertTrue(callable(run))
        self.assertTrue(callable(build_parser))

    def test_push_in_produces_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_png(root / "assets" / "composed" / "SC-02-card.png")
            manifest = _write_manifest(root, _plan())
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])

            mp4 = root / "assets" / "motion" / "SC-02-motion.mp4"
            self.assertTrue(mp4.exists())
            self.assertGreater(mp4.stat().st_size, 1000)

    def test_static_produces_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_png(root / "assets" / "composed" / "SC-02-card.png")
            manifest = _write_manifest(root, _plan({"motion_type": "static"}))
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
            self.assertTrue((root / "assets" / "motion" / "SC-02-motion.mp4").exists())

    def test_missing_input_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # PNG deliberately not created
            manifest = _write_manifest(root, _plan())
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertNotEqual(proc.returncode, 0)

    def test_qc_report_written_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # PNG not created — will fail
            manifest = _write_manifest(root, _plan())
            qc_out = root / "qc" / "motion_cards_qc.md"

            _run(manifest, qc_out)
            self.assertTrue(qc_out.exists(), "QC report must be written even on failure")
            content = qc_out.read_text()
            self.assertIn("FAIL", content)

    def test_output_path_outside_assets_motion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_png(root / "assets" / "composed" / "SC-02-card.png")
            manifest = _write_manifest(
                root, _plan({"output_path": "assets/composed/SC-02-motion.mp4"})
            )
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertNotEqual(proc.returncode, 0)

    @unittest.skipUnless(FFPROBE is not None, "ffprobe not available")
    def test_output_duration_roughly_correct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_png(root / "assets" / "composed" / "SC-02-card.png")
            manifest = _write_manifest(root, _plan({"duration_seconds": 2.0}))
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertEqual(proc.returncode, 0, proc.stderr[-500:])

            mp4 = root / "assets" / "motion" / "SC-02-motion.mp4"
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 str(mp4)],
                capture_output=True, text=True,
            )
            duration = float(result.stdout.strip())
            self.assertAlmostEqual(duration, 2.0, delta=0.5)

    @unittest.skipUnless(FFPROBE is not None, "ffprobe not available")
    def test_output_resolution_is_1280x720(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_png(root / "assets" / "composed" / "SC-02-card.png")
            manifest = _write_manifest(root, _plan())
            qc_out = root / "qc" / "motion_cards_qc.md"

            proc = _run(manifest, qc_out)
            self.assertEqual(proc.returncode, 0, proc.stderr[-500:])

            mp4 = root / "assets" / "motion" / "SC-02-motion.mp4"
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "stream=width,height",
                 "-of", "default=noprint_wrappers=1",
                 str(mp4)],
                capture_output=True, text=True,
            )
            self.assertIn("width=1280", result.stdout)
            self.assertIn("height=720", result.stdout)


if __name__ == "__main__":
    unittest.main()
