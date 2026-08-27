from __future__ import annotations

import copy
import unittest

from core.validation.semantic_completeness_audit_v0_1 import audit_pf2_scope_completeness


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


class SemanticCompletenessAuditPF2V01Tests(unittest.TestCase):
    SOURCE = "Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes."

    def test_c01_reproduced_pf2_failure_is_flagged(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2"), ("2.4", "PF2")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertTrue(result["human_review_required"])
        self.assertTrue(result["stop_automatic_downstream_use"])
        self.assertIn("ausschließlich", result["matched_markers"])
        self.assertIn("einschließlich", result["matched_markers"])

    def test_c02_complete_pf2_assignment_is_not_flagged(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2"), ("2.2", "PF2"), ("2.4", "PF2")),
        )
        self.assertFalse(result["possible_multi_assignment_omission"])
        self.assertFalse(result["human_review_required"])
        self.assertFalse(result["stop_automatic_downstream_use"])

    def test_c03_marker_without_any_pf2_assignment_does_not_infer_pf2(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text="Die Unterlage gilt ausschließlich für Mai 2026.",
            model_response=response_with(("4.2", "PF4")),
        )
        self.assertFalse(result["possible_multi_assignment_omission"])
        self.assertIsNone(result["candidate_question_id"])
        self.assertFalse(result["auto_assignment_performed"])

    def test_c04_pf2_without_explicit_scope_marker_is_not_flagged(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text="Betrachtet wird das bestehende Rathaus.",
            model_response=response_with(("2.1", "PF2")),
        )
        self.assertFalse(result["possible_multi_assignment_omission"])
        self.assertEqual(result["matched_markers"], [])

    def test_c05_ausgenommen_marker_is_supported(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text="Betrachtet wird das Rathaus, ausgenommen der rückwärtige Parkplatz.",
            model_response=response_with(("2.1", "PF2")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertEqual(result["matched_markers"], ["ausgenommen"])

    def test_c06_model_output_is_not_mutated(self) -> None:
        response = response_with(("2.1", "PF2"), ("2.4", "PF2"))
        before = copy.deepcopy(response)
        result = audit_pf2_scope_completeness(source_text=self.SOURCE, model_response=response)
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertFalse(result["auto_assignment_performed"])
        self.assertEqual(result["decision_authority"], "NONE")

    def test_c07_audit_never_exposes_an_automatic_question_id(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertIsNone(result["candidate_question_id"])
        self.assertEqual(result["candidate_missing_dimension"], "PF2_SCOPE_MEMBERSHIP_OR_EXCLUSION")


if __name__ == "__main__":
    unittest.main()
