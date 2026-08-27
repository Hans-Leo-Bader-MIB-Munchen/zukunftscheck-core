from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v1_2 as runner


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
                        "question_id": q,
                        "pf_id": pf,
                        "assignment_confidence": "UNCERTAIN",
                        "human_review_required": True,
                    }
                    for q, pf in assignments
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": True,
            }
        ],
    }


CASE = {
    "case_id": "ZS-KI-B-SEM-V07-Q-PF2-SYN-001",
    "target_source_location_id": "SL-PF2-001",
    "source_locations": [
        {
            "source_location_id": "SL-PF2-001",
            "original_text": "Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes.",
        }
    ],
}


class SemQualificationRunnerV12RuntimeGuardTests(unittest.TestCase):
    def test_r01_dry_run_binds_guard_but_authorizes_no_model_run(self) -> None:
        payload = runner.build_dry_run_manifest()
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_2")
        self.assertEqual(manifest["runner_version"], "v1.2")
        self.assertEqual(manifest["runtime_guard_version"], "semantic-runtime-guard-v0.1")
        self.assertTrue(manifest["runtime_guard_bound"])
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["execution_attempted"])
        self.assertEqual(manifest["observed_model_request_count"], 0)

    def test_r02_pf2_underassignment_is_stopped_before_gold(self) -> None:
        result = runner.evaluate_runtime_guard(CASE, response_with(("2.1", "PF2"), ("2.4", "PF2")))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertFalse(result["passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertTrue(result["completeness_audit"]["possible_multi_assignment_omission"])
        self.assertIn("SEMANTIC_COMPLETENESS_REVIEW_REQUIRED", [row["code"] for row in result["issues"]])

    def test_r03_pf2_complete_assignment_passes_guard(self) -> None:
        result = runner.evaluate_runtime_guard(
            CASE,
            response_with(("2.1", "PF2"), ("2.2", "PF2"), ("2.4", "PF2")),
        )
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["passed"])
        self.assertFalse(result["human_review_required"])
        self.assertTrue(result["automatic_downstream_use_allowed"])

    def test_r04_runner_has_no_authorized_execution_fixture(self) -> None:
        with self.assertRaises(PermissionError):
            runner.validate_execution_authorization("qwen3-14b")

    def test_r05_guard_has_no_decision_authority_and_mutates_nothing(self) -> None:
        response = response_with(("2.1", "PF2"), ("2.4", "PF2"))
        result = runner.evaluate_runtime_guard(CASE, response)
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertFalse(result["model_output_mutated"])
        self.assertEqual([a["question_id"] for a in response["proposals"][0]["assignment_candidates"]], ["2.1", "2.4"])


if __name__ == "__main__":
    unittest.main()
