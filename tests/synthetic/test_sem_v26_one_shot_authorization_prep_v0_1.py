from __future__ import annotations

import unittest
from copy import deepcopy

import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26


class SemV26OneShotAuthorizationPrepTests(unittest.TestCase):
    def test_v26_01_candidate_awaits_explicit_user_approval(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertTrue(candidate["approval_required"])
        self.assertTrue(candidate["no_execution_from_candidate"])

    def test_v26_02_candidate_authorizes_nothing(self):
        candidate = v26.build_authorization_candidate()
        self.assertFalse(candidate["execution_authorized"])
        self.assertFalse(candidate["model_run_authorized"])
        self.assertFalse(candidate["model_contact_authorized"])
        self.assertFalse(candidate["authorization_consumed"])

    def test_v26_03_max_tokens_2048_is_exact(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["max_tokens"], 2048)
        self.assertEqual(v26.v25.MAX_TOKENS, 2048)

    def test_v26_04_exact_v25_runner_blob_is_bound(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["bound_v25_runner_blob_oid"], v26.EXPECTED_V25_RUNNER_BLOB)
        self.assertEqual(candidate["live_runner_blob_oid"], v26.EXPECTED_V25_RUNNER_BLOB)

    def test_v26_05_current_commit_and_runner_path_are_bound(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["bound_main_commit"], v26._current_git_commit())
        self.assertEqual(candidate["live_runner_git_commit"], v26._current_git_commit())
        self.assertEqual(candidate["bound_v25_runner_path"], v26.EXPECTED_V25_RUNNER_PATH)
        self.assertEqual(candidate["live_runner_path"], v26.EXPECTED_V25_RUNNER_PATH)

    def test_v26_06_candidate_hash_is_exact_and_tamper_fails(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["authorization_candidate_sha256"], v26.candidate_sha256(candidate))
        tampered = deepcopy(candidate)
        tampered["max_tokens"] = 1024
        with self.assertRaises(PermissionError):
            v26.validate_authorization_candidate(tampered)

    def test_v26_07_manual_status_escalation_is_not_a_valid_candidate(self):
        candidate = v26.build_authorization_candidate()
        candidate["status"] = "EXPLICIT_USER_APPROVED"
        candidate["execution_authorized"] = True
        candidate["model_run_authorized"] = True
        candidate["model_contact_authorized"] = True
        with self.assertRaises(PermissionError):
            v26.validate_authorization_candidate(candidate)

    def test_v26_08_candidate_cannot_execute_v25_runner(self):
        candidate = v26.build_authorization_candidate()
        with self.assertRaises(PermissionError):
            v26.v25.validate_live_execution_authorization(candidate)

    def test_v26_09_candidate_is_single_use_only(self):
        candidate = v26.build_authorization_candidate()
        self.assertTrue(candidate["single_use_only"])
        self.assertTrue(candidate["single_run_only"])
        self.assertEqual(candidate["expected_model_request_count"], 16)

    def test_v26_10_retry_repair_and_rerun_are_forbidden(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["retry_count"], 0)
        self.assertFalse(candidate["output_repair"])
        self.assertFalse(candidate["automatic_retry_authorized"])
        self.assertFalse(candidate["automatic_rerun_authorized"])

    def test_v26_11_report_is_model_free_and_non_executable(self):
        report = v26.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["governance_status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(report["ready_for_explicit_user_approval"])
        self.assertTrue(report["separate_approval_artifact_required"])
        self.assertFalse(report["approval_ceremony_implemented"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])
        self.assertFalse(report["authorization_artifact_persisted"])
        self.assertFalse(report["authorization_consumed"])

    def test_v26_12_report_preserves_model_not_qualified(self):
        report = v26.build_prep_report()
        self.assertFalse(report["model_qualified"])
        self.assertTrue(report["checks"]["model_not_qualified"])

    def test_v26_13_no_approval_or_execution_helper_exists(self):
        self.assertFalse(hasattr(v26, "approve_candidate"))
        self.assertFalse(hasattr(v26, "approve_authorization"))
        self.assertFalse(hasattr(v26, "execute_once"))

    def test_v26_14_v25_runner_blob_on_head_remains_exact(self):
        self.assertEqual(v26._current_v25_runner_blob(), v26.EXPECTED_V25_RUNNER_BLOB)

    def test_v26_15_candidate_validator_accepts_exact_candidate_only(self):
        candidate = v26.build_authorization_candidate()
        validated = v26.validate_authorization_candidate(candidate)
        self.assertEqual(validated, candidate)
        altered = deepcopy(candidate)
        altered["runtime_model_id"] = "wrong-model"
        altered["authorization_candidate_sha256"] = v26.candidate_sha256(altered)
        with self.assertRaises(PermissionError):
            v26.validate_authorization_candidate(altered)

    def test_v26_16_status_escalated_candidate_is_rejected_by_actual_v25_gate(self):
        candidate = v26.build_authorization_candidate()
        escalated = deepcopy(candidate)
        escalated.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        with self.assertRaises(PermissionError):
            v26.v25.validate_live_execution_authorization(escalated)
        self.assertTrue(v26._status_escalated_candidate_rejected_by_v25(candidate))

    def test_v26_17_stale_commit_or_blob_candidate_is_rejected(self):
        candidate = v26.build_authorization_candidate()
        for key in ("live_runner_git_commit", "live_runner_blob_oid", "bound_v25_runner_blob_oid"):
            altered = deepcopy(candidate)
            altered[key] = "0" * 40
            altered["authorization_candidate_sha256"] = v26.candidate_sha256(altered)
            with self.assertRaises(PermissionError):
                v26.validate_authorization_candidate(altered)

    def test_v26_18_candidate_only_identity_is_distinct_from_bound_v25_identity(self):
        candidate = v26.build_authorization_candidate()
        self.assertEqual(candidate["bound_v25_live_runner_version"], v26.v25.RUNNER_VERSION)
        self.assertEqual(candidate["bound_v25_live_run_type"], v26.v25.RUN_TYPE)
        self.assertNotEqual(candidate["live_runner_version"], v26.v25.RUNNER_VERSION)
        self.assertNotEqual(candidate["live_run_type"], v26.v25.RUN_TYPE)
        self.assertTrue(candidate["candidate_hash_is_integrity_checksum_not_authentication"])
        self.assertTrue(candidate["separate_approval_artifact_required"])
        report = v26.build_prep_report()
        self.assertTrue(report["checks"]["status_escalation_rejected_by_actual_v25_gate"])


if __name__ == "__main__":
    unittest.main()
