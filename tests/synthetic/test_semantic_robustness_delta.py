from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_boundary import FORBIDDEN_MODEL_FIELDS, validate_semantic_response
from core.validation.validator import validate_bundle
from llm.smoketest import parse_model_json
from tests.synthetic.test_validator import base_bundle

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "zs_ki_b_semantic_valid_response_v0_1.json"


def valid_response() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def boundary_codes(response: dict) -> set[str]:
    return {
        issue.code
        for issue in validate_semantic_response(
            response,
            allowed_source_location_ids={"SL-SYN-001", "SL-SYN-002"},
        )
    }


class SemanticRobustnessDeltaTests(unittest.TestCase):
    """Model-free regression coverage for DET delta D01-D05 only."""

    def test_D01_every_forbidden_model_field_is_rejected(self) -> None:
        for field in sorted(FORBIDDEN_MODEL_FIELDS):
            with self.subTest(field=field):
                response = valid_response()
                response["proposals"][0][field] = "synthetic-forbidden-value"
                self.assertIn("MODEL_AUTHORITY_VIOLATION", boundary_codes(response))

    def test_D02_deterministic_actor_cannot_create_human_decision(self) -> None:
        bundle = base_bundle()
        bundle["human_decisions"] = [
            {
                "human_decision_id": "HD-DET-001",
                "actor_type": "DETERMINISTIC",
                "decision_scope": "content",
                "decision_value": "synthetic",
                "reason": "synthetic robustness case",
            }
        ]
        codes = {issue.code for issue in validate_bundle(bundle)}
        self.assertIn("NONHUMAN_APPROVAL", codes)

    def test_D03_ambiguous_multi_mapping_with_human_review_is_allowed(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["conflict_candidate_refs"] = []
        proposal["uncertainty_notes"] = ["Zuordnung zwischen zwei bestehenden Fragen ist mehrdeutig."]
        proposal["human_review_required"] = True
        proposal["assignment_candidates"][0].update(
            assignment_confidence="UNCERTAIN",
            human_review_required=True,
        )
        proposal["assignment_candidates"][1].update(
            assignment_confidence="UNCERTAIN",
            human_review_required=True,
        )
        self.assertEqual(boundary_codes(response), set())

    def test_D04_duplicate_finding_id_with_different_content_fails(self) -> None:
        bundle = base_bundle()
        duplicate = copy.deepcopy(bundle["findings"][0])
        duplicate["normalized_statement"] = "abweichende synthetische Aussage"
        bundle["findings"].append(duplicate)
        codes = {issue.code for issue in validate_bundle(bundle)}
        self.assertIn("DUPLICATE_ID", codes)

    def test_D05_valid_json_with_trailing_prose_is_rejected(self) -> None:
        raw = '{"contract_version":"ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1"}\nBegründung außerhalb des JSON'
        with self.assertRaises(json.JSONDecodeError):
            parse_model_json(raw)


if __name__ == "__main__":
    unittest.main()
