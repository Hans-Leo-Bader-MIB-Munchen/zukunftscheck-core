from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31
import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32
import scripts.zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep as v33
import scripts.zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep as v34
import scripts.zs_ki_b_sem_external_attestation_global_single_use_v3_5_prep as v35
import scripts.zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep as v36
import scripts.zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep as v41
import scripts.zs_ki_b_sem_external_trust_anchor_provenance_authority_attestation_v4_2_prep as v42

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

SECRET = "V42-SYNTHETIC-ONLY-SECRET-" + ("A" * 40)
NONCE = "9" * 64
RUNNER_OID = "4" * 40
MESSAGE = b"ZS-KI-B V42 synthetic external authority evidence\n"


class TestSemV42ExternalTrustAnchorProvenanceAuthorityAttestationPrep(unittest.TestCase):
    @staticmethod
    def der(public_key):
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def _bundle(self, root: Path, verifier_public_key_der: bytes, verifier_algorithm: str = "ED25519"):
        verifier_fp = hashlib.sha256(verifier_public_key_der).hexdigest()
        candidate = v29.build_candidate_snapshot()
        challenge = v28.build_gate_challenge_preview(candidate=candidate, approval_secret=SECRET, nonce=NONCE)
        authority_path = root / "authority" / "state.json"
        contract31 = v31.build_authority_state_contract_preview(
            authority_state_path=str(authority_path.resolve()), trust_anchor_id="V42-ANCHOR-001",
            trust_anchor_fingerprint_sha256=verifier_fp, durable_claim_record_id="V42-CLAIM-001",
            consume_record_id="V42-CONSUME-001", final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        external = v32.build_external_state_resolution_preview(authority_contract=contract31)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V42-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract31["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract31["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        authority_binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        evidence_path = root / "external-evidence.bin"
        evidence_path.write_bytes(MESSAGE)
        evidence = v35.build_external_evidence_reference_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_path=str(evidence_path.resolve()), evidence_id="V42-EVIDENCE-001",
            expected_evidence_sha256=hashlib.sha256(MESSAGE).hexdigest(),
        )
        global_binding = v35.build_global_store_binding_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract31, external_state_preview=external, store_root=str(store_root.resolve()),
            evidence_reference=evidence, global_store_binding_id="V42-GLOBAL-STORE-001",
        )
        attestation = v36.build_attestation_verification_contract_preview(
            global_store_binding=global_binding, evidence_reference=evidence, authority_binding=authority_binding,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
            verifier_id="V42-VERIFIER-001", verifier_key_id="V42-KEY-001",
            verifier_key_fingerprint_sha256=verifier_fp, signature_algorithm=verifier_algorithm,
        )
        sources = dict(
            global_store_binding=global_binding, evidence_reference=evidence,
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract31,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        v41_binding = v41.build_direct_signer_trust_binding_preview(
            attestation_contract=attestation, authority_binding=authority_binding, **sources
        )
        return sources, authority_binding, attestation, v41_binding

    def _contract(self, root: Path, verifier_der: bytes, root_der: bytes, root_algorithm: str):
        sources, authority_binding, attestation, v41_binding = self._bundle(root, verifier_der)
        contract = v42.build_authority_key_attestation_contract_preview(
            v41_binding=v41_binding, attestation_contract=attestation, authority_binding=authority_binding,
            authority_root_key_id="V42-ROOT-KEY-001",
            authority_root_public_key_sha256=hashlib.sha256(root_der).hexdigest(),
            authority_signature_algorithm=root_algorithm, **sources,
        )
        return sources, authority_binding, attestation, v41_binding, contract

    def _payload_bytes(self, contract, v41_binding):
        payload = v42._authority_attestation_payload(
            v41_binding=v41_binding,
            authority_root_key_id=contract["authority_root_key_id"],
            authority_root_public_key_sha256=contract["authority_root_public_key_sha256"],
            authority_signature_algorithm=contract["authority_signature_algorithm"],
        )
        return v42._canonical_bytes(payload)

    def test_01_base_and_v41_source_binding_exact(self):
        self.assertEqual(v42.BASE_MAIN_COMMIT, "422ca141e9c8ba42c9627e5c3928616fa33be41e")
        self.assertEqual(v42.SOURCE_V41_SCRIPT_BLOB_SHA, "a4fca4f0f97b422dcd8baa811c2a04fab38e2674")
        self.assertEqual(v42._validate_v41_source_before_import(), v42.SOURCE_V41_SCRIPT_BLOB_SHA)

    def test_02_contract_binds_separate_root_without_external_escalation(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, contract = self._contract(Path(tmp), self.der(verifier.public_key()), self.der(root_key.public_key()), "ED25519")
        self.assertTrue(contract["separate_authority_root_key_required"])
        self.assertTrue(contract["authority_root_external_provenance_required"])
        for key in ("authority_key_attestation_signature_verified", "authority_root_external_provenance_verified",
                    "external_verifier_identity_verified", "external_authority_attested", "external_trust_anchor_verified",
                    "execution_authorized", "model_run_authorized", "model_contact_authorized",
                    "ready_for_model_contact", "model_qualified"):
            self.assertIs(contract[key], False)

    def test_03_same_root_and_verifier_key_rejected(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        der = self.der(verifier.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding = self._bundle(Path(tmp), der)
            with self.assertRaises(PermissionError):
                v42.build_authority_key_attestation_contract_preview(
                    v41_binding=v41_binding, attestation_contract=attestation, authority_binding=authority_binding,
                    authority_root_key_id="ROOT", authority_root_public_key_sha256=hashlib.sha256(der).hexdigest(),
                    authority_signature_algorithm="ED25519", **sources)

    def test_04_unknown_authority_signature_algorithm_rejected(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding = self._bundle(Path(tmp), self.der(verifier.public_key()))
            with self.assertRaises(PermissionError):
                v42.build_authority_key_attestation_contract_preview(
                    v41_binding=v41_binding, attestation_contract=attestation, authority_binding=authority_binding,
                    authority_root_key_id="ROOT", authority_root_public_key_sha256=hashlib.sha256(self.der(root_key.public_key())).hexdigest(),
                    authority_signature_algorithm="ED448", **sources)

    def test_05_contract_tamper_rejected_even_after_rehash(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), self.der(root_key.public_key()), "ED25519")
            tampered = dict(contract)
            tampered["attested_verifier_id"] = "ATTACKER"
            tampered["contract_sha256"] = v42._sha256_payload({k: v for k, v in tampered.items() if k != "contract_sha256"})
            with self.assertRaises(PermissionError):
                v42.validate_authority_key_attestation_contract_preview(
                    tampered, v41_binding=v41_binding, attestation_contract=attestation,
                    authority_binding=authority_binding, **sources)

    def test_06_ed25519_authority_attestation_signature_valid(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ED25519")
            payload = self._payload_bytes(contract, v41_binding)
            result = v42.verify_authority_key_attestation_signature(
                contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                authority_binding=authority_binding, authority_root_public_key_der=root_der,
                authority_signature=root_key.sign(payload), **sources)
        self.assertTrue(result["authority_key_attestation_signature_verified"])

    def test_07_ecdsa_authority_attestation_signature_valid(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ec.generate_private_key(ec.SECP256R1())
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ECDSA-P256-SHA256")
            payload = self._payload_bytes(contract, v41_binding)
            signature = root_key.sign(payload, ec.ECDSA(hashes.SHA256()))
            result = v42.verify_authority_key_attestation_signature(
                contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                authority_binding=authority_binding, authority_root_public_key_der=root_der,
                authority_signature=signature, **sources)
        self.assertTrue(result["authority_key_attestation_signature_verified"])

    def test_08_rsa_authority_attestation_signature_valid(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "RSA-PSS-SHA256")
            payload = self._payload_bytes(contract, v41_binding)
            signature = root_key.sign(payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256())
            result = v42.verify_authority_key_attestation_signature(
                contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                authority_binding=authority_binding, authority_root_public_key_der=root_der,
                authority_signature=signature, **sources)
        self.assertTrue(result["authority_key_attestation_signature_verified"])

    def test_09_wrong_root_public_key_rejected(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ED25519")
            payload = self._payload_bytes(contract, v41_binding)
            with self.assertRaises(PermissionError):
                v42.verify_authority_key_attestation_signature(
                    contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                    authority_binding=authority_binding, authority_root_public_key_der=self.der(other.public_key()),
                    authority_signature=root_key.sign(payload), **sources)

    def test_10_wrong_authority_signature_fails_closed(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ED25519")
            payload = self._payload_bytes(contract, v41_binding)
            with self.assertRaises(PermissionError):
                v42.verify_authority_key_attestation_signature(
                    contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                    authority_binding=authority_binding, authority_root_public_key_der=root_der,
                    authority_signature=other.sign(payload), **sources)

    def test_11_v41_binding_substitution_rejected(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), self.der(root_key.public_key()), "ED25519")
            bad = dict(v41_binding)
            bad["verifier_id"] = "ATTACKER"
            bad["binding_sha256"] = v41._sha256_payload({k: v for k, v in bad.items() if k != "binding_sha256"})
            with self.assertRaises(PermissionError):
                v42.validate_authority_key_attestation_contract_preview(
                    contract, v41_binding=bad, attestation_contract=attestation,
                    authority_binding=authority_binding, **sources)

    def test_12_attestation_payload_is_domain_separated_and_hash_bound(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), self.der(root_key.public_key()), "ED25519")
        payload = self._payload_bytes(contract, v41_binding)
        self.assertEqual(v42.ATTESTATION_DOMAIN, "ZS-KI-B-V42-AUTHORITY-KEY-ATTESTATION-v1")
        self.assertEqual(hashlib.sha256(payload).hexdigest(), contract["attestation_payload_sha256"])

    def test_13_result_keeps_root_provenance_and_external_authority_unverified(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ED25519")
            payload = self._payload_bytes(contract, v41_binding)
            result = v42.verify_authority_key_attestation_signature(
                contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                authority_binding=authority_binding, authority_root_public_key_der=root_der,
                authority_signature=root_key.sign(payload), **sources)
        for key in ("authority_root_external_provenance_verified", "external_verifier_identity_verified",
                    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
                    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified"):
            self.assertIs(result[key], False)

    def test_14_result_hash_self_consistent(self):
        verifier = ed25519.Ed25519PrivateKey.generate()
        root_key = ed25519.Ed25519PrivateKey.generate()
        root_der = self.der(root_key.public_key())
        with tempfile.TemporaryDirectory() as tmp:
            sources, authority_binding, attestation, v41_binding, contract = self._contract(
                Path(tmp), self.der(verifier.public_key()), root_der, "ED25519")
            payload = self._payload_bytes(contract, v41_binding)
            result = v42.verify_authority_key_attestation_signature(
                contract=contract, v41_binding=v41_binding, attestation_contract=attestation,
                authority_binding=authority_binding, authority_root_public_key_der=root_der,
                authority_signature=root_key.sign(payload), **sources)
        expected = v42._sha256_payload({k: v for k, v in result.items() if k != "result_sha256"})
        self.assertEqual(result["result_sha256"], expected)

    def test_15_prep_report_has_no_authority_or_model_escalation(self):
        report = v42.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authority_key_attestation_signature_verified"])
        self.assertFalse(report["authority_root_external_provenance_verified"])
        self.assertFalse(report["external_authority_attested"])
        self.assertFalse(report["model_contact_performed"])

    def test_16_direct_script_report_is_model_free(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "zs_ki_b_sem_external_trust_anchor_provenance_authority_attestation_v4_2_prep.py"
        completed = subprocess.run([sys.executable, str(script)], cwd=str(repo_root), capture_output=True, text=True, check=True)
        self.assertIn('"status": "PASS"', completed.stdout)
        self.assertIn('"external_authority_attested": false', completed.stdout)
        self.assertIn('"model_contact_performed": false', completed.stdout)


if __name__ == "__main__":
    unittest.main()
