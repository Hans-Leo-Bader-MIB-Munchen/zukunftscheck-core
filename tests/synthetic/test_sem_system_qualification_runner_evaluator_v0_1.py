from __future__ import annotations

import copy
import unittest

from core.validation.semantic_system_qualification_evaluator_v0_1 import (
    UNKNOWN_SYSTEM_STATE_STOP_CODE,
    evaluate_system_case,
)
import scripts.zs_ki_b_sem_system_qualification_runner_v0_1 as runner


class SemSystemQualificationRunnerEvaluatorV01Tests(unittest.TestCase):
    def test_r01_model_free_runner_matches_all_19_frozen_cases(self) -> None:
        result = runner.run_model_free_system_qualification()
        manifest = result["manifest"]
        self.assertEqual(result["mode"], "MODEL_FREE_GUARDED_SYSTEM_QUALIFICATION_V0_1")
        self.assertEqual(manifest["system_case_count"], 19)
        self.assertEqual(manifest["system_case_pass_count"], 19)
        self.assertTrue(manifest["guarded_system_qualified"])
        self.assertFalse(manifest["model_qualified"])
        self.assertFalse(manifest["model_contact_attempted"])
        self.assertEqual(manifest["model_request_count"], 0)
        self.assertFalse(manifest["remote_cloud"])
        self.assertFalse(manifest["real_data"])
        self.assertFalse(manifest["pilot_approved"])
        self.assertFalse(manifest["production_approved"])
        self.assertFalse(manifest["phase_f_approved"])
        self.assertTrue(all(row["evaluation"]["case_passed"] for row in result["cases"]))

    def test_r02_runner_preserves_16_pass_and_3_stop_shape(self) -> None:
        result = runner.run_model_free_system_qualification()
        behaviors = [row["evaluation"]["actual_behavior"] for row in result["cases"]]
        self.assertEqual(behaviors.count("PASS_THROUGH"), 16)
        self.assertEqual(behaviors.count("FAIL_CLOSED_STOP"), 3)

    def test_r03_pf2_underassignment_uses_stable_completeness_stop_code(self) -> None:
        result = runner.run_model_free_system_qualification()
        row = next(row for row in result["cases"] if row["system_case_id"] == "SYS-STOP-PF2-UNDERASSIGN")
        evaluation = row["evaluation"]
        self.assertEqual(evaluation["stop_code"], "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED")
        self.assertTrue(evaluation["human_review_required"])
        self.assertFalse(evaluation["automatic_downstream_use_allowed"])
        self.assertTrue(evaluation["case_passed"])

    def test_r04_formal_boundary_failure_is_elevated_to_human_review_stop(self) -> None:
        result = runner.run_model_free_system_qualification()
        row = next(row for row in result["cases"] if row["system_case_id"] == "SYS-STOP-TARGET-MISMATCH")
        evaluation = row["evaluation"]
        self.assertEqual(evaluation["stop_code"], "TARGET_SOURCE_LOCATION_MISMATCH")
        self.assertTrue(evaluation["human_review_required"])
        self.assertFalse(evaluation["automatic_downstream_use_allowed"])
        self.assertTrue(evaluation["case_passed"])

    def test_r05_unknown_state_is_fail_closed_and_never_passes_through(self) -> None:
        spec = {
            "system_case_id": "SYS-STOP-UNKNOWN-STATE",
            "expected_behavior": "FAIL_CLOSED_STOP",
            "expected_stop_code": UNKNOWN_SYSTEM_STATE_STOP_CODE,
            "human_review_required": True,
            "automatic_downstream_use_allowed": False,
        }
        evaluation = evaluate_system_case(
            case_spec=spec,
            guard_result=None,
            system_state_classified=False,
        )
        self.assertTrue(evaluation["case_passed"])
        self.assertEqual(evaluation["actual_behavior"], "FAIL_CLOSED_STOP")
        self.assertTrue(evaluation["human_review_required"])
        self.assertFalse(evaluation["automatic_downstream_use_allowed"])
        self.assertFalse(evaluation["model_qualification_changed"])

    def test_r06_evaluator_detects_wrong_expected_stop_code(self) -> None:
        spec = {
            "system_case_id": "NEG",
            "expected_behavior": "FAIL_CLOSED_STOP",
            "expected_stop_code": "WRONG_CODE",
            "human_review_required": True,
            "automatic_downstream_use_allowed": False,
        }
        evaluation = evaluate_system_case(
            case_spec=spec,
            guard_result=None,
            system_state_classified=False,
        )
        self.assertFalse(evaluation["case_passed"])
        self.assertFalse(evaluation["checks"]["stop_code_matches"])

    def test_r07_evaluator_fails_if_guard_reports_model_output_mutation(self) -> None:
        spec = {"system_case_id": "PASS", "expected_behavior": "PASS_THROUGH"}
        guard_result = {
            "boundary_passed": True,
            "automatic_downstream_use_allowed": True,
            "human_review_required": False,
            "model_output_mutated": True,
            "boundary_issues": [],
            "completeness_audit": None,
        }
        original = copy.deepcopy(guard_result)
        evaluation = evaluate_system_case(case_spec=spec, guard_result=guard_result)
        self.assertFalse(evaluation["case_passed"])
        self.assertFalse(evaluation["checks"]["no_model_output_mutation"])
        self.assertEqual(guard_result, original)


if __name__ == "__main__":
    unittest.main()
