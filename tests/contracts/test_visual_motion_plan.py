from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "artifacts" / "visual_motion_plan.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_shot() -> dict:
    return {
        "shot_id": "SC-02-motion",
        "source_card_id": "SC-02",
        "input_path": "assets/composed/SC-02-card.png",
        "output_path": "assets/motion/SC-02-motion.mp4",
        "duration_seconds": 4.0,
        "motion_type": "push_in",
        "start_scale": 1.0,
        "end_scale": 1.04,
    }


def _valid() -> dict:
    return {
        "version": "1.0",
        "episode_id": "test-episode",
        "shots": [_valid_shot()],
    }


def _errors(doc: dict) -> list[str]:
    schema = _schema()
    return [e.message for e in sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: list(e.path))]


class VisualMotionPlanSchemaTests(unittest.TestCase):

    def test_valid_visual_motion_plan_passes(self) -> None:
        self.assertEqual(_errors(_valid()), [])

    def test_missing_shot_id_fails(self) -> None:
        doc = _valid()
        del doc["shots"][0]["shot_id"]
        self.assertTrue(len(_errors(doc)) > 0)

    def test_invalid_motion_type_fails(self) -> None:
        doc = _valid()
        doc["shots"][0]["motion_type"] = "bounce"
        self.assertTrue(len(_errors(doc)) > 0)

    def test_static_motion_type_allowed(self) -> None:
        doc = _valid()
        doc["shots"][0]["motion_type"] = "static"
        self.assertEqual(_errors(doc), [])

    def test_output_path_outside_assets_motion_fails(self) -> None:
        doc = _valid()
        doc["shots"][0]["output_path"] = "assets/composed/SC-02-motion.mp4"
        self.assertTrue(len(_errors(doc)) > 0)

    def test_output_path_with_dotdot_fails(self) -> None:
        doc = _valid()
        doc["shots"][0]["output_path"] = "assets/motion/../../SC-02-motion.mp4"
        self.assertTrue(len(_errors(doc)) > 0)

    def test_duration_seconds_must_be_positive(self) -> None:
        doc = _valid()
        doc["shots"][0]["duration_seconds"] = 0
        self.assertTrue(len(_errors(doc)) > 0)

    def test_empty_shots_fails(self) -> None:
        doc = _valid()
        doc["shots"] = []
        self.assertTrue(len(_errors(doc)) > 0)


if __name__ == "__main__":
    unittest.main()
