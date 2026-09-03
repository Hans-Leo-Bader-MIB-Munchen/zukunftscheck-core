from __future__ import annotations

import hashlib
import subprocess
import sys
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
import scripts.zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep as v41

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

SECRET = "V41-SYNTHETIC-ONLY-SECRET-" + ("A" * 40)
NONCE = "8" * 64
RUNNER_OID = "3" * 40


class TestSemV41ExternalSignatureTrustAnchorBindingPrep(unittest.TestCase):
    MESSAGE = b"ZS-KI-B V41 synthetic external authority evidence\n"

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

    @staticmethod
    def der(public_key):
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def _bundle(self, root: Path, public_key_der: bytes, algorithm: str, *, verifier_fp: str | None = None):
        key_fp = hashlib.sha256(public_key_der).hexdigest()
        authority_path = root / "authority" / "state.json"
        contract31 = v31.build_authority_state_contract_preview(
            authority_state_path=str(authority_path.resolve()), trust_anchor_id="V41-ANCHOR-001",
            trust_anchor_fingerprint_sha256=key_fp, durable_claim_record_id="V41-CLAIM-001",
            consume_record_id="V41-CONSUME-001", final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        external = v32.build_external_state_resolution_preview(authority_contract=contract31)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V41-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract31["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract31["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        authority_binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        evidence_path = root / "external-evidence.bin"
        evidence_path.write_bytes(self.MESSAGE)
        evidence = v35.build_external_evidence_reference_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_path=str(evidence_path.resolve()), evidence_id="V41-EVIDENCE-001",
            expected_evidence_sha256=hashlib.sha256(self.MESSAGE).hexdigest(),
        )
        global_binding = v35.build_global_store_binding_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_reference=evidence, global_store_binding_id="V41-GLOBAL-STORE-001",
        )
        attestation = v36.build_attestation_verification_contract_preview(
            global_store_binding=global_binding, evidence_reference=evidence, authority_binding=authority_binding,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
            verifier_id="V41-VERIFIER-001", verifier_key_id="V41-KEY-001",
            verifier_key_fingerprint_sha256=verifier_fp or key_fp, signature_algorithm=algorithm,
        )
        sources = dict(
            global_store_binding=global_binding, evidence_reference=evidence,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        return sources, authority_binding, attestation

    def _binding(self, root: Path, public_key_der: bytes, algorithm: str):
        sources, authority_binding, attestation = self._bundle(root, public_key_der, algorithm)
        binding = v41.build_direct_signer_trust_binding_preview(
            attestation_contract=attestation, authority_binding=authority_binding, **sources
        )
        return sources, authority_binding, attestation, binding

    def test_01_base_and_predecessor_source_bindings_exact(self):
        self.assertEqual(v41.BASE_MAIN_COMMIT, "a5f943a56c8e5f8532db36a642f610e1914c2f6b")
        self.assertEqual(v41.SOURCE_V34_SCRIPT_BLOB_SHA, "02fc1ffe52b05ee46d5a7933c5b5e7e308c92cfe")
        self.assertEqual(v41.SOURCE_V35_SCRIPT_BLOB_SHA, "4e40f078585ef67b28aa55e923f5d76c05d4e93b")
        self.assertEqual(v41.SOURCE_V36_SCRIPT_BLOB_SHA, "a794a179f0d83bd1cde9823cdee535ce4ba01ccb")
        self.assertEqual(v41.SOURCE_V40_SCRIPT_BLOB_SHA, "20ac072ba529f92fc72590ef7852547f162250f1")
        self.assertEqual(set(v41._validate_sources_before_import()), {"V34", "V35", "V36", "V40"})

    def test_02_supported_algorithms_exact(self):
        self.assertEqual(v41.SUPPORTED_ALGORITHMS, frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"}))

    def test_03_binding_revalidates_v34_v36_chain_without_trust_escalation(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, binding = self._binding(Path(tmp), self.der(private.public_key()), "ED25519")
        self.assertTrue(binding["v36_attestation_contract_revalidated"])
        self.assertTrue(binding["v34_authority_binding_revalidated"])
        self.assertTrue(binding["verifier_key_equals_trust_anchor_pin"])
        for key in ("pin_external_provenance_verified", "external_authority_attested", "external_trust_anchor_verified",
                    "execution_authorized", "model_run_authorized", "model_contact_authorized",
                    "ready_for_model_contact", "model_qualified"):
            self.assertIs(binding[key], False)

    def test_04_self_chosen_verifier_key_not_matching_v34_anchor_rejected(self):
        signer = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation = self._bundle(
                Path(tmp), self.der(signer.public_key()), "ED25519",
                verifier_fp=hashlib.sha256(self.der(other.public_key())).hexdigest(),
            )
            with self.assertRaises(PermissionError):
                v41.build_direct_signer_trust_binding_preview(
                    attestation_contract=attestation, authority_binding=authority_binding, **sources
                )

    def test_05_binding_exact_keyset_and_rehash_tamper_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), self.der(private.public_key()), "ED25519")
            tampered = dict(binding)
            tampered["verifier_id"] = "ATTACKER"
            tampered["binding_sha256"] = v41._sha256_payload({k: v for k, v in tampered.items() if k != "binding_sha256"})
            with self.assertRaises(PermissionError):
                v41.validate_direct_signer_trust_binding_preview(
                    tampered, attestation_contract=attestation, authority_binding=authority_binding, **sources
                )
            extra = dict(binding)
            extra["approved"] = True
            with self.assertRaises(PermissionError):
                v41.validate_direct_signer_trust_binding_preview(
                    extra, attestation_contract=attestation, authority_binding=authority_binding, **sources
                )

    def test_06_attestation_contract_substitution_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), self.der(private.public_key()), "ED25519")
            bad = deepcopy(attestation)
            bad["verifier_id"] = "ATTACKER"
            bad["attestation_contract_sha256"] = v36._sha256_payload({k: v for k, v in bad.items() if k != "attestation_contract_sha256"})
            with self.assertRaises(PermissionError):
                v41.validate_direct_signer_trust_binding_preview(
                    binding, attestation_contract=bad, authority_binding=authority_binding, **sources
                )

    def test_07_ed25519_signature_valid_for_contracted_payload(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            result = v41.verify_external_signature_against_direct_anchor(
                binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                public_key_der=der, message=self.MESSAGE, signature=private.sign(self.MESSAGE), **sources)
        self.assertTrue(result["external_signature_verified"])
        self.assertTrue(result["signed_payload_contract_match_verified"])

    def test_08_ecdsa_signature_valid_for_contracted_payload(self):
        private = ec.generate_private_key(ec.SECP256R1())
        der = self.der(private.public_key())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA256()))
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ECDSA-P256-SHA256")
            result = v41.verify_external_signature_against_direct_anchor(
                binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                public_key_der=der, message=self.MESSAGE, signature=sig, **sources)
        self.assertTrue(result["external_signature_verified"])

    def test_09_rsa_signature_valid_for_contracted_payload(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        der = self.der(private.public_key())
        sig = private.sign(self.MESSAGE, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "RSA-PSS-SHA256")
            result = v41.verify_external_signature_against_direct_anchor(
                binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                public_key_der=der, message=self.MESSAGE, signature=sig, **sources)
        self.assertTrue(result["external_signature_verified"])

    def test_10_wrong_public_key_rejected_before_crypto(self):
        signer = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        signer_der = self.der(signer.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), signer_der, "ED25519")
            with self.assertRaises(PermissionError):
                v41.verify_external_signature_against_direct_anchor(
                    binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                    public_key_der=self.der(other.public_key()), message=self.MESSAGE,
                    signature=signer.sign(self.MESSAGE), **sources)

    def test_11_noncontracted_payload_rejected_even_if_correctly_signed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        other_message = b"attacker-selected but correctly signed payload"
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            with self.assertRaises(PermissionError):
                v41.verify_external_signature_against_direct_anchor(
                    binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                    public_key_der=der, message=other_message, signature=private.sign(other_message), **sources)

    def test_12_wrong_signature_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            with self.assertRaises(PermissionError):
                v41.verify_external_signature_against_direct_anchor(
                    binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                    public_key_der=der, message=self.MESSAGE, signature=other.sign(self.MESSAGE), **sources)

    def test_13_algorithm_key_type_mismatch_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ECDSA-P256-SHA256")
            with self.assertRaises(PermissionError):
                v41.verify_external_signature_against_direct_anchor(
                    binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                    public_key_der=der, message=self.MESSAGE, signature=private.sign(self.MESSAGE), **sources)

    def test_14_result_keeps_external_identity_authority_and_trust_unverified(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            result = v41.verify_external_signature_against_direct_anchor(
                binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                public_key_der=der, message=self.MESSAGE, signature=private.sign(self.MESSAGE), **sources)
        for key in ("pin_external_provenance_verified", "external_verifier_identity_verified",
                    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
                    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified"):
            self.assertIs(result[key], False)

    def test_15_result_hash_is_self_consistent(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            result = v41.verify_external_signature_against_direct_anchor(
                binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                public_key_der=der, message=self.MESSAGE, signature=private.sign(self.MESSAGE), **sources)
        expected = v41._sha256_payload({k: v for k, v in result.items() if k != "result_sha256"})
        self.assertEqual(result["result_sha256"], expected)

    def test_16_incomplete_source_bundle_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation = self._bundle(Path(tmp), der, "ED25519")
            sources.pop("authority_contract")
            with self.assertRaises(PermissionError):
                v41.build_direct_signer_trust_binding_preview(
                    attestation_contract=attestation, authority_binding=authority_binding, **sources
                )

    def test_17_empty_nonbytes_inputs_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, binding = self._binding(Path(tmp), der, "ED25519")
            for bad_key, bad_message in ((b"", self.MESSAGE), ("not-bytes", self.MESSAGE), (der, b""), (der, "bad")):
                with self.subTest(bad_key=bad_key, bad_message=bad_message), self.assertRaises(PermissionError):
                    v41.verify_external_signature_against_direct_anchor(
                        binding=binding, attestation_contract=attestation, authority_binding=authority_binding,
                        public_key_der=bad_key, message=bad_message, signature=private.sign(self.MESSAGE), **sources)

    def test_18_direct_script_report_is_model_free(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep.py"
        completed = subprocess.run([sys.executable, str(script)], cwd=str(repo_root), capture_output=True, text=True, check=True)
        self.assertIn('"status": "PASS"', completed.stdout)
        self.assertIn('"external_signature_verified": false', completed.stdout)
        self.assertIn('"model_contact_performed": false', completed.stdout)


if __name__ == "__main__":
    unittest.main()
