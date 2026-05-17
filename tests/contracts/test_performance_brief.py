from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "artifacts" / "performance_brief.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid() -> dict:
    return {
        "version": "1.0",
        "episode_id": "test-episode",
        "viewer_promise": "Why one company can remove a site from the internet with no appeal.",
        "opening_claim": "In August 2019, Cloudflare terminated 8chan because its CEO woke up in a bad mood.",
        "stakes": "Infrastructure concentration gives private companies unreviewable governance power over public speech.",
        "title_angle": {
            "title": "The Company That Controls 20% of the Internet",
            "pillar": "Hidden Control",
            "engine": "chokepoint",
        },
        "thumbnail_angle": {
            "family": "Hidden Operator",
            "variant": "power",
            "headline_text": "WHO CONTROLS THIS?",
        },
        "first_15_seconds_plan": [
            {"beat": 1, "seconds": "0-5", "what_happens": "Open with the termination fact."},
            {"beat": 2, "seconds": "5-10", "what_happens": "Show the internal memo quote."},
            {"beat": 3, "seconds": "10-15", "what_happens": "State the chokepoint stakes."},
        ],
        "retention_risks": ["Opening may feel too abstract before the memo quote lands."],
        "boring_parts_to_cut": [],
        "visual_pacing_notes": "Cut or annotate every 3-5 seconds in mechanism sections; no static card holds over 4s.",
    }


def _errors(doc: dict) -> list[str]:
    schema = _schema()
    return [e.message for e in sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: list(e.path))]


class PerformanceBriefSchemaTests(unittest.TestCase):

    def test_valid_performance_brief_passes(self) -> None:
        self.assertEqual(_errors(_valid()), [])

    def test_missing_viewer_promise_fails(self) -> None:
        doc = _valid()
        del doc["viewer_promise"]
        self.assertTrue(len(_errors(doc)) > 0)

    def test_missing_opening_claim_fails(self) -> None:
        doc = _valid()
        del doc["opening_claim"]
        self.assertTrue(len(_errors(doc)) > 0)

    def test_first_15_seconds_plan_needs_three_beats(self) -> None:
        doc = _valid()
        doc["first_15_seconds_plan"] = doc["first_15_seconds_plan"][:2]
        self.assertTrue(len(_errors(doc)) > 0)

    def test_thumbnail_variant_must_be_enum(self) -> None:
        doc = _valid()
        doc["thumbnail_angle"]["variant"] = "viral"
        self.assertTrue(len(_errors(doc)) > 0)

    def test_retention_risks_needs_at_least_one_item(self) -> None:
        doc = _valid()
        doc["retention_risks"] = []
        self.assertTrue(len(_errors(doc)) > 0)

    def test_missing_visual_pacing_notes_fails(self) -> None:
        doc = _valid()
        del doc["visual_pacing_notes"]
        self.assertTrue(len(_errors(doc)) > 0)

    def test_headline_text_over_30_chars_fails(self) -> None:
        doc = _valid()
        doc["thumbnail_angle"]["headline_text"] = "X" * 31
        self.assertTrue(len(_errors(doc)) > 0)


if __name__ == "__main__":
    unittest.main()
