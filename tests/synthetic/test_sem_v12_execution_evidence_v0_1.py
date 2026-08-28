from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "tests/fixtures/zs_ki_b_sem_v12_execution_result_2026_012_v0_1.json"


class SemV12ExecutionEvidenceTests(unittest.TestCase):
    def test_e01_consumed_run_evidence_records_exact_fail_closed_pf2_stop(self) -> None:
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        manifest = payload["manifest"]
        self.assertEqual(manifest["run_type"], "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-2-RUNTIME-GUARD-2026-012")
        self.assertEqual(manifest["runner_version"], "v1.2")
        self.assertEqual(manifest["observed_run_count"], 1)
        self.assertEqual(manifest["observed_model_request_count"], 2)
        self.assertEqual(manifest["model"], "qwen3-14b")
        self.assertFalse(manifest["model_qualified"])
        self.assertTrue(manifest["runtime_guard_bound"])

        self.assertEqual(len(payload["cases"]), 2)
        pf1, pf2 = payload["cases"]
        self.assertTrue(pf1["boundary_evaluation"]["passed"])
        self.assertTrue(pf1["gold_evaluation"]["passed"])

        boundary = pf2["boundary_evaluation"]
        self.assertTrue(boundary["formal_boundary_passed"])
        self.assertFalse(boundary["passed"])
        self.assertTrue(boundary["human_review_required"])
        self.assertFalse(boundary["automatic_downstream_use_allowed"])
        self.assertEqual(
            [row["code"] for row in boundary["issues"]],
            ["SEMANTIC_COMPLETENESS_REVIEW_REQUIRED"],
        )
        audit = boundary["completeness_audit"]
        self.assertEqual(audit["matched_markers"], ["ausschließlich", "einschließlich"])
        self.assertEqual(audit["observed_assignments"], [["2.1", "PF2"]])
        self.assertTrue(audit["possible_multi_assignment_omission"])
        self.assertTrue(audit["stop_automatic_downstream_use"])
        self.assertFalse(audit["auto_assignment_performed"])
        self.assertFalse(audit["model_output_mutated"])
        self.assertIsNone(audit["candidate_question_id"])
        self.assertEqual(audit["decision_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
