from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31

SECRET = "V31-SYNTHETIC-ONLY-SECRET-" + ("C" * 40)
NONCE = "5" * 64
AUTHORITY_PATH = r"C:\ZS_KI_B_AUTHORITY\authoritative_state.json"
ANCHOR_FP = "a" * 64
RUNNER_OID = "b" * 40


class SemV31AuthorityStateAtomicConsumePrepTests(unittest.TestCase):
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
        cls.gate = v30.build_proof_gate_envelope_preview(
            candidate=cls.candidate,
            challenge=cls.challenge,
            artifact=cls.artifact,
            claim=cls.claim,
            v29_preview=cls.v29_preview,
            approval_secret=SECRET,
        )
        cls.contract = v31.build_authority_state_contract_preview(
            authority_state_path=AUTHORITY_PATH,
            trust_anchor_id="V31-SYNTHETIC-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP,
            durable_claim_record_id="V31-SYNTHETIC-CLAIM-001",
            consume_record_id="V31-SYNTHETIC-CONSUME-001",
            final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        cls.request = v31.build_explicit_run_approval_request_preview(
            gate_envelope=cls.gate,
            authority_contract=cls.contract,
        )

    def _validate_request(self, request):
        return v31.validate_explicit_run_approval_request_preview(
            request,
            gate_envelope=self.gate,
            authority_contract=self.contract,
        )

    def test_v31_01_contract_is_non_authoritative(self):
        self.assertEqual(self.contract["status"], "AUTHORITY_STATE_CONTRACT_PREVIEW_NOT_VERIFIED")
        self.assertFalse(self.contract["authoritative_external_anchor_verified"])
        self.assertFalse(self.contract["explicit_user_approval_recorded"])

    def test_v31_02_contract_requires_external_absolute_path(self):
        with self.assertRaises(PermissionError):
            v31.build_authority_state_contract_preview(
                authority_state_path="relative/state.json",
                trust_anchor_id="x",
                trust_anchor_fingerprint_sha256=ANCHOR_FP,
                durable_claim_record_id="c",
                consume_record_id="u",
                final_main_commit=v31.BASE_MAIN_COMMIT,
                final_runner_blob_oid=RUNNER_OID,
            )

    def test_v31_03_repo_local_path_rejected(self):
        repo_local = str(v31.ROOT / "state" / "authority.json")
        with self.assertRaises(PermissionError):
            v31.build_authority_state_contract_preview(
                authority_state_path=repo_local,
                trust_anchor_id="x",
                trust_anchor_fingerprint_sha256=ANCHOR_FP,
                durable_claim_record_id="c",
                consume_record_id="u",
                final_main_commit=v31.BASE_MAIN_COMMIT,
                final_runner_blob_oid=RUNNER_OID,
            )

    def test_v31_04_bad_anchor_fingerprint_rejected(self):
        with self.assertRaises(PermissionError):
            v31.build_authority_state_contract_preview(
                authority_state_path=AUTHORITY_PATH,
                trust_anchor_id="x",
                trust_anchor_fingerprint_sha256="bad",
                durable_claim_record_id="c",
                consume_record_id="u",
                final_main_commit=v31.BASE_MAIN_COMMIT,
                final_runner_blob_oid=RUNNER_OID,
            )

    def test_v31_05_contract_validates_exact(self):
        self.assertEqual(v31.validate_authority_state_contract_preview(self.contract), self.contract)

    def test_v31_06_contract_positive_flag_escalation_rejected(self):
        for key in (
            "authoritative_external_anchor_verified",
            "authority_state_persistence_verified",
            "durable_single_use_claim_verified",
            "atomic_consume_implemented",
            "explicit_user_approval_recorded",
            "execution_authorized",
            "model_run_authorized",
            "model_contact_authorized",
        ):
            tampered = deepcopy(self.contract)
            tampered[key] = True
            with self.subTest(key=key):
                with self.assertRaises(PermissionError):
                    v31.validate_authority_state_contract_preview(tampered)

    def test_v31_07_hash_recompute_cannot_hide_contract_escalation(self):
        tampered = deepcopy(self.contract)
        tampered["authoritative_external_anchor_verified"] = True
        tampered["contract_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "contract_sha256"})
        with self.assertRaises(PermissionError):
            v31.validate_authority_state_contract_preview(tampered)

    def test_v31_08_storage_semantics_tamper_rejected(self):
        tampered = deepcopy(self.contract)
        tampered["required_storage_semantics"] = "MUTABLE_FILESYSTEM"
        tampered["contract_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "contract_sha256"})
        with self.assertRaises(PermissionError):
            v31.validate_authority_state_contract_preview(tampered)

    def test_v31_09_approval_request_waits_for_separate_user_approval(self):
        self.assertEqual(self.request["status"], "AWAITING_SEPARATE_EXPLICIT_USER_RUN_APPROVAL")
        self.assertFalse(self.request["explicit_user_approval_recorded"])
        self.assertFalse(self.request["execution_authorized"])

    def test_v31_10_approval_request_scope_is_one_run_no_retry(self):
        self.assertEqual(
            self.request["approval_scope"],
            "EXACTLY_ONE_SYNTHETIC_MODEL_RUN_NO_RETRY_NO_RERUN_NO_REPAIR",
        )

    def test_v31_11_approval_request_binds_v30_and_contract(self):
        self.assertEqual(self.request["source_v30_gate_envelope_sha256"], self.gate["proof_gate_envelope_sha256"])
        self.assertEqual(self.request["source_authority_contract_sha256"], self.contract["contract_sha256"])

    def test_v31_12_approval_request_validates_exact(self):
        self.assertEqual(self._validate_request(self.request), self.request)

    def test_v31_13_manual_approval_escalation_rejected(self):
        tampered = deepcopy(self.request)
        tampered["explicit_user_approval_recorded"] = True
        tampered["approval_request_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "approval_request_sha256"})
        with self.assertRaises(PermissionError):
            self._validate_request(tampered)

    def test_v31_14_manual_model_contact_escalation_rejected(self):
        tampered = deepcopy(self.request)
        tampered["model_contact_authorized"] = True
        tampered["approval_request_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "approval_request_sha256"})
        with self.assertRaises(PermissionError):
            self._validate_request(tampered)

    def test_v31_15_scope_widening_rejected(self):
        tampered = deepcopy(self.request)
        tampered["approval_scope"] = "UNLIMITED_RUNS"
        tampered["approval_request_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "approval_request_sha256"})
        with self.assertRaises(PermissionError):
            self._validate_request(tampered)

    def test_v31_16_v25_binding_tamper_rejected(self):
        tampered = deepcopy(self.request)
        tampered["requested_v25_binding"]["model"] = "tampered-model"
        with self.assertRaises(PermissionError):
            self._validate_request(tampered)

    def test_v31_17_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V31 remains non-live"):
            v31.reject_any_live_use(
                gate_envelope=self.gate,
                authority_contract=self.contract,
                approval_request=self.request,
            )

    def test_v31_18_final_git_bindings_are_frozen_in_request(self):
        self.assertEqual(self.request["requested_final_main_commit"], v31.BASE_MAIN_COMMIT)
        self.assertEqual(self.request["requested_final_runner_blob_oid"], RUNNER_OID)

    def test_v31_19_report_is_model_free(self):
        report = v31.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authoritative_external_anchor_verified"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["atomic_consume_implemented"])
        self.assertFalse(report["model_contact_performed"])

    def test_v31_20_no_positive_live_or_execution_helpers(self):
        self.assertFalse(hasattr(v31, "materialize_live_authorization"))
        self.assertFalse(hasattr(v31, "_default_transport"))
        self.assertFalse(hasattr(v31, "_default_preflight"))
        self.assertFalse(hasattr(v31, "execute_once"))
        self.assertFalse(hasattr(v31, "approve"))

    def test_v31_21_self_consistent_v25_scope_forgery_rejected(self):
        tampered = deepcopy(self.request)
        tampered["requested_v25_binding"]["model"] = "attacker-selected-model"
        tampered["requested_v25_binding_sha256"] = v31._sha256_payload(tampered["requested_v25_binding"])
        tampered["approval_request_sha256"] = v31._sha256_payload(
            {k: v for k, v in tampered.items() if k != "approval_request_sha256"}
        )
        with self.assertRaisesRegex(PermissionError, "canonical V30 binding"):
            self._validate_request(tampered)

    def test_v31_22_unknown_contract_field_rejected_even_with_rehash(self):
        tampered = deepcopy(self.contract)
        tampered["backdoor_field_not_checked"] = True
        tampered["contract_sha256"] = v31._sha256_payload({k: v for k, v in tampered.items() if k != "contract_sha256"})
        with self.assertRaisesRegex(PermissionError, "keyset mismatch"):
            v31.validate_authority_state_contract_preview(tampered)

    def test_v31_23_unknown_approval_field_rejected_even_with_rehash(self):
        tampered = deepcopy(self.request)
        tampered["backdoor_field_not_checked"] = True
        tampered["approval_request_sha256"] = v31._sha256_payload(
            {k: v for k, v in tampered.items() if k != "approval_request_sha256"}
        )
        with self.assertRaisesRegex(PermissionError, "keyset mismatch"):
            self._validate_request(tampered)

    def test_v31_24_isolated_approval_request_rejected_without_sources(self):
        with self.assertRaisesRegex(PermissionError, "requires exact source objects"):
            v31.validate_explicit_run_approval_request_preview(self.request)

    def test_v31_25_source_hash_substitution_rejected_even_with_rehash(self):
        tampered = deepcopy(self.request)
        tampered["source_v30_gate_envelope_sha256"] = "0" * 64
        tampered["approval_request_sha256"] = v31._sha256_payload(
            {k: v for k, v in tampered.items() if k != "approval_request_sha256"}
        )
        with self.assertRaisesRegex(PermissionError, "V30 source binding mismatch"):
            self._validate_request(tampered)


if __name__ == "__main__":
    unittest.main()
