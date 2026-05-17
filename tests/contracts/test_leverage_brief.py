from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "artifacts"
    / "leverage_brief.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid() -> dict:
    return {
        "version": "1.0",
        "episode_id": "ai-datacenter-cost-transfer-p001",
        "public_story": (
            "The AI buildout is a private-sector investment creating jobs and "
            "modernizing the grid."
        ),
        "hidden_mechanism": (
            "Data center operators negotiate incentive agreements and utility "
            "rate structures that transfer construction and grid-upgrade costs "
            "to ratepayers while the operators retain asset ownership and "
            "market power."
        ),
        "control_surface": (
            "Utility rate case filings that allow capital expenditure for "
            "grid upgrades serving data centers to be recovered through "
            "general ratepayer rate increases."
        ),
        "dependency": (
            "Ratepayers and local taxpayers have no alternative: they are "
            "captive to their regulated utility and cannot opt out of rate "
            "increases approved by the public utility commission."
        ),
        "cost_transfer": [
            {
                "from_entity": "Hyperscale data center operator",
                "to_entity": "Utility ratepayers",
                "mechanism": "Grid upgrade costs included in rate base and recovered via regulated rate increase",
                "estimated_magnitude": "$500M–$2B per large facility (varies by state and agreement)",
            }
        ],
        "beneficiaries": [
            {
                "entity": "Hyperscale cloud operators (Microsoft, Google, Amazon, Meta)",
                "capture_mechanism": "Subsidized infrastructure cost, tax incentives, asset ownership with socialized risk",
            }
        ],
        "accountability_gap": (
            "Public utility commissions approve rate cases without requiring "
            "public disclosure of individual data center incentive agreements. "
            "No federal agency aggregates the total public cost exposure."
        ),
        "viewer_takeaway": (
            "When a regulated utility proposes a rate increase, ask whether "
            "the capital investment behind it serves general ratepayers or a "
            "specific large commercial customer whose incentive agreement is "
            "not publicly disclosed."
        ),
        "leverage_takeaway": {
            "what_to_watch_for": [
                "Utility rate increase filings in data-center-dense states",
                "Economic development incentive agreements with energy-intensive tenants",
                "Public utility commission dockets referencing 'large customer load growth'",
            ],
            "questions_to_ask": [
                "Who is the anchor customer for this grid upgrade?",
                "What is the term and structure of the incentive agreement?",
                "How much of this capital expenditure is recoverable from general ratepayers?",
            ],
            "documents_to_find": [
                "State public utility commission rate case filings",
                "Economic development incentive agreements (FOIA if not public)",
                "Utility integrated resource plans showing load growth assumptions",
            ],
            "safe_action_language": (
                "File a public comment in your state utility commission's rate case docket. "
                "Contact your state legislator's office to ask whether existing disclosure "
                "rules require large customer incentive agreements to be made public. "
                "These are lawful, non-partisan, informational actions."
            ),
        },
        "advertiser_safety_posture": {
            "risk_level": "low",
            "language_approved": [
                "cost transfer",
                "ratepayer exposure",
                "public-cost exposure",
                "incentive structure",
                "market power",
                "accountability gap",
            ],
            "language_forbidden": [
                "robbery",
                "scam",
                "criminals",
                "corrupt",
                "sold us out",
            ],
            "claim_source_required": True,
        },
    }


def _errors(doc: dict) -> list[str]:
    schema = _schema()
    return [
        e.message
        for e in sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    ]


class LeverageBriefSchemaTests(unittest.TestCase):

    def test_valid_leverage_brief_passes(self) -> None:
        self.assertEqual(_errors(_valid()), [])

    def test_missing_control_surface_fails(self) -> None:
        doc = _valid()
        del doc["control_surface"]
        self.assertGreater(len(_errors(doc)), 0)

    def test_empty_cost_transfer_fails(self) -> None:
        doc = _valid()
        doc["cost_transfer"] = []
        self.assertGreater(len(_errors(doc)), 0)

    def test_empty_beneficiaries_fails(self) -> None:
        doc = _valid()
        doc["beneficiaries"] = []
        self.assertGreater(len(_errors(doc)), 0)

    def test_missing_leverage_takeaway_fails(self) -> None:
        doc = _valid()
        del doc["leverage_takeaway"]
        self.assertGreater(len(_errors(doc)), 0)

    def test_missing_advertiser_safety_posture_fails(self) -> None:
        doc = _valid()
        del doc["advertiser_safety_posture"]
        self.assertGreater(len(_errors(doc)), 0)

    def test_risk_level_must_be_enum(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["risk_level"] = "critical"
        self.assertGreater(len(_errors(doc)), 0)

    def test_risk_level_low_passes(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["risk_level"] = "low"
        self.assertEqual(_errors(doc), [])

    def test_risk_level_medium_passes(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["risk_level"] = "medium"
        self.assertEqual(_errors(doc), [])

    def test_risk_level_high_passes(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["risk_level"] = "high"
        self.assertEqual(_errors(doc), [])

    def test_claim_source_required_must_be_true(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["claim_source_required"] = False
        self.assertGreater(len(_errors(doc)), 0)

    def test_additional_top_level_property_fails(self) -> None:
        doc = _valid()
        doc["undocumented_field"] = "should not be here"
        self.assertGreater(len(_errors(doc)), 0)

    def test_version_must_be_1_0(self) -> None:
        doc = _valid()
        doc["version"] = "2.0"
        self.assertGreater(len(_errors(doc)), 0)

    def test_episode_id_empty_string_fails(self) -> None:
        doc = _valid()
        doc["episode_id"] = ""
        self.assertGreater(len(_errors(doc)), 0)

    def test_empty_what_to_watch_for_fails(self) -> None:
        doc = _valid()
        doc["leverage_takeaway"]["what_to_watch_for"] = []
        self.assertGreater(len(_errors(doc)), 0)

    def test_empty_questions_to_ask_fails(self) -> None:
        doc = _valid()
        doc["leverage_takeaway"]["questions_to_ask"] = []
        self.assertGreater(len(_errors(doc)), 0)

    def test_documents_to_find_may_be_empty(self) -> None:
        doc = _valid()
        doc["leverage_takeaway"]["documents_to_find"] = []
        self.assertEqual(_errors(doc), [])

    def test_cost_transfer_item_missing_mechanism_fails(self) -> None:
        doc = _valid()
        del doc["cost_transfer"][0]["mechanism"]
        self.assertGreater(len(_errors(doc)), 0)

    def test_beneficiary_missing_capture_mechanism_fails(self) -> None:
        doc = _valid()
        del doc["beneficiaries"][0]["capture_mechanism"]
        self.assertGreater(len(_errors(doc)), 0)

    def test_additional_property_in_advertiser_safety_fails(self) -> None:
        doc = _valid()
        doc["advertiser_safety_posture"]["extra_field"] = "bad"
        self.assertGreater(len(_errors(doc)), 0)

    def test_additional_property_in_leverage_takeaway_fails(self) -> None:
        doc = _valid()
        doc["leverage_takeaway"]["extra_field"] = "bad"
        self.assertGreater(len(_errors(doc)), 0)


if __name__ == "__main__":
    unittest.main()
