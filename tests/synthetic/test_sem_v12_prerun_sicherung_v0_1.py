from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_2 as runner


class SemV12PreRunSicherungTests(unittest.TestCase):
    def test_p01_dry_run_manifest_proves_guard_bound_and_consumed_run_blocked(self) -> None:
        payload = runner.build_dry_run_manifest(model="qwen3-14b")
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_2")
        self.assertEqual(manifest["runner_version"], "v1.2")
        self.assertEqual(manifest["runtime_guard_version"], "semantic-runtime-guard-v0.1")
        self.assertTrue(manifest["runtime_guard_bound"])
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["execution_attempted"])
        self.assertEqual(manifest["observed_run_count"], 0)
        self.assertEqual(manifest["observed_model_request_count"], 0)

    def test_p02_consumed_authorization_stops_before_any_model_contact(self) -> None:
        runner._install_bindings()
        preflight = runner.v11.v10.v09.preflight_loaded_model
        chat = runner.v11.v10.v09.chat_completion_structured
        with patch.object(runner.v11.v10.v09, "preflight_loaded_model", wraps=preflight) as preflight_mock, \
             patch.object(runner.v11.v10.v09, "chat_completion_structured", wraps=chat) as chat_mock, \
             patch.object(sys, "argv", ["runner", "--execute", "--model", "qwen3-14b"]):
            with self.assertRaises(SystemExit) as exc:
                runner.main()
        self.assertEqual(exc.exception.code, 2)
        preflight_mock.assert_not_called()
        chat_mock.assert_not_called()

    def test_p03_pf2_underassignment_stops_at_runtime_guard_before_gold_eligibility(self) -> None:
        case = {
            "case_id": "ZS-KI-B-SEM-V07-Q-PF2-SYN-001",
            "target_source_location_id": "SL-PF2-001",
            "source_locations": [
                {
                    "source_location_id": "SL-PF2-001",
                    "original_text": "Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes.",
                }
            ],
        }
        response = {
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
                        {"question_id": "2.1", "pf_id": "PF2", "assignment_confidence": "UNCERTAIN", "human_review_required": True},
                        {"question_id": "2.4", "pf_id": "PF2", "assignment_confidence": "UNCERTAIN", "human_review_required": True},
                    ],
                    "conflict_candidate_refs": [],
                    "gap_notes": [],
                    "uncertainty_notes": [],
                    "human_review_required": True,
                }
            ],
        }
        result = runner.evaluate_runtime_guard(case, response)
        self.assertTrue(result["formal_boundary_passed"])
        self.assertFalse(result["passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertIn("SEMANTIC_COMPLETENESS_REVIEW_REQUIRED", [row["code"] for row in result["issues"]])
        self.assertEqual(result["decision_authority"], "NONE")

    def test_p04_authorization_receipt_is_consumed_and_one_shot_remains_enforced(self) -> None:
        auth = runner.v11.v10.v09.base.load(runner.AUTH_PATH)
        self.assertEqual(auth["status"], "CONSUMED")
        self.assertEqual(auth["consumed_observed_run_count"], 1)
        self.assertEqual(auth["consumed_observed_model_request_count"], 2)
        self.assertTrue(auth["single_run_only"])
        self.assertEqual(auth["retry_count"], 0)
        self.assertFalse(auth["output_repair"])
        self.assertTrue(auth["synthetic_only"])
        self.assertTrue(auth["local_loopback_only"])
        self.assertFalse(auth["remote_cloud"])
        self.assertFalse(auth["real_data"])
        self.assertTrue(auth["runtime_guard_required"])


if __name__ == "__main__":
    unittest.main()
