from __future__ import annotations

import unittest
from copy import deepcopy

import scripts.zs_ki_b_sem_approval_ceremony_v2_7_architecture_prep as v27


SECRET_A = "A" * 40
SECRET_B = "B" * 40


class SemV27ApprovalCeremonyArchitecturePrepTests(unittest.TestCase):
    def setUp(self):
        self.candidate = v27.build_candidate_snapshot()
        self.challenge = v27.build_challenge_preview(candidate=self.candidate, approval_secret=SECRET_A)
        self.artifact = v27.build_approval_artifact_preview(
            candidate=self.candidate,
            challenge=self.challenge,
            approval_secret=SECRET_A,
        )

    def test_v27_01_candidate_remains_non_authorizing(self):
        self.assertEqual(self.candidate["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(self.candidate["execution_authorized"])
        self.assertFalse(self.candidate["model_run_authorized"])
        self.assertFalse(self.candidate["model_contact_authorized"])

    def test_v27_02_challenge_stores_commitment_not_secret(self):
        self.assertNotIn("approval_secret", self.challenge)
        self.assertFalse(self.challenge["secret_stored_in_artifact"])
        self.assertEqual(self.challenge["approval_secret_commitment_sha256"], v27._sha256_text(SECRET_A))
        self.assertNotIn(SECRET_A, repr(self.challenge))

    def test_v27_03_challenge_binds_exact_candidate_hash(self):
        self.assertEqual(self.challenge["candidate_sha256"], self.candidate["authorization_candidate_sha256"])
        self.assertEqual(self.challenge["bound_main_commit"], self.candidate["bound_main_commit"])
        self.assertEqual(self.challenge["bound_v25_runner_blob_oid"], self.candidate["bound_v25_runner_blob_oid"])
        self.assertEqual(self.challenge["max_tokens"], 2048)

    def test_v27_04_approval_preview_stores_hmac_not_secret(self):
        self.assertIn("approval_proof_hmac_sha256", self.artifact)
        self.assertNotIn("approval_secret", self.artifact)
        self.assertFalse(self.artifact["secret_stored_in_artifact"])
        self.assertNotIn(SECRET_A, repr(self.artifact))

    def test_v27_05_approval_preview_authorizes_nothing(self):
        self.assertFalse(self.artifact["execution_authorized"])
        self.assertFalse(self.artifact["model_run_authorized"])
        self.assertFalse(self.artifact["model_contact_authorized"])
        self.assertFalse(self.artifact["authorization_consumed"])
        self.assertTrue(self.artifact["no_execution_from_approval_preview"])

    def test_v27_06_exact_secret_validates_proof(self):
        validated = v27.validate_approval_artifact_preview(
            candidate=self.candidate,
            challenge=self.challenge,
            artifact=self.artifact,
            approval_secret=SECRET_A,
        )
        self.assertEqual(validated, self.artifact)

    def test_v27_07_wrong_secret_fails(self):
        with self.assertRaises(PermissionError):
            v27.validate_approval_artifact_preview(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_B,
            )

    def test_v27_08_tampered_candidate_hash_fails(self):
        tampered = deepcopy(self.candidate)
        tampered["max_tokens"] = 1024
        with self.assertRaises(PermissionError):
            v27.build_challenge_preview(candidate=tampered, approval_secret=SECRET_A)

    def test_v27_09_tampered_challenge_fails(self):
        tampered = deepcopy(self.challenge)
        tampered["max_tokens"] = 1024
        with self.assertRaises(PermissionError):
            v27.build_approval_artifact_preview(
                candidate=self.candidate,
                challenge=tampered,
                approval_secret=SECRET_A,
            )

    def test_v27_10_tampered_approval_proof_fails(self):
        tampered = deepcopy(self.artifact)
        tampered["approval_proof_hmac_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            v27.validate_approval_artifact_preview(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=tampered,
                approval_secret=SECRET_A,
            )

    def test_v27_11_six_field_candidate_edit_does_not_create_v27_proof(self):
        edited = deepcopy(self.candidate)
        edited["status"] = "EXPLICIT_USER_APPROVED"
        edited["execution_authorized"] = True
        edited["model_run_authorized"] = True
        edited["model_contact_authorized"] = True
        edited["live_runner_version"] = edited["bound_v25_live_runner_version"]
        edited["live_run_type"] = edited["bound_v25_live_run_type"]
        with self.assertRaises(PermissionError):
            v27.build_challenge_preview(candidate=edited, approval_secret=SECRET_A)

    def test_v27_12_values_from_candidate_are_not_sufficient_for_proof(self):
        candidate_text = repr(self.candidate)
        self.assertNotIn(SECRET_A, candidate_text)
        self.assertNotEqual(self.challenge["approval_secret_commitment_sha256"], self.candidate["authorization_candidate_sha256"])

    def test_v27_13_secret_minimum_length_is_enforced(self):
        with self.assertRaises(PermissionError):
            v27.build_challenge_preview(candidate=self.candidate, approval_secret="short")

    def test_v27_14_report_is_model_free(self):
        report = v27.build_architecture_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["approval_ceremony_implemented_for_execution"])
        self.assertFalse(report["approval_gate_integrated"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])

    def test_v27_15_report_authorizes_nothing(self):
        report = v27.build_architecture_report()
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_qualified"])

    def test_v27_16_no_execute_or_transport_helper(self):
        self.assertFalse(hasattr(v27, "execute_once"))
        self.assertFalse(hasattr(v27, "_default_transport"))
        self.assertFalse(hasattr(v27, "approve_and_execute"))

    def test_v27_17_v26_candidate_validator_remains_required(self):
        tampered = deepcopy(self.candidate)
        tampered["authorization_candidate_sha256"] = "f" * 64
        with self.assertRaises(PermissionError):
            v27.build_challenge_preview(candidate=tampered, approval_secret=SECRET_A)

    def test_v27_18_artifact_requires_separate_gate_integration(self):
        self.assertTrue(self.artifact["separate_gate_integration_required"])
        self.assertEqual(self.artifact["status"], "EXPLICIT_USER_APPROVAL_PROOF_PREVIEW_NOT_EXECUTABLE")


if __name__ == "__main__":
    unittest.main()
