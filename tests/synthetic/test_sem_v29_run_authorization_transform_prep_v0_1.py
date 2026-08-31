from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28


SECRET_A = "A" * 40
SECRET_B = "B" * 40
NONCE_A = "3" * 64


class SemV29RunAuthorizationTransformPrepTests(unittest.TestCase):
    def setUp(self):
        self.candidate = v29.build_candidate_snapshot()
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
        self.anchor = v29.build_trust_anchor_preview(candidate=self.candidate, challenge=self.challenge)
        with tempfile.TemporaryDirectory() as tmp:
            claim_path = Path(tmp) / "claim.json"
            self.claim = v28.claim_gate_once_preview(
                claim_path=claim_path,
                candidate=self.candidate,
                persisted_challenge=self.challenge,
                artifact=self.artifact,
                approval_secret=SECRET_A,
            )
        self.preview = v29.build_run_authorization_preview(
            candidate=self.candidate,
            challenge=self.challenge,
            artifact=self.artifact,
            claim=self.claim,
            trust_anchor_preview=self.anchor,
            approval_secret=SECRET_A,
        )

    def test_v29_01_candidate_remains_awaiting_approval(self):
        self.assertEqual(self.candidate["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(self.candidate["execution_authorized"])

    def test_v29_02_trust_anchor_preview_is_not_authoritative(self):
        self.assertFalse(self.anchor["authoritative_external_anchor"])
        self.assertFalse(self.anchor["explicit_user_approval_recorded"])
        self.assertFalse(self.anchor["model_contact_authorized"])

    def test_v29_03_anchor_binds_challenge_and_candidate(self):
        self.assertEqual(self.anchor["challenge_id"], self.challenge["challenge_id"])
        self.assertEqual(self.anchor["candidate_sha256"], self.candidate["authorization_candidate_sha256"])
        self.assertEqual(self.anchor["bound_main_commit"], self.candidate["bound_main_commit"])

    def test_v29_04_anchor_candidate_mismatch_rejected(self):
        tampered = deepcopy(self.challenge)
        tampered["candidate_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            v29.build_trust_anchor_preview(candidate=self.candidate, challenge=tampered)

    def test_v29_05_exact_claim_receipt_validates(self):
        out = v29.validate_claim_receipt(
            candidate=self.candidate,
            challenge=self.challenge,
            artifact=self.artifact,
            claim=self.claim,
            approval_secret=SECRET_A,
        )
        self.assertEqual(out, self.claim)

    def test_v29_06_wrong_secret_rejects_claim_chain(self):
        with self.assertRaises(PermissionError):
            v29.validate_claim_receipt(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=self.claim,
                approval_secret=SECRET_B,
            )

    def test_v29_07_tampered_claim_challenge_id_rejected(self):
        tampered = deepcopy(self.claim)
        tampered["challenge_id"] = "0" * 64
        with self.assertRaises(PermissionError):
            v29.validate_claim_receipt(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=tampered,
                approval_secret=SECRET_A,
            )

    def test_v29_08_tampered_claim_proof_rejected(self):
        tampered = deepcopy(self.claim)
        tampered["approval_proof_hmac_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            v29.validate_claim_receipt(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=tampered,
                approval_secret=SECRET_A,
            )

    def test_v29_09_claim_authorization_escalation_rejected(self):
        tampered = deepcopy(self.claim)
        tampered["model_contact_authorized"] = True
        with self.assertRaises(PermissionError):
            v29.validate_claim_receipt(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=tampered,
                approval_secret=SECRET_A,
            )

    def test_v29_10_preview_binds_v25_template_fields(self):
        self.assertEqual(self.preview["max_tokens"], 2048)
        self.assertEqual(self.preview["required_base_url"], self.candidate["required_base_url"])
        self.assertEqual(self.preview["model"], self.candidate["model"])
        self.assertEqual(self.preview["prompt_sha256"], self.candidate["prompt_sha256"])
        self.assertEqual(self.preview["response_format_sha256"], self.candidate["response_format_sha256"])

    def test_v29_11_preview_binds_source_chain(self):
        self.assertEqual(self.preview["source_candidate_sha256"], self.candidate["authorization_candidate_sha256"])
        self.assertEqual(self.preview["source_challenge_id"], self.challenge["challenge_id"])
        self.assertEqual(self.preview["source_claim_version"], self.claim["claim_version"])
        self.assertEqual(self.preview["source_approval_proof_hmac_sha256"], self.artifact["approval_proof_hmac_sha256"])

    def test_v29_12_preview_authorizes_nothing(self):
        self.assertFalse(self.preview["execution_authorized"])
        self.assertFalse(self.preview["model_run_authorized"])
        self.assertFalse(self.preview["model_contact_authorized"])
        self.assertFalse(self.preview["ready_for_model_contact"])
        self.assertFalse(self.preview["model_qualified"])

    def test_v29_13_preview_records_no_user_approval(self):
        self.assertFalse(self.preview["explicit_user_approval_recorded"])
        self.assertFalse(self.preview["authoritative_external_anchor_verified"])
        self.assertTrue(self.preview["separate_explicit_approval_required"])

    def test_v29_14_preview_hash_validates(self):
        self.assertEqual(v29.validate_run_authorization_preview(self.preview), self.preview)

    def test_v29_15_preview_hash_tamper_rejected(self):
        tampered = deepcopy(self.preview)
        tampered["model"] = "tampered-model"
        with self.assertRaises(PermissionError):
            v29.validate_run_authorization_preview(tampered)

    def test_v29_16_preview_flag_escalation_rejected(self):
        for field in ("execution_authorized", "model_run_authorized", "model_contact_authorized", "ready_for_model_contact"):
            tampered = deepcopy(self.preview)
            tampered[field] = True
            with self.subTest(field=field):
                with self.assertRaises(PermissionError):
                    v29.validate_run_authorization_preview(tampered)

    def test_v29_17_v25_rejects_transform_preview(self):
        self.assertTrue(v29.v25_rejects_transform_preview(self.preview))

    def test_v29_18_self_escalated_preview_still_rejected_by_v25(self):
        tampered = deepcopy(self.preview)
        tampered.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        self.assertTrue(v29.v25_rejects_transform_preview(tampered))

    def test_v29_19_authoritative_anchor_in_preview_rejected(self):
        anchor = deepcopy(self.anchor)
        anchor["authoritative_external_anchor"] = True
        with self.assertRaises(PermissionError):
            v29.build_run_authorization_preview(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=self.claim,
                trust_anchor_preview=anchor,
                approval_secret=SECRET_A,
            )

    def test_v29_20_user_approval_in_preview_rejected(self):
        anchor = deepcopy(self.anchor)
        anchor["explicit_user_approval_recorded"] = True
        with self.assertRaises(PermissionError):
            v29.build_run_authorization_preview(
                candidate=self.candidate,
                challenge=self.challenge,
                artifact=self.artifact,
                claim=self.claim,
                trust_anchor_preview=anchor,
                approval_secret=SECRET_A,
            )

    def test_v29_21_canonical_loader_accepts_exact_and_rejects_pretty_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            exact = Path(tmp) / "exact.json"
            exact.write_bytes(v29._canonical_bytes(self.claim) + b"\n")
            self.assertEqual(v29.load_canonical_json(exact), self.claim)
            pretty = Path(tmp) / "pretty.json"
            import json
            pretty.write_text(json.dumps(self.claim, indent=2), encoding="utf-8")
            with self.assertRaises(PermissionError):
                v29.load_canonical_json(pretty)

    def test_v29_22_report_is_model_free(self):
        report = v29.build_transform_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["trust_anchor_created"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["run_authorization_created"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])

    def test_v29_23_report_authorizes_nothing(self):
        report = v29.build_transform_report()
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["ready_for_model_contact"])
        self.assertFalse(report["model_qualified"])

    def test_v29_24_no_transport_execute_preflight_or_approval_action(self):
        self.assertFalse(hasattr(v29, "_default_transport"))
        self.assertFalse(hasattr(v29, "execute_once"))
        self.assertFalse(hasattr(v29, "_default_preflight"))
        self.assertFalse(hasattr(v29, "approve_and_execute"))
        self.assertFalse(hasattr(v29, "approve"))


if __name__ == "__main__":
    unittest.main()
