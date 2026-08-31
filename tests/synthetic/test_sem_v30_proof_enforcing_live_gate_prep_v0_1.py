from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25


SECRET = "V30-SYNTHETIC-ONLY-SECRET-" + ("A" * 40)
NONCE = "4" * 64


class SemV30ProofEnforcingLiveGatePrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v29.build_candidate_snapshot()
        cls.challenge = v28.build_gate_challenge_preview(
            candidate=cls.candidate,
            approval_secret=SECRET,
            nonce=NONCE,
        )
        cls.artifact = v28.build_gate_approval_proof_preview(
            candidate=cls.candidate,
            persisted_challenge=cls.challenge,
            approval_secret=SECRET,
        )
        with tempfile.TemporaryDirectory() as tmp:
            cls.claim = v28.claim_gate_once_preview(
                claim_path=Path(tmp) / "claim.json",
                candidate=cls.candidate,
                persisted_challenge=cls.challenge,
                artifact=cls.artifact,
                approval_secret=SECRET,
            )
        cls.anchor = v29.build_trust_anchor_preview(candidate=cls.candidate, challenge=cls.challenge)
        cls.v29_preview = v29.build_run_authorization_preview(
            candidate=cls.candidate,
            challenge=cls.challenge,
            artifact=cls.artifact,
            claim=cls.claim,
            trust_anchor_preview=cls.anchor,
            approval_secret=SECRET,
        )
        cls.envelope = v30.build_proof_gate_envelope_preview(
            candidate=cls.candidate,
            challenge=cls.challenge,
            artifact=cls.artifact,
            claim=cls.claim,
            v29_preview=cls.v29_preview,
            approval_secret=SECRET,
        )

    def test_v30_01_envelope_is_non_live(self):
        self.assertFalse(self.envelope["execution_authorized"])
        self.assertFalse(self.envelope["model_run_authorized"])
        self.assertFalse(self.envelope["model_contact_authorized"])
        self.assertFalse(self.envelope["ready_for_model_contact"])

    def test_v30_02_full_provenance_is_bound(self):
        self.assertTrue(self.envelope["full_provenance_validated"])
        self.assertEqual(self.envelope["source_candidate_sha256"], self.candidate["authorization_candidate_sha256"])
        self.assertEqual(self.envelope["source_challenge_id"], self.challenge["challenge_id"])
        self.assertEqual(self.envelope["source_approval_proof_hmac_sha256"], self.artifact["approval_proof_hmac_sha256"])

    def test_v30_03_envelope_requires_future_authority_and_approval(self):
        self.assertTrue(self.envelope["requires_authoritative_trust_anchor"])
        self.assertTrue(self.envelope["requires_separate_explicit_user_approval"])
        self.assertTrue(self.envelope["requires_atomic_live_authorization_consume_before_contact"])
        self.assertTrue(self.envelope["v25_validation_alone_is_insufficient"])

    def test_v30_04_envelope_validates_exact(self):
        self.assertEqual(v30.validate_proof_gate_envelope_preview(self.envelope), self.envelope)

    def test_v30_05_envelope_flag_escalation_rejected(self):
        for key in (
            "authoritative_external_anchor_verified",
            "explicit_user_approval_recorded",
            "live_authorization_materialized",
            "execution_authorized",
            "model_run_authorized",
            "model_contact_authorized",
            "ready_for_model_contact",
        ):
            tampered = deepcopy(self.envelope)
            tampered[key] = True
            with self.subTest(key=key):
                with self.assertRaises(PermissionError):
                    v30.validate_proof_gate_envelope_preview(tampered)

    def test_v30_06_nested_v25_binding_tamper_rejected(self):
        tampered = deepcopy(self.envelope)
        tampered["proposed_v25_binding"]["model"] = "tampered-model"
        with self.assertRaises(PermissionError):
            v30.validate_proof_gate_envelope_preview(tampered)

    def test_v30_07_hash_recompute_does_not_hide_binding_tamper(self):
        tampered = deepcopy(self.envelope)
        tampered["proposed_v25_binding"]["model"] = "tampered-model"
        tampered["proposed_v25_binding_sha256"] = v30._sha256_payload(tampered["proposed_v25_binding"])
        tampered["proof_gate_envelope_sha256"] = v30._sha256_payload(
            {k: v for k, v in tampered.items() if k != "proof_gate_envelope_sha256"}
        )
        with self.assertRaises(PermissionError):
            v30.validate_proof_gate_envelope_preview(tampered)

    def test_v30_08_wrong_secret_rejects_full_provenance(self):
        with self.assertRaises(PermissionError):
            v30.validate_full_provenance(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=self.claim,
                v29_preview=self.v29_preview,
                approval_secret="WRONG-SECRET-" + ("B" * 40),
            )

    def test_v30_09_tampered_challenge_rejected(self):
        challenge = deepcopy(self.challenge)
        challenge["challenge_id"] = "0" * 64
        with self.assertRaises(PermissionError):
            v30.validate_full_provenance(
                candidate=self.candidate,
                challenge=challenge,
                artifact=self.artifact,
                claim=self.claim,
                v29_preview=self.v29_preview,
                approval_secret=SECRET,
            )

    def test_v30_10_tampered_proof_rejected(self):
        artifact = deepcopy(self.artifact)
        artifact["approval_proof_hmac_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            v30.validate_full_provenance(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=artifact,
                claim=self.claim,
                v29_preview=self.v29_preview,
                approval_secret=SECRET,
            )

    def test_v30_11_tampered_claim_rejected(self):
        claim = deepcopy(self.claim)
        claim["model_contact_authorized"] = True
        with self.assertRaises(PermissionError):
            v30.validate_full_provenance(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=claim,
                v29_preview=self.v29_preview,
                approval_secret=SECRET,
            )

    def test_v30_12_tampered_v29_preview_rejected(self):
        preview = deepcopy(self.v29_preview)
        preview["source_challenge_id"] = "0" * 64
        with self.assertRaises(PermissionError):
            v30.validate_full_provenance(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=self.claim,
                v29_preview=preview,
                approval_secret=SECRET,
            )

    def test_v30_13_known_v25_gap_still_reproducible_directly(self):
        authorization = deepcopy(self.v29_preview["proposed_v25_binding"])
        authorization.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        self.assertEqual(v25.validate_live_execution_authorization(authorization), authorization)

    def test_v30_14_same_bare_v25_object_rejected_by_v30(self):
        authorization = deepcopy(self.v29_preview["proposed_v25_binding"])
        authorization.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        self.assertTrue(v30.v30_rejects_bare_or_self_escalated_v25(authorization))

    def test_v30_15_valid_v25_plus_valid_non_live_envelope_still_rejected(self):
        authorization = deepcopy(self.v29_preview["proposed_v25_binding"])
        authorization.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        with self.assertRaisesRegex(PermissionError, "authoritative trust anchor"):
            v30.validate_live_authorization_through_proof_gate(
                authorization=authorization,
                gate_envelope=self.envelope,
            )

    def test_v30_16_runtime_binding_mismatch_rejected_before_final_block(self):
        authorization = deepcopy(self.v29_preview["proposed_v25_binding"])
        authorization["model"] = "tampered-model"
        authorization.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        with self.assertRaisesRegex(PermissionError, "runtime binding mismatch"):
            v30.validate_live_authorization_through_proof_gate(
                authorization=authorization,
                gate_envelope=self.envelope,
            )

    def test_v30_17_missing_envelope_rejected(self):
        with self.assertRaisesRegex(PermissionError, "requires provenance envelope"):
            v30.validate_live_authorization_through_proof_gate(
                authorization={},
                gate_envelope=None,
            )

    def test_v30_18_envelope_base_commit_bound(self):
        tampered = deepcopy(self.envelope)
        tampered["gate_base_main_commit"] = "0" * 40
        with self.assertRaises(PermissionError):
            v30.validate_proof_gate_envelope_preview(tampered)

    def test_v30_19_report_is_model_free_and_non_authorizing(self):
        report = v30.build_gate_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authoritative_trust_anchor_created"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["live_authorization_materialized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])

    def test_v30_20_no_positive_materializer_or_execution_helpers(self):
        self.assertFalse(hasattr(v30, "materialize_live_authorization"))
        self.assertFalse(hasattr(v30, "_default_transport"))
        self.assertFalse(hasattr(v30, "execute_once"))
        self.assertFalse(hasattr(v30, "_default_preflight"))
        self.assertFalse(hasattr(v30, "approve_and_execute"))
        self.assertFalse(hasattr(v30, "approve"))


if __name__ == "__main__":
    unittest.main()
