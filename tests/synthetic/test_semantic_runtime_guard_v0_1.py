from __future__ import annotations

import copy
import unittest

from core.validation.semantic_runtime_guard_v0_1 import evaluate_semantic_runtime_guard


def response_with(*assignments: tuple[str, str]) -> dict:
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": "SL-PF2-001",
        "proposals": [
            {
                "proposal_id": "P-SL-PF2-001-1",
                "source_location_id": "SL-PF2-001",
                "normalized_statement": "synthetic",
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {
                        "question_id": question_id,
                        "pf_id": pf_id,
                        "assignment_confidence": "UNCERTAIN",
                        "human_review_required": True,
                    }
                    for question_id, pf_id in assignments
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": True,
            }
        ],
    }


class SemanticRuntimeGuardV01Tests(unittest.TestCase):
    SOURCE = "Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes."
    ALLOWED = {"SL-PF2-001"}

    def test_g01_pf2_undercoverage_blocks_automatic_downstream_use(self) -> None:
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2"), ("2.4", "PF2")),
            allowed_source_location_ids=self.ALLOWED,
            target_source_location_id="SL-PF2-001",
        )
        self.assertTrue(result["boundary_passed"])
        self.assertTrue(result["completeness_audit"]["possible_multi_assignment_omission"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])

    def test_g02_complete_pf2_passes_guard(self) -> None:
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2"), ("2.2", "PF2"), ("2.4", "PF2")),
            allowed_source_location_ids=self.ALLOWED,
            target_source_location_id="SL-PF2-001",
        )
        self.assertTrue(result["boundary_passed"])
        self.assertFalse(result["completeness_audit"]["possible_multi_assignment_omission"])
        self.assertFalse(result["human_review_required"])
        self.assertTrue(result["automatic_downstream_use_allowed"])

    def test_g03_boundary_failure_stops_before_completeness_audit(self) -> None:
        response = response_with(("2.1", "PF2"))
        response["source_location_id"] = "SL-WRONG"
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response,
            allowed_source_location_ids=self.ALLOWED,
            target_source_location_id="SL-PF2-001",
        )
        self.assertFalse(result["boundary_passed"])
        self.assertIsNone(result["completeness_audit"])
        self.assertFalse(result["automatic_downstream_use_allowed"])

    def test_g04_guard_never_mutates_or_repairs_model_output(self) -> None:
        response = response_with(("2.1", "PF2"))
        before = copy.deepcopy(response)
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response,
            allowed_source_location_ids=self.ALLOWED,
            target_source_location_id="SL-PF2-001",
        )
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertIsNone(result["completeness_audit"]["candidate_question_id"])


if __name__ == "__main__":
    unittest.main()
