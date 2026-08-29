from __future__ import annotations

import copy
import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v1_5 as v15


class MinistralV15QualificationAuthorizationPrepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = v15.load(v15.AUTH_PATH)

    def test_q01_authorization_is_live_single_use(self) -> None:
        self.assertEqual(self.auth["status"], "EXPLICIT_USER_APPROVED")
        self.assertTrue(self.auth["qualification_authorization_candidate_prepared"])
        self.assertTrue(self.auth["explicit_user_approval_required"])
        self.assertTrue(self.auth["explicit_user_approval_received"])
        self.assertTrue(self.auth["execution_authorized"])
        self.assertTrue(self.auth["model_run_authorized"])
        self.assertTrue(self.auth["model_contact_authorized"])
        self.assertFalse(self.auth["authorization_consumed"])
        self.assertTrue(self.auth["single_run_only"])
        self.assertTrue(v15._authorization_matches(self.auth, v15.RUNTIME_MODEL_ID))

    def test_q02_exact_runner_model_and_timeout_scope(self) -> None:
        self.assertEqual(self.auth["runner_version"], v15.RUNNER_VERSION)
        self.assertEqual(self.auth["run_type"], v15.RUN_TYPE)
        self.assertEqual(self.auth["runtime_model_id"], v15.RUNTIME_MODEL_ID)
        self.assertEqual(self.auth["model_repository"], v15.MODEL_REPOSITORY)
        self.assertEqual(self.auth["required_request_timeout_seconds"], v15.REQUIRED_TIMEOUT)
        self.assertEqual(self.auth["expected_model_request_count"], 16)
        self.assertEqual(self.auth["retry_count"], 0)
        self.assertFalse(self.auth["output_repair"])

    def test_q03_preflight_and_v14_failure_are_preserved(self) -> None:
        self.assertTrue(self.auth["preflight_pass_required"])
        self.assertTrue(self.auth["preflight_pass_observed"])
        self.assertTrue(self.auth["qualification_authorization_must_follow_preflight_pass"])
        self.assertTrue(self.auth["v14_timeout_failure_preserved"])
        self.assertTrue(self.auth["timeout_binding_fix_verified_model_free"])
        self.assertFalse(self.auth["qualification_authorization_ready_for_separate_user_decision"])

    def test_q04_consumed_state_fails_closed(self) -> None:
        auth = copy.deepcopy(self.auth)
        auth["authorization_consumed"] = True
        self.assertFalse(v15._authorization_matches(auth, v15.RUNTIME_MODEL_ID))

    def test_q05_wrong_timeout_or_request_count_fails_closed(self) -> None:
        auth = copy.deepcopy(self.auth)
        auth["required_request_timeout_seconds"] = 600
        self.assertFalse(v15._authorization_matches(auth, v15.RUNTIME_MODEL_ID))

        auth = copy.deepcopy(self.auth)
        auth["expected_model_request_count"] = 15
        self.assertFalse(v15._authorization_matches(auth, v15.RUNTIME_MODEL_ID))

    def test_q06_scope_remains_synthetic_local_and_not_qualified(self) -> None:
        self.assertTrue(self.auth["synthetic_only"])
        self.assertTrue(self.auth["local_loopback_only"])
        self.assertFalse(self.auth["remote_cloud"])
        self.assertFalse(self.auth["real_data"])
        self.assertFalse(self.auth["model_qualified"])
        self.assertFalse(self.auth["benchmark_approved"])
        self.assertFalse(self.auth["generalisation_approved"])
        self.assertFalse(self.auth["pilot_approved"])
        self.assertFalse(self.auth["production_approved"])
        self.assertFalse(self.auth["phase_f_approved"])


if __name__ == "__main__":
    unittest.main()
