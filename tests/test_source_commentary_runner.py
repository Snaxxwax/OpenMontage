from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_asymmetric_source_commentary import (
    DEFAULT_COMFY_HOST,
    fixture_artifacts,
    preflight,
    resolve_comfy_host,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class SourceCommentaryRunnerTests(unittest.TestCase):
    def test_comfy_host_precedence(self) -> None:
        with patch.dict("os.environ", {"COMFYUI_SERVER_URL": "http://env-host:8188"}):
            self.assertEqual(resolve_comfy_host(None), "http://env-host:8188")
            self.assertEqual(resolve_comfy_host("http://cli-host:8188"), "http://cli-host:8188")
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_comfy_host(None), DEFAULT_COMFY_HOST)

    def test_preflight_without_comfy_passes_local_checks(self) -> None:
        result = preflight(comfy_host=DEFAULT_COMFY_HOST, check_comfy=False)

        self.assertTrue(result["ok"], result)

    def test_fixture_without_approval_fails_render_gate(self) -> None:
        artifacts = fixture_artifacts("fixture_pending", "Fixture topic", approved=False)

        self.assertFalse(artifacts["source_capture_plan.json"]["operator_approved_for_acquisition"])
        self.assertFalse(artifacts["visual_rhythm_plan.json"]["operator_approved_for_render"])
        self.assertFalse(artifacts["source_segment_approval_manifest.json"]["segments"][0]["approved"])

    def test_full_fixture_run_cli_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_asymmetric_source_commentary.py",
                    "--run-base-dir",
                    temp_dir,
                    "run",
                    "--mode",
                    "fixture",
                    "--episode-id",
                    "fixture_001",
                    "--topic",
                    "AI browser agent trust boundary failure",
                    "--auto-approve-fixture",
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "success")
            run_dir = Path(payload["run_dir"])
            self.assertTrue((run_dir / "artifacts/qc_report.json").exists())
            self.assertTrue((run_dir / "qc/qc_gate.json").exists())
            self.assertTrue(Path(payload["render"]).exists())

            validate_proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_asymmetric_source_commentary.py",
                    "--run-base-dir",
                    temp_dir,
                    "validate",
                    "--episode-id",
                    "fixture_001",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(validate_proc.returncode, 0, validate_proc.stdout + validate_proc.stderr)

    def test_full_real_smoke_run_cli_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_asymmetric_source_commentary.py",
                    "--run-base-dir",
                    temp_dir,
                    "run",
                    "--mode",
                    "real-smoke",
                    "--episode-id",
                    "real_smoke_001",
                    "--topic",
                    "AI browser agent trust boundary failure",
                    "--auto-approve-fixture",
                    "--overwrite",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "success")
            run_dir = Path(payload["run_dir"])
            self.assertTrue((run_dir / "assets/source_card_ev-proof-demo.ppm").exists())
            self.assertTrue((run_dir / "qc/ffmpeg_source_proof_smoke.log").exists())
            self.assertTrue((run_dir / "artifacts/qc_report.json").exists())
            self.assertTrue(Path(payload["render"]).exists())


if __name__ == "__main__":
    unittest.main()
