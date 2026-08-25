from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.smoketest import build_messages, evaluate_smoke, parse_model_json

ROOT = Path(__file__).resolve().parents[2]
CASE = json.loads((ROOT / "tests" / "fixtures" / "zs_ki_b_smoketest_case_v0_1.json").read_text(encoding="utf-8"))
EXPECT = json.loads((ROOT / "tests" / "fixtures" / "zs_ki_b_smoketest_expectations_v0_1.json").read_text(encoding="utf-8"))


def valid_model_response() -> dict:
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1",
        "source_location_id": "SL-SMOKE-003",
        "proposals": [
            {
                "proposal_id": "P-SMOKE-001",
                "normalized_statement": "Die aktuelle Projektübersicht nennt 2.620 m², während eine andere bereitgestellte Fundstelle 2.450 m² nennt; die Maßgeblichkeit ist ungeklärt.",
                "finding_type_candidate": "WI",
                "evidence_relation_type_candidate": "DIRECT",
                "derivation_note": "",
                "assignment_candidates": [
                    {"question_id": "6.3", "pf_id": "PF6", "assignment_confidence": "CLEAR", "human_review_required": False},
                    {"question_id": "11.1", "pf_id": "PF11", "assignment_confidence": "PLAUSIBLE", "human_review_required": True}
                ],
                "conflict_candidate_refs": ["SL-SMOKE-002"],
                "gap_notes": [],
                "uncertainty_notes": ["Welche Flächenangabe maßgeblich ist, ist nicht dokumentiert."],
                "human_review_required": True
            },
            {
                "proposal_id": "P-SMOKE-002",
                "normalized_statement": "Für Barrierefreiheit liegt keine Fachuntersuchung vor und eine zuständige externe Fachstelle ist nicht benannt.",
                "finding_type_candidate": "IL",
                "evidence_relation_type_candidate": "DIRECT",
                "derivation_note": "",
                "assignment_candidates": [
                    {"question_id": "8.5", "pf_id": "PF8", "assignment_confidence": "PLAUSIBLE", "human_review_required": True},
                    {"question_id": "11.3", "pf_id": "PF11", "assignment_confidence": "CLEAR", "human_review_required": False}
                ],
                "conflict_candidate_refs": [],
                "gap_notes": ["Fachuntersuchung und benannte Fachstelle fehlen."],
                "uncertainty_notes": [],
                "human_review_required": True
            }
        ]
    }


class LocalSmokeHarnessTests(unittest.TestCase):
    def test_01_loopback_ipv4_allowed(self) -> None:
        self.assertEqual(validate_local_base_url("http://127.0.0.1:1234/v1"), "http://127.0.0.1:1234/v1")

    def test_02_localhost_allowed(self) -> None:
        self.assertEqual(validate_local_base_url("http://localhost:1234/v1/"), "http://localhost:1234/v1")

    def test_03_remote_host_rejected(self) -> None:
        with self.assertRaises(LocalModelError):
            validate_local_base_url("https://example.com/v1")

    def test_04_credentials_in_url_rejected(self) -> None:
        with self.assertRaises(LocalModelError):
            validate_local_base_url("http://user:pass@127.0.0.1:1234/v1")

    def test_05_messages_include_frozen_target(self) -> None:
        messages = build_messages(CASE)
        self.assertEqual(len(messages), 2)
        self.assertIn("SL-SMOKE-003", messages[1]["content"])
        self.assertIn("SYNTHETIC_ONLY", messages[1]["content"])

    def test_06_messages_include_full_67_question_reference(self) -> None:
        payload = json.loads(build_messages(CASE)[1]["content"])
        self.assertEqual(len(payload["reference_questions"]), 67)

    def test_07_strict_json_parser_accepts_object(self) -> None:
        self.assertEqual(parse_model_json('{"a":1}'), {"a": 1})

    def test_08_strict_json_parser_rejects_markdown_fence(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_model_json('```json\n{"a":1}\n```')

    def test_09_predeclared_valid_smoke_response_passes(self) -> None:
        evaluation = evaluate_smoke(valid_model_response(), case=CASE, expectations=EXPECT)
        self.assertTrue(evaluation["passed"], evaluation)

    def test_10_missing_conflict_candidate_fails_smoke(self) -> None:
        response = valid_model_response()
        response["proposals"][0]["conflict_candidate_refs"] = []
        evaluation = evaluate_smoke(response, case=CASE, expectations=EXPECT)
        self.assertFalse(evaluation["passed"])
        self.assertFalse(evaluation["criteria"]["conflict_candidate_pass"])

    def test_11_missing_second_question_group_fails_smoke(self) -> None:
        response = valid_model_response()
        response["proposals"] = [response["proposals"][0]]
        evaluation = evaluate_smoke(response, case=CASE, expectations=EXPECT)
        self.assertFalse(evaluation["criteria"]["question_groups_pass"])

    def test_12_unknown_conflict_reference_fails_boundary(self) -> None:
        response = valid_model_response()
        response["proposals"][0]["conflict_candidate_refs"] = ["SL-HALLUCINATED"]
        evaluation = evaluate_smoke(response, case=CASE, expectations=EXPECT)
        self.assertFalse(evaluation["criteria"]["boundary_pass"])

    def test_13_forbidden_question_status_fails_boundary(self) -> None:
        response = valid_model_response()
        response["proposals"][0]["question_status"] = "beantwortet"
        evaluation = evaluate_smoke(response, case=CASE, expectations=EXPECT)
        self.assertFalse(evaluation["criteria"]["boundary_pass"])

    def test_14_expectations_are_bound_to_same_case(self) -> None:
        self.assertEqual(EXPECT["case_id"], CASE["case_id"])
        self.assertEqual(EXPECT["target_source_location_id"], CASE["target_source_location_id"])


if __name__ == "__main__":
    unittest.main()
