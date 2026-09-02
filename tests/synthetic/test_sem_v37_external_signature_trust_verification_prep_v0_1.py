from __future__ import annotations

import base64
import hashlib
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31
import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32
import scripts.zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep as v33
import scripts.zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep as v34
import scripts.zs_ki_b_sem_external_attestation_global_single_use_v3_5_prep as v35
import scripts.zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep as v36
import scripts.zs_ki_b_sem_external_signature_trust_verification_v3_7_prep as v37

SECRET = "V37-SYNTHETIC-ONLY-SECRET-" + ("A" * 40)
NONCE = "7" * 64
RUNNER_OID = "3" * 40


class SemV37ExternalSignatureTrustVerificationPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v29.build_candidate_snapshot()
        cls.challenge = v28.build_gate_challenge_preview(candidate=cls.candidate, approval_secret=SECRET, nonce=NONCE)
        cls.artifact = v28.build_gate_approval_proof_preview(
            candidate=cls.candidate, persisted_challenge=cls.challenge, approval_secret=SECRET
        )
        with tempfile.TemporaryDirectory() as tmp:
            cls.claim = v28.claim_gate_once_preview(
                claim_path=Path(tmp) / "claim.json", candidate=cls.candidate,
                persisted_challenge=cls.challenge, artifact=cls.artifact, approval_secret=SECRET,
            )
        cls.anchor = v29.build_trust_anchor_preview(candidate=cls.candidate, challenge=cls.challenge)
        cls.v29_preview = v29.build_run_authorization_preview(
            candidate=cls.candidate, challenge=cls.challenge, artifact=cls.artifact,
            claim=cls.claim, trust_anchor_preview=cls.anchor, approval_secret=SECRET,
        )
        cls.gate = v30.build_proof_gate_envelope_preview(
            candidate=cls.candidate, challenge=cls.challenge, artifact=cls.artifact,
            claim=cls.claim, v29_preview=cls.v29_preview, approval_secret=SECRET,
        )

    def _bundle(self, root: Path):
        authority_path = root / "authority" / "state.json"
        contract31 = v31.build_authority_state_contract_preview(
            authority_state_path=str(authority_path.resolve()), trust_anchor_id="V37-ANCHOR-001",
            trust_anchor_fingerprint_sha256="a" * 64, durable_claim_record_id="V37-CLAIM-001",
            consume_record_id="V37-CONSUME-001", final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        external = v32.build_external_state_resolution_preview(authority_contract=contract31)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V37-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract31["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract31["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        payload = b"synthetic signed authority evidence bytes\n"
        evidence_path = root / "external-evidence.bin"
        evidence_path.write_bytes(payload)
        evidence = v35.build_external_evidence_reference_preview(
            authority_binding=binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_path=str(evidence_path.resolve()), evidence_id="V37-EVIDENCE-001",
            expected_evidence_sha256=hashlib.sha256(payload).hexdigest(),
        )
        global_binding = v35.build_global_store_binding_preview(
            authority_binding=binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_reference=evidence, global_store_binding_id="V37-GLOBAL-STORE-001",
        )
        public_key = b"synthetic-public-key-material-v37"
        key_fp = hashlib.sha256(public_key).hexdigest()
        attestation = v36.build_attestation_verification_contract_preview(
            global_store_binding=global_binding, evidence_reference=evidence, authority_binding=binding,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
            verifier_id="V37-VERIFIER-001", verifier_key_id="V37-KEY-001",
            verifier_key_fingerprint_sha256=key_fp, signature_algorithm="ED25519",
        )
        sources = dict(
            global_store_binding=global_binding, evidence_reference=evidence, authority_binding=binding,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        signature = b"synthetic-signature-bytes-not-cryptographically-verified"
        request = v37.build_crypto_verification_request_preview(
            attestation_contract=attestation,
            public_key_b64=base64.b64encode(public_key).decode("ascii"),
            signature_b64=base64.b64encode(signature).decode("ascii"),
            signed_payload_b64=base64.b64encode(payload).decode("ascii"),
            **sources,
        )
        result = v37.build_unverified_crypto_result_preview(
            verification_request=request, attestation_contract=attestation, **sources
        )
        return sources, attestation, public_key, payload, signature, request, result

    def test_v37_01_request_binds_inputs_without_verifying(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, request, _ = self._bundle(Path(tmp))
            self.assertTrue(request["cryptographic_backend_required"])
            self.assertFalse(request["cryptographic_verification_performed"])
            self.assertFalse(request["external_signature_verified"])

    def test_v37_02_result_remains_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, _, result = self._bundle(Path(tmp))
            self.assertFalse(result["cryptographic_backend_present"])
            self.assertFalse(result["external_authority_attested"])
            self.assertFalse(result["model_run_authorized"])

    def test_v37_03_wrong_public_key_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, payload, signature, _, _ = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v37.build_crypto_verification_request_preview(
                    attestation_contract=attestation,
                    public_key_b64=base64.b64encode(b"different-key").decode("ascii"),
                    signature_b64=base64.b64encode(signature).decode("ascii"),
                    signed_payload_b64=base64.b64encode(payload).decode("ascii"), **sources,
                )

    def test_v37_04_wrong_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, public_key, _, signature, _, _ = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v37.build_crypto_verification_request_preview(
                    attestation_contract=attestation,
                    public_key_b64=base64.b64encode(public_key).decode("ascii"),
                    signature_b64=base64.b64encode(signature).decode("ascii"),
                    signed_payload_b64=base64.b64encode(b"changed").decode("ascii"), **sources,
                )

    def test_v37_05_signature_bytes_are_hash_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, public_key, payload, _, request, _ = self._bundle(Path(tmp))
            other = v37.build_crypto_verification_request_preview(
                attestation_contract=attestation,
                public_key_b64=base64.b64encode(public_key).decode("ascii"),
                signature_b64=base64.b64encode(b"other-signature").decode("ascii"),
                signed_payload_b64=base64.b64encode(payload).decode("ascii"), **sources,
            )
            self.assertNotEqual(request["signature_sha256"], other["signature_sha256"])
            self.assertFalse(other["external_signature_verified"])

    def test_v37_06_invalid_base64_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, payload, signature, _, _ = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v37.build_crypto_verification_request_preview(
                    attestation_contract=attestation, public_key_b64="not***base64",
                    signature_b64=base64.b64encode(signature).decode("ascii"),
                    signed_payload_b64=base64.b64encode(payload).decode("ascii"), **sources,
                )

    def test_v37_07_request_extra_field_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, _, _, request, _ = self._bundle(Path(tmp))
            tampered = deepcopy(request)
            tampered["approved"] = True
            tampered["verification_request_sha256"] = v37._sha256_payload(
                {k: v for k, v in tampered.items() if k != "verification_request_sha256"}
            )
            with self.assertRaises(PermissionError):
                v37.validate_crypto_verification_request_preview(tampered, attestation_contract=attestation, **sources)

    def test_v37_08_request_live_escalation_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, _, _, request, _ = self._bundle(Path(tmp))
            tampered = deepcopy(request)
            tampered["external_signature_verified"] = True
            tampered["verification_request_sha256"] = v37._sha256_payload(
                {k: v for k, v in tampered.items() if k != "verification_request_sha256"}
            )
            with self.assertRaises(PermissionError):
                v37.validate_crypto_verification_request_preview(tampered, attestation_contract=attestation, **sources)

    def test_v37_09_result_live_escalation_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, _, _, request, result = self._bundle(Path(tmp))
            tampered = deepcopy(result)
            tampered["model_contact_authorized"] = True
            tampered["verification_result_sha256"] = v37._sha256_payload(
                {k: v for k, v in tampered.items() if k != "verification_result_sha256"}
            )
            with self.assertRaises(PermissionError):
                v37.validate_unverified_crypto_result_preview(
                    tampered, verification_request=request, attestation_contract=attestation, **sources
                )

    def test_v37_10_attestation_contract_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, _, _, request, _ = self._bundle(Path(tmp))
            tampered_contract = deepcopy(attestation)
            tampered_contract["verifier_key_id"] = "V37-KEY-OTHER"
            tampered_contract["attestation_contract_sha256"] = v36._sha256_payload(
                {k: v for k, v in tampered_contract.items() if k != "attestation_contract_sha256"}
            )
            with self.assertRaises(PermissionError):
                v37.validate_crypto_verification_request_preview(
                    request, attestation_contract=tampered_contract, **sources
                )

    def test_v37_11_bool_type_attack_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, attestation, _, _, _, request, _ = self._bundle(Path(tmp))
            tampered = deepcopy(request)
            tampered["cryptographic_verification_performed"] = 1
            tampered["verification_request_sha256"] = v37._sha256_payload(
                {k: v for k, v in tampered.items() if k != "verification_request_sha256"}
            )
            with self.assertRaises(PermissionError):
                v37.validate_crypto_verification_request_preview(tampered, attestation_contract=attestation, **sources)

    def test_v37_12_algorithm_is_inherited_from_v36_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, attestation, _, _, _, request, _ = self._bundle(Path(tmp))
            self.assertEqual(request["signature_algorithm"], attestation["signature_algorithm"])

    def test_v37_13_no_crypto_backend_helper_present(self):
        self.assertFalse(hasattr(v37, "verify_signature"))
        self.assertFalse(hasattr(v37, "materialize_live_authorization"))
        self.assertFalse(hasattr(v37, "execute_once"))

    def test_v37_14_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V37 has no cryptographic backend"):
            v37.reject_any_live_use()

    def test_v37_15_report_is_non_authorizing(self):
        report = v37.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        for key in (
            "cryptographic_backend_present", "cryptographic_verification_performed",
            "external_signature_verified", "external_authority_attested", "external_trust_anchor_verified",
            "explicit_user_approval_recorded", "authorization_consumed", "execution_authorized",
            "model_run_authorized", "model_contact_authorized", "model_qualified",
        ):
            self.assertFalse(report[key])

    def test_v37_16_statuses_are_explicitly_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, request, result = self._bundle(Path(tmp))
            self.assertIn("NOT_VERIFIED", request["status"])
            self.assertIn("NOT_VERIFIED", result["status"])


if __name__ == "__main__":
    unittest.main()
