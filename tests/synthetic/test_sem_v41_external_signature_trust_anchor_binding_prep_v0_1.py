from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep as v41

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa


class TestSemV41ExternalSignatureTrustAnchorBindingPrep(unittest.TestCase):
    MESSAGE = b"ZS-KI-B V41 synthetic external signature vector"

    @staticmethod
    def der(public_key):
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def binding(self, public_key_der: bytes, algorithm: str):
        return v41.build_direct_signer_trust_binding_preview(
            authority_id="AUTHORITY-001",
            authority_epoch="EPOCH-001",
            verifier_id="VERIFIER-001",
            verifier_key_id="KEY-001",
            trust_anchor_id="ANCHOR-001",
            trust_anchor_public_key_sha256=hashlib.sha256(public_key_der).hexdigest(),
            signature_algorithm=algorithm,
        )

    def test_01_base_and_v40_source_binding_exact(self):
        self.assertEqual(v41.BASE_MAIN_COMMIT, "a5f943a56c8e5f8532db36a642f610e1914c2f6b")
        self.assertEqual(v41.SOURCE_V40_SCRIPT_BLOB_SHA, "20ac072ba529f92fc72590ef7852547f162250f1")
        self.assertEqual(v41._validate_v40_source_before_import(), v41.SOURCE_V40_SCRIPT_BLOB_SHA)

    def test_02_supported_algorithms_exact(self):
        self.assertEqual(v41.SUPPORTED_ALGORITHMS, frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"}))

    def test_03_binding_is_structural_and_non_escalating(self):
        private = ed25519.Ed25519PrivateKey.generate()
        binding = self.binding(self.der(private.public_key()), "ED25519")
        self.assertTrue(binding["signer_identity_bound"])
        self.assertTrue(binding["direct_trust_anchor_pin_bound"])
        for key in (
            "pin_external_provenance_verified", "external_authority_attested",
            "external_trust_anchor_verified", "execution_authorized", "model_run_authorized",
            "model_contact_authorized", "ready_for_model_contact", "model_qualified",
        ):
            self.assertIs(binding[key], False)

    def test_04_binding_hash_and_exact_keyset_validate(self):
        private = ed25519.Ed25519PrivateKey.generate()
        binding = self.binding(self.der(private.public_key()), "ED25519")
        self.assertIs(v41.validate_direct_signer_trust_binding_preview(binding), binding)
        tampered = dict(binding)
        tampered["extra"] = False
        with self.assertRaises(PermissionError):
            v41.validate_direct_signer_trust_binding_preview(tampered)

    def test_05_binding_hash_tamper_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        binding = self.binding(self.der(private.public_key()), "ED25519")
        binding["verifier_id"] = "VERIFIER-002"
        with self.assertRaises(PermissionError):
            v41.validate_direct_signer_trust_binding_preview(binding)

    def test_06_invalid_ids_hashes_and_algorithm_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        fp = hashlib.sha256(der).hexdigest()
        with self.assertRaises(PermissionError):
            v41.build_direct_signer_trust_binding_preview(
                authority_id="bad id", authority_epoch="E", verifier_id="V", verifier_key_id="K",
                trust_anchor_id="A", trust_anchor_public_key_sha256=fp, signature_algorithm="ED25519")
        with self.assertRaises(PermissionError):
            v41.build_direct_signer_trust_binding_preview(
                authority_id="A", authority_epoch="E", verifier_id="V", verifier_key_id="K",
                trust_anchor_id="T", trust_anchor_public_key_sha256="00", signature_algorithm="ED25519")
        with self.assertRaises(PermissionError):
            v41.build_direct_signer_trust_binding_preview(
                authority_id="A", authority_epoch="E", verifier_id="V", verifier_key_id="K",
                trust_anchor_id="T", trust_anchor_public_key_sha256=fp, signature_algorithm="ED448")

    def test_07_ed25519_external_signature_valid_against_pin(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        result = v41.verify_external_signature_against_direct_anchor(
            binding=self.binding(der, "ED25519"), public_key_der=der,
            message=self.MESSAGE, signature=private.sign(self.MESSAGE))
        self.assertTrue(result["external_signature_verified"])
        self.assertTrue(result["direct_trust_anchor_pin_match_verified"])
        self.assertTrue(result["signer_identity_binding_verified"])

    def test_08_ecdsa_external_signature_valid_against_pin(self):
        private = ec.generate_private_key(ec.SECP256R1())
        der = self.der(private.public_key())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA256()))
        result = v41.verify_external_signature_against_direct_anchor(
            binding=self.binding(der, "ECDSA-P256-SHA256"), public_key_der=der,
            message=self.MESSAGE, signature=sig)
        self.assertTrue(result["external_signature_verified"])

    def test_09_rsa_external_signature_valid_against_pin(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        der = self.der(private.public_key())
        sig = private.sign(self.MESSAGE, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256())
        result = v41.verify_external_signature_against_direct_anchor(
            binding=self.binding(der, "RSA-PSS-SHA256"), public_key_der=der,
            message=self.MESSAGE, signature=sig)
        self.assertTrue(result["external_signature_verified"])

    def test_10_wrong_public_key_pin_fails_before_crypto(self):
        signer = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        signer_der = self.der(signer.public_key())
        other_der = self.der(other.public_key())
        with self.assertRaises(PermissionError):
            v41.verify_external_signature_against_direct_anchor(
                binding=self.binding(signer_der, "ED25519"), public_key_der=other_der,
                message=self.MESSAGE, signature=signer.sign(self.MESSAGE))

    def test_11_wrong_message_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with self.assertRaises(PermissionError):
            v41.verify_external_signature_against_direct_anchor(
                binding=self.binding(der, "ED25519"), public_key_der=der,
                message=b"wrong", signature=private.sign(self.MESSAGE))

    def test_12_cross_algorithm_mismatch_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        with self.assertRaises(PermissionError):
            v41.verify_external_signature_against_direct_anchor(
                binding=self.binding(der, "ECDSA-P256-SHA256"), public_key_der=der,
                message=self.MESSAGE, signature=private.sign(self.MESSAGE))

    def test_13_result_keeps_external_identity_authority_and_trust_unverified(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        result = v41.verify_external_signature_against_direct_anchor(
            binding=self.binding(der, "ED25519"), public_key_der=der,
            message=self.MESSAGE, signature=private.sign(self.MESSAGE))
        self.assertTrue(result["external_signature_verified"])
        for key in (
            "pin_external_provenance_verified", "external_verifier_identity_verified",
            "external_authority_attested", "external_trust_anchor_verified",
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "ready_for_model_contact", "model_qualified",
        ):
            self.assertIs(result[key], False)

    def test_14_empty_or_nonbytes_public_key_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        binding = self.binding(der, "ED25519")
        for bad in (b"", "not-bytes"):
            with self.subTest(bad=bad), self.assertRaises(PermissionError):
                v41.verify_external_signature_against_direct_anchor(
                    binding=binding, public_key_der=bad,
                    message=self.MESSAGE, signature=private.sign(self.MESSAGE))

    def test_15_result_hash_is_self_consistent(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        result = v41.verify_external_signature_against_direct_anchor(
            binding=self.binding(der, "ED25519"), public_key_der=der,
            message=self.MESSAGE, signature=private.sign(self.MESSAGE))
        expected = v41._sha256_payload({k: v for k, v in result.items() if k != "result_sha256"})
        self.assertEqual(result["result_sha256"], expected)

    def test_16_direct_script_report_is_model_free(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep.py"
        completed = subprocess.run([sys.executable, str(script)], cwd=str(repo_root), capture_output=True, text=True, check=True)
        self.assertIn('"status": "PASS"', completed.stdout)
        self.assertIn('"external_signature_verified": false', completed.stdout)
        self.assertIn('"model_contact_performed": false', completed.stdout)


if __name__ == "__main__":
    unittest.main()
