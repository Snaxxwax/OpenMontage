from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.asymmetric_real_smoke_acquisition import AcquisitionError, write_source_cards
from lib.source_proof import SourceProofManifest


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class RealSmokeAcquisitionTests(unittest.TestCase):
    def test_writes_source_card_assets_and_sidecars_from_local_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "episode_001"
            artifacts = run_dir / "artifacts"
            write_json(
                artifacts / "source_capture_plan.json",
                {
                    "episode": "episode_001",
                    "operator_approved_for_acquisition": True,
                    "captures": [
                        {
                            "id": "cap-doc",
                            "source_id": "src-doc",
                            "claim_ids": ["claim-1"],
                            "capture_type": "web_screenshot",
                            "url": "https://example.com/doc",
                            "purpose": "Show the documented boundary.",
                            "rights_risk": "low",
                            "approved": True,
                        }
                    ],
                },
            )
            write_json(
                artifacts / "source_candidate_manifest.json",
                {
                    "topic": "test",
                    "sources": [
                        {
                            "id": "src-doc",
                            "url": "https://example.com/doc",
                            "kind": "documentation",
                            "relevance": "Primary documentation.",
                            "capture_potential": "screenshot",
                            "credibility_notes": "Fixture.",
                        }
                    ],
                },
            )
            write_json(
                artifacts / "evidence_candidate_manifest.json",
                {
                    "episode": "episode_001",
                    "evidence": [
                        {
                            "id": "ev-doc",
                            "claim_id": "claim-1",
                            "asset_type": "web_screenshot",
                            "source_id": "src-doc",
                            "purpose": "Source label context.",
                            "priority": "high",
                        }
                    ],
                },
            )

            manifest = write_source_cards(
                run_dir=run_dir,
                captured_at="2026-05-13T12:00:00Z",
            )

            self.assertEqual(manifest["asset_count"], 1)
            asset_path = run_dir / "assets/src-doc__ev-doc.html"
            sidecar_path = run_dir / "assets/src-doc__ev-doc.json"
            image_path = run_dir / "assets/source_card_ev-doc.ppm"
            proof_manifest_path = run_dir / "assets/source_proof_manifest.json"
            self.assertTrue(asset_path.exists())
            self.assertTrue(sidecar_path.exists())
            self.assertTrue(image_path.exists())
            self.assertTrue(proof_manifest_path.exists())
            self.assertIn("https://example.com/doc", asset_path.read_text(encoding="utf-8"))

            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["source_id"], "src-doc")
            self.assertEqual(sidecar["url"], "https://example.com/doc")
            self.assertEqual(sidecar["capture_timestamp"], "2026-05-13T12:00:00Z")
            self.assertEqual(sidecar["claim_ids"], ["claim-1"])
            self.assertEqual(sidecar["evidence_id"], "ev-doc")
            self.assertEqual(sidecar["rights_risk"], "low")
            self.assertIn(str(image_path), sidecar["image_paths"])

            proof_manifest = SourceProofManifest.load(run_dir / "assets")
            self.assertEqual(len(proof_manifest.assets), 1)
            self.assertEqual(proof_manifest.assets[0].evidence_id, "ev-doc")
            self.assertEqual(proof_manifest.resolve_asset_for_segment({"evidence_ids": ["ev-doc"]}), image_path)

    def test_refuses_without_acquisition_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "episode_001"
            artifacts = run_dir / "artifacts"
            write_json(
                artifacts / "source_capture_plan.json",
                {
                    "episode": "episode_001",
                    "operator_approved_for_acquisition": False,
                    "captures": [],
                },
            )
            write_json(artifacts / "source_candidate_manifest.json", {"topic": "test", "sources": []})

            with self.assertRaises(AcquisitionError):
                write_source_cards(run_dir=run_dir, captured_at="2026-05-13T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
