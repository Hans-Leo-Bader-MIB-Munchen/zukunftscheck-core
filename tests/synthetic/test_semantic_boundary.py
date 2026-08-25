from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_boundary import validate_semantic_response

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "zs_ki_b_semantic_valid_response_v0_1.json"


def valid_response() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def codes(response: dict, allowed: set[str] | None = None) -> set[str]:
    issues = validate_semantic_response(
        response,
        allowed_source_location_ids=allowed or {"SL-SYN-001", "SL-SYN-002"},
    )
    return {issue.code for issue in issues}


class SemanticBoundaryTests(unittest.TestCase):
    def test_01_valid_multi_mapping_response_passes(self) -> None:
        self.assertEqual(codes(valid_response()), set())

    def test_02_unknown_source_location_fails(self) -> None:
        response = valid_response()
        self.assertIn("UNKNOWN_SOURCE_LOCATION_REF", codes(response, {"SL-OTHER"}))

    def test_03_wrong_contract_version_fails(self) -> None:
        response = valid_response()
        response["contract_version"] = "v0.2"
        self.assertIn("SEMANTIC_CONTRACT_VERSION_MISMATCH", codes(response))

    def test_04_unknown_question_id_fails(self) -> None:
        response = valid_response()
        response["proposals"][0]["assignment_candidates"][0]["question_id"] = "13.1"
        self.assertIn("UNKNOWN_QUESTION_ID", codes(response))

    def test_05_pf_question_mismatch_fails(self) -> None:
        response = valid_response()
        response["proposals"][0]["assignment_candidates"][0]["pf_id"] = "PF5"
        self.assertIn("PF_QUESTION_MISMATCH", codes(response))

    def test_06_question_status_is_forbidden_model_authority(self) -> None:
        response = valid_response()
        response["proposals"][0]["assignment_candidates"][0]["question_status"] = "beantwortet"
        result = codes(response)
        self.assertIn("MODEL_AUTHORITY_VIOLATION", result)
        self.assertIn("ASSIGNMENT_FIELD_FORBIDDEN", result)

    def test_07_governance_approval_is_forbidden(self) -> None:
        response = valid_response()
        response["proposals"][0]["governance_approval_state"] = "APPROVED"
        self.assertIn("MODEL_AUTHORITY_VIOLATION", codes(response))

    def test_08_human_decision_is_forbidden(self) -> None:
        response = valid_response()
        response["human_decision_id"] = "HD-AI-001"
        self.assertIn("MODEL_AUTHORITY_VIOLATION", codes(response))

    def test_09_confirmed_conflict_is_forbidden(self) -> None:
        response = valid_response()
        response["proposals"][0]["conflict_status"] = "CONFIRMED"
        self.assertIn("MODEL_AUTHORITY_VIOLATION", codes(response))

    def test_10_original_text_echo_or_overwrite_field_is_forbidden(self) -> None:
        response = valid_response()
        response["proposals"][0]["original_text"] = "veränderter Text"
        self.assertIn("MODEL_AUTHORITY_VIOLATION", codes(response))

    def test_11_invalid_finding_type_candidate_fails(self) -> None:
        response = valid_response()
        response["proposals"][0]["finding_type_candidate"] = "NEW_TYPE"
        self.assertIn("INVALID_FINDING_TYPE_CANDIDATE", codes(response))

    def test_12_invalid_evidence_relation_candidate_fails(self) -> None:
        response = valid_response()
        response["proposals"][0]["evidence_relation_type_candidate"] = "DRAFT"
        self.assertIn("INVALID_EVIDENCE_RELATION_CANDIDATE", codes(response))

    def test_13_derived_without_derivation_note_fails(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["evidence_relation_type_candidate"] = "DERIVED"
        proposal["derivation_note"] = ""
        self.assertIn("MISSING_DERIVATION_PATH", codes(response))

    def test_14_uncertain_assignment_requires_assignment_review(self) -> None:
        response = valid_response()
        assignment = response["proposals"][0]["assignment_candidates"][0]
        assignment["assignment_confidence"] = "UNCERTAIN"
        assignment["human_review_required"] = False
        self.assertIn("MISSING_REVIEW_FLAG", codes(response))

    def test_15_uncertainty_requires_proposal_review(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["conflict_candidate_refs"] = []
        proposal["uncertainty_notes"] = ["Zuordnung ist nur vorläufig."]
        proposal["human_review_required"] = False
        self.assertIn("MISSING_PROPOSAL_REVIEW_FLAG", codes(response))

    def test_16_gap_candidate_requires_proposal_review(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["conflict_candidate_refs"] = []
        proposal["gap_notes"] = ["Versionsdatum fehlt."]
        proposal["human_review_required"] = False
        self.assertIn("MISSING_PROPOSAL_REVIEW_FLAG", codes(response))

    def test_17_duplicate_proposal_id_fails(self) -> None:
        response = valid_response()
        response["proposals"].append(copy.deepcopy(response["proposals"][0]))
        self.assertIn("DUPLICATE_PROPOSAL_ID", codes(response))

    def test_18_duplicate_assignment_candidate_fails(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["assignment_candidates"].append(copy.deepcopy(proposal["assignment_candidates"][0]))
        self.assertIn("DUPLICATE_ASSIGNMENT_CANDIDATE", codes(response))

    def test_19_stage_open_is_forbidden(self) -> None:
        response = valid_response()
        response["proposals"][0]["stage1_open"] = True
        self.assertIn("MODEL_AUTHORITY_VIOLATION", codes(response))

    def test_20_empty_assignments_are_allowed_for_unmapped_proposal(self) -> None:
        response = valid_response()
        proposal = response["proposals"][0]
        proposal["assignment_candidates"] = []
        proposal["conflict_candidate_refs"] = []
        proposal["human_review_required"] = False
        self.assertEqual(codes(response), set())

    def test_21_unknown_conflict_source_reference_fails(self) -> None:
        response = valid_response()
        response["proposals"][0]["conflict_candidate_refs"] = ["SL-HALLUCINATED"]
        self.assertIn("UNKNOWN_CONFLICT_SOURCE_REF", codes(response))


if __name__ == "__main__":
    unittest.main()
