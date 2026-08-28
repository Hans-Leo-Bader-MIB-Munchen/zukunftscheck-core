from __future__ import annotations

import copy
import unittest

from core.validation.semantic_completeness_audit_v0_2 import audit_pf2_scope_completeness
from core.validation.semantic_runtime_guard_v0_2 import evaluate_semantic_runtime_guard


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


class SemanticCompletenessAuditPF2V02Tests(unittest.TestCase):
    SOURCE = "Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes."

    def test_h01_complete_pf2_omission_is_fail_closed(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("4.2", "PF4")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertTrue(result["human_review_required"])
        self.assertTrue(result["stop_automatic_downstream_use"])
        self.assertEqual(
            result["missing_required_assignments"],
            [["2.1", "PF2"], ["2.2", "PF2"]],
        )

    def test_h02_missing_21_is_fail_closed(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.2", "PF2")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertEqual(result["missing_required_assignments"], [["2.1", "PF2"]])

    def test_h03_missing_22_is_fail_closed(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2")),
        )
        self.assertTrue(result["possible_multi_assignment_omission"])
        self.assertEqual(result["missing_required_assignments"], [["2.2", "PF2"]])

    def test_h04_complete_required_pf2_is_not_stopped(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text=self.SOURCE,
            model_response=response_with(("2.1", "PF2"), ("2.2", "PF2")),
        )
        self.assertFalse(result["possible_multi_assignment_omission"])
        self.assertEqual(result["missing_required_assignments"], [])

    def test_h05_date_only_exclusivity_does_not_create_pf2_stop(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text="Die Unterlage gilt ausschließlich für Mai 2026.",
            model_response=response_with(("4.2", "PF4")),
        )
        self.assertFalse(result["pf2_scope_context_detected"])
        self.assertFalse(result["possible_multi_assignment_omission"])

    def test_h06_equivalent_scope_language_is_detected(self) -> None:
        result = audit_pf2_scope_completeness(
            source_text="Betrachtet wird nur das Rathaus mit Ausnahme des rückwärtigen Parkplatzes.",
            model_response=response_with(("2.1", "PF2")),
        )
        self.assertTrue(result["pf2_scope_context_detected"])
        self.assertIn("nur", result["matched_markers"])
        self.assertIn("mit ausnahme", result["matched_markers"])
        self.assertTrue(result["possible_multi_assignment_omission"])

    def test_h07_audit_does_not_mutate_or_auto_assign(self) -> None:
        response = response_with()
        before = copy.deepcopy(response)
        result = audit_pf2_scope_completeness(source_text=self.SOURCE, model_response=response)
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertFalse(result["auto_assignment_performed"])
        self.assertIsNone(result["candidate_question_id"])
        self.assertEqual(result["decision_authority"], "NONE")

    def test_h08_runtime_guard_v02_blocks_complete_pf2_omission(self) -> None:
        response = response_with(("4.2", "PF4"))
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response,
            allowed_source_location_ids={"SL-PF2-001"},
            target_source_location_id="SL-PF2-001",
        )
        self.assertTrue(result["boundary_passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertEqual(result["runtime_guard_version"], "semantic-runtime-guard-v0.2")

    def test_h09_boundary_failure_requires_human_review_in_v02(self) -> None:
        response = response_with(("2.1", "PF2"), ("2.2", "PF2"))
        response["source_location_id"] = "SL-WRONG"
        result = evaluate_semantic_runtime_guard(
            source_text=self.SOURCE,
            model_response=response,
            allowed_source_location_ids={"SL-PF2-001"},
            target_source_location_id="SL-PF2-001",
        )
        self.assertFalse(result["boundary_passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])


if __name__ == "__main__":
    unittest.main()
