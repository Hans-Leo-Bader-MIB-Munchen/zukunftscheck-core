from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28


SECRET_A = "A" * 40
SECRET_B = "B" * 40
NONCE_A = "1" * 64
NONCE_B = "2" * 64


class SemV28ExecutionGateIntegrationPrepTests(unittest.TestCase):
    def setUp(self):
        self.candidate = v28.build_candidate_snapshot()
        self.challenge = v28.build_gate_challenge_preview(
            candidate=self.candidate,
            approval_secret=SECRET_A,
            nonce=NONCE_A,
        )
        self.artifact = v28.build_gate_approval_proof_preview(
            candidate=self.candidate,
            persisted_challenge=self.challenge,
            approval_secret=SECRET_A,
        )

    def test_v28_01_candidate_remains_non_authorizing(self):
        self.assertEqual(self.candidate["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(self.candidate["execution_authorized"])
        self.assertFalse(self.candidate["model_run_authorized"])
        self.assertFalse(self.candidate["model_contact_authorized"])

    def test_v28_02_nonce_is_256_bit_hex(self):
        nonce = v28.generate_gate_nonce()
        self.assertEqual(len(nonce), 64)
        bytes.fromhex(nonce)

    def test_v28_03_nonce_validation_fail_closed(self):
        for bad in ("", "A" * 64, "g" * 64, "1" * 63, "1" * 65, None, 7):
            with self.subTest(bad=bad):
                with self.assertRaises(PermissionError):
                    v28._require_nonce(bad)

    def test_v28_04_challenge_binds_nonce_and_candidate(self):
        self.assertEqual(self.challenge["gate_nonce"], NONCE_A)
        self.assertEqual(self.challenge["candidate_sha256"], self.candidate["authorization_candidate_sha256"])
        self.assertEqual(self.challenge["bound_main_commit"], self.candidate["bound_main_commit"])
        self.assertEqual(self.challenge["max_tokens"], 2048)

    def test_v28_05_challenge_id_changes_with_nonce(self):
        other = v28.build_gate_challenge_preview(
            candidate=self.candidate,
            approval_secret=SECRET_A,
            nonce=NONCE_B,
        )
        self.assertNotEqual(self.challenge["challenge_id"], other["challenge_id"])

    def test_v28_06_challenge_stores_commitment_not_secret(self):
        self.assertNotIn("approval_secret", self.challenge)
        self.assertNotIn(SECRET_A, repr(self.challenge))
        self.assertFalse(self.challenge["secret_stored_in_artifact"])

    def test_v28_07_challenge_authorizes_nothing(self):
        self.assertFalse(self.challenge["execution_authorized"])
        self.assertFalse(self.challenge["model_run_authorized"])
        self.assertFalse(self.challenge["model_contact_authorized"])
        self.assertTrue(self.challenge["no_execution_from_challenge"])

    def test_v28_08_exact_challenge_validates(self):
        validated = v28.validate_gate_challenge_preview(
            candidate=self.candidate,
            challenge=self.challenge,
            approval_secret=SECRET_A,
        )
        self.assertEqual(validated, self.challenge)

    def test_v28_09_wrong_secret_rejects_challenge(self):
        with self.assertRaises(PermissionError):
            v28.validate_gate_challenge_preview(
                candidate=self.candidate,
                challenge=self.challenge,
                approval_secret=SECRET_B,
            )

    def test_v28_10_tampered_nonce_rejects_challenge(self):
        tampered = deepcopy(self.challenge)
        tampered["gate_nonce"] = NONCE_B
        with self.assertRaises(PermissionError):
            v28.validate_gate_challenge_preview(
                candidate=self.candidate,
                challenge=tampered,
                approval_secret=SECRET_A,
            )

    def test_v28_11_tampered_binding_rejects_challenge(self):
        for field, value in (
            ("max_tokens", 1024),
            ("bound_main_commit", "0" * 40),
            ("bound_v25_runner_blob_oid", "0" * 40),
            ("model", "tampered-model"),
            ("base_url", "http://127.0.0.1:9999"),
        ):
            tampered = deepcopy(self.challenge)
            tampered[field] = value
            with self.subTest(field=field):
                with self.assertRaises(PermissionError):
                    v28.validate_gate_challenge_preview(
                        candidate=self.candidate,
                        challenge=tampered,
                        approval_secret=SECRET_A,
                    )

    def test_v28_12_persist_challenge_once_and_load_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "challenge.json"
            v28.persist_gate_challenge_once(path, self.challenge)
            loaded = v28.load_persisted_gate_challenge(path)
            self.assertEqual(loaded, self.challenge)

    def test_v28_13_second_challenge_persist_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "challenge.json"
            v28.persist_gate_challenge_once(path, self.challenge)
            with self.assertRaises(PermissionError):
                v28.persist_gate_challenge_once(path, self.challenge)

    def test_v28_14_noncanonical_persisted_challenge_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "challenge.json"
            path.write_text(json.dumps(self.challenge, indent=2), encoding="utf-8")
            with self.assertRaises(PermissionError):
                v28.load_persisted_gate_challenge(path)

    def test_v28_15_approval_proof_binds_challenge_id_and_nonce(self):
        self.assertEqual(self.artifact["challenge_id"], self.challenge["challenge_id"])
        self.assertEqual(self.artifact["gate_nonce"], NONCE_A)
        self.assertEqual(self.artifact["candidate_sha256"], self.candidate["authorization_candidate_sha256"])

    def test_v28_16_approval_proof_authorizes_nothing(self):
        self.assertFalse(self.artifact["execution_authorized"])
        self.assertFalse(self.artifact["model_run_authorized"])
        self.assertFalse(self.artifact["model_contact_authorized"])
        self.assertFalse(self.artifact["authorization_consumed"])
        self.assertTrue(self.artifact["requires_atomic_gate_claim"])

    def test_v28_17_wrong_secret_rejects_approval_proof(self):
        with self.assertRaises(PermissionError):
            v28.validate_gate_approval_proof_preview(
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_B,
            )

    def test_v28_18_tampered_proof_rejected(self):
        tampered = deepcopy(self.artifact)
        tampered["approval_proof_hmac_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            v28.validate_gate_approval_proof_preview(
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=tampered,
                approval_secret=SECRET_A,
            )

    def test_v28_19_cross_nonce_replay_rejected(self):
        challenge_b = v28.build_gate_challenge_preview(
            candidate=self.candidate,
            approval_secret=SECRET_A,
            nonce=NONCE_B,
        )
        with self.assertRaises(PermissionError):
            v28.validate_gate_approval_proof_preview(
                candidate=self.candidate,
                persisted_challenge=challenge_b,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )

    def test_v28_20_six_field_v26_edit_still_fails_before_gate(self):
        edited = deepcopy(self.candidate)
        edited["status"] = "EXPLICIT_USER_APPROVED"
        edited["execution_authorized"] = True
        edited["model_run_authorized"] = True
        edited["model_contact_authorized"] = True
        edited["live_runner_version"] = edited["bound_v25_live_runner_version"]
        edited["live_run_type"] = edited["bound_v25_live_run_type"]
        with self.assertRaises(PermissionError):
            v28.build_gate_challenge_preview(
                candidate=edited,
                approval_secret=SECRET_A,
                nonce=NONCE_A,
            )

    def test_v28_21_atomic_claim_succeeds_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim_path = Path(tmp) / "claim.json"
            claim = v28.claim_gate_once_preview(
                claim_path=claim_path,
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )
            self.assertTrue(claim_path.is_file())
            self.assertTrue(claim["challenge_claimed"])
            self.assertTrue(claim["approval_proof_validated"])

    def test_v28_22_atomic_claim_replay_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim_path = Path(tmp) / "claim.json"
            v28.claim_gate_once_preview(
                claim_path=claim_path,
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )
            with self.assertRaises(PermissionError):
                v28.claim_gate_once_preview(
                    claim_path=claim_path,
                    candidate=self.candidate,
                    persisted_challenge=self.challenge,
                    artifact=self.artifact,
                    approval_secret=SECRET_A,
                )

    def test_v28_23_claim_remains_non_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim = v28.claim_gate_once_preview(
                claim_path=Path(tmp) / "claim.json",
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )
            self.assertFalse(claim["execution_authorized"])
            self.assertFalse(claim["model_run_authorized"])
            self.assertFalse(claim["model_contact_authorized"])
            self.assertFalse(claim["ready_for_model_contact"])
            self.assertTrue(claim["requires_separate_run_authorization_transform"])

    def test_v28_24_secret_not_written_to_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim_path = Path(tmp) / "claim.json"
            v28.claim_gate_once_preview(
                claim_path=claim_path,
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )
            self.assertNotIn(SECRET_A, claim_path.read_text(encoding="utf-8"))

    def test_v28_25_report_is_model_free_and_non_authorizing(self):
        report = v28.build_gate_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])
        self.assertFalse(report["model_qualified"])

    def test_v28_26_report_persists_nothing(self):
        report = v28.build_gate_report()
        self.assertFalse(report["challenge_persisted_by_report"])
        self.assertFalse(report["approval_proof_persisted_by_report"])
        self.assertFalse(report["gate_claim_persisted_by_report"])
        self.assertFalse(report["approval_secret_generated_by_report"])
        self.assertFalse(report["approval_secret_stored"])

    def test_v28_27_no_transport_execute_or_preflight_helper(self):
        self.assertFalse(hasattr(v28, "_default_transport"))
        self.assertFalse(hasattr(v28, "execute_once"))
        self.assertFalse(hasattr(v28, "preflight"))
        self.assertFalse(hasattr(v28, "approve_and_execute"))


if __name__ == "__main__":
    unittest.main()
