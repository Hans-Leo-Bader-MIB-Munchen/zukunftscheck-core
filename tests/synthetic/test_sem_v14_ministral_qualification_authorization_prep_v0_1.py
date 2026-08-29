from __future__ import annotations

import copy
import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14


class MinistralQualificationAuthorizationPrepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = v14.load(v14.AUTH_PATH)

    def _approved_shape(self) -> dict:
        auth = copy.deepcopy(self.auth)
        auth["status"] = "EXPLICIT_USER_APPROVED"
        auth["execution_authorized"] = True
        auth["model_run_authorized"] = True
        auth["model_contact_authorized"] = True
        auth["explicit_user_approval_received"] = True
        return auth

    def test_q01_candidate_is_prepared_but_closed(self) -> None:
        self.assertEqual(self.auth["status"], "PREPARED_NOT_APPROVED")
        self.assertTrue(self.auth["qualification_authorization_candidate_prepared"])
        self.assertFalse(self.auth["explicit_user_approval_received"])
        self.assertFalse(self.auth["execution_authorized"])
        self.assertFalse(self.auth["model_run_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])
        self.assertFalse(v14._authorization_matches(self.auth, v14.RUNTIME_MODEL_ID))

    def test_q02_preflight_pass_is_preserved_as_prerequisite(self) -> None:
        self.assertTrue(self.auth["preflight_pass_required"])
        self.assertTrue(self.auth["preflight_pass_observed"])
        self.assertTrue(self.auth["qualification_authorization_must_follow_preflight_pass"])
        self.assertTrue(self.auth["qualification_authorization_ready_for_separate_user_decision"])

    def test_q03_exact_approved_shape_would_match(self) -> None:
        auth = self._approved_shape()
        self.assertTrue(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))

    def test_q04_wrong_runtime_id_fails_closed(self) -> None:
        auth = self._approved_shape()
        auth["runtime_model_id"] = v14.MODEL_REPOSITORY
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))

    def test_q05_wrong_request_count_or_retry_fails_closed(self) -> None:
        auth = self._approved_shape()
        auth["expected_model_request_count"] = 15
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))
        auth = self._approved_shape()
        auth["retry_count"] = 1
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))

    def test_q06_scope_remains_synthetic_local_and_not_qualified(self) -> None:
        self.assertTrue(self.auth["synthetic_only"])
        self.assertTrue(self.auth["local_loopback_only"])
        self.assertFalse(self.auth["remote_cloud"])
        self.assertFalse(self.auth["real_data"])
        self.assertFalse(self.auth["model_qualified"])
        self.assertFalse(self.auth["benchmark_approved"])
        self.assertFalse(self.auth["pilot_approved"])
        self.assertFalse(self.auth["production_approved"])
        self.assertFalse(self.auth["phase_f_approved"])


if __name__ == "__main__":
    unittest.main()
