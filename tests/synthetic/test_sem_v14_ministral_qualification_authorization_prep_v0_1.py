from __future__ import annotations

import copy
import json
import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14


RESULT_PATH = v14.ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_qualification_result_timeout_failure_preserved_v0_1.json"


class MinistralQualificationAuthorizationPrepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = v14.load(v14.AUTH_PATH)
        self.result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    def test_q01_authorization_is_consumed_and_closed(self) -> None:
        self.assertEqual(self.auth["status"], "CONSUMED_EXECUTED_ONCE_FAILED_TIMEOUT")
        self.assertTrue(self.auth["qualification_authorization_candidate_prepared"])
        self.assertTrue(self.auth["explicit_user_approval_received"])
        self.assertTrue(self.auth["authorization_consumed"])
        self.assertFalse(self.auth["execution_authorized"])
        self.assertFalse(self.auth["model_run_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])
        self.assertTrue(self.auth["model_contact_performed"])
        self.assertFalse(v14._authorization_matches(self.auth, v14.RUNTIME_MODEL_ID))

    def test_q02_preflight_pass_remains_preserved_as_historical_prerequisite(self) -> None:
        self.assertTrue(self.auth["preflight_pass_required"])
        self.assertTrue(self.auth["preflight_pass_observed"])
        self.assertTrue(self.auth["qualification_authorization_must_follow_preflight_pass"])
        self.assertFalse(self.auth["qualification_authorization_ready_for_separate_user_decision"])

    def test_q03_failure_result_preserves_single_attempt_and_timeout(self) -> None:
        self.assertEqual(self.result["mode"], "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_4")
        manifest = self.result["manifest"]
        self.assertEqual(manifest["observed_run_count"], 1)
        self.assertEqual(manifest["observed_model_request_count"], 1)
        self.assertTrue(manifest["model_contact_performed"])
        self.assertEqual(self.result["cases"][0]["case_id"], "ZS-KI-B-SEM-V07-Q-PF1-SYN-001")
        self.assertIn("timed out", self.result["cases"][0]["endpoint_error"])

    def test_q04_preserved_result_keeps_model_unqualified_and_scope_closed(self) -> None:
        manifest = self.result["manifest"]
        self.assertFalse(manifest["model_qualified"])
        self.assertFalse(manifest["benchmark_approved"])
        self.assertFalse(manifest["generalisation_approved"])
        self.assertFalse(manifest["pilot_approved"])
        self.assertFalse(manifest["production_approved"])
        self.assertFalse(manifest["phase_f_approved"])

    def test_q05_any_attempt_to_reopen_consumed_authorization_fails_closed(self) -> None:
        auth = copy.deepcopy(self.auth)
        auth["status"] = "EXPLICIT_USER_APPROVED"
        auth["execution_authorized"] = True
        auth["model_run_authorized"] = True
        auth["model_contact_authorized"] = True
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))

    def test_q06_scope_remains_synthetic_local_and_no_retry_or_repair(self) -> None:
        self.assertTrue(self.auth["synthetic_only"])
        self.assertTrue(self.auth["local_loopback_only"])
        self.assertFalse(self.auth["remote_cloud"])
        self.assertFalse(self.auth["real_data"])
        self.assertEqual(self.auth["retry_count"], 0)
        self.assertFalse(self.auth["output_repair"])
        self.assertTrue(self.auth["single_run_only"])
        self.assertFalse(self.auth["model_qualified"])


if __name__ == "__main__":
    unittest.main()
