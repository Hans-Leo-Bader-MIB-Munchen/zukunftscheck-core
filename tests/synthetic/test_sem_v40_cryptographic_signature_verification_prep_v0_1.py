from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep as v40

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
except Exception:  # tested explicitly by V40 fail-closed dependency checks
    hashes = serialization = ec = ed25519 = padding = rsa = None


@unittest.skipIf(serialization is None, "cryptography dependency not installed")
class TestSemV40CryptographicSignatureVerificationPrep(unittest.TestCase):
    MESSAGE = b"ZS-KI-B V40 synthetic signature verification vector"

    @staticmethod
    def der(public_key):
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def test_01_base_and_dependency_binding_exact(self):
        self.assertEqual(v40.BASE_MAIN_COMMIT, "53bb1deaeda70466b82d666fa32e727b8c30d16d")
        self.assertEqual(v40.BACKEND_REQUIREMENT, "cryptography==50.0.1")

    def test_02_source_blob_bindings_exact(self):
        self.assertEqual(v40.SOURCE_V38_SCRIPT_BLOB_SHA, "5c6ccdeeb94e086dfea48361279461c0d5cad2f8")
        self.assertEqual(v40.SOURCE_V39_SCRIPT_BLOB_SHA, "071f4d5d8ee7fa91f28a38b8cd8804be2c53b584")
        self.assertEqual(v40._validate_source(v40.v38, v40.SOURCE_V38_SCRIPT_BLOB_SHA, "V38"), v40.SOURCE_V38_SCRIPT_BLOB_SHA)
        self.assertEqual(v40._validate_source(v40.v39, v40.SOURCE_V39_SCRIPT_BLOB_SHA, "V39"), v40.SOURCE_V39_SCRIPT_BLOB_SHA)

    def test_03_supported_algorithms_are_exact_v38_set(self):
        self.assertEqual(v40.SUPPORTED_ALGORITHMS, frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"}))

    def test_04_ed25519_valid_signature(self):
        private = ed25519.Ed25519PrivateKey.generate()
        result = v40.verify_bound_signature(
            signature_algorithm="ED25519",
            public_key_der=self.der(private.public_key()),
            message=self.MESSAGE,
            signature=private.sign(self.MESSAGE),
        )
        self.assertTrue(result["signature_valid"])
        self.assertTrue(result["cryptographic_verification_performed"])
        self.assertFalse(result["external_trust_anchor_verified"])

    def test_05_ed25519_wrong_message_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        sig = private.sign(self.MESSAGE)
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ED25519", public_key_der=self.der(private.public_key()),
                message=b"wrong", signature=sig,
            )

    def test_06_ed25519_wrong_key_fails_closed(self):
        signer = ed25519.Ed25519PrivateKey.generate()
        other = ed25519.Ed25519PrivateKey.generate()
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ED25519", public_key_der=self.der(other.public_key()),
                message=self.MESSAGE, signature=signer.sign(self.MESSAGE),
            )

    def test_07_ed25519_wrong_signature_length_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ED25519", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=b"x" * 63,
            )

    def test_08_ecdsa_p256_sha256_valid_signature(self):
        private = ec.generate_private_key(ec.SECP256R1())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA256()))
        result = v40.verify_bound_signature(
            signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
            message=self.MESSAGE, signature=sig,
        )
        self.assertTrue(result["signature_valid"])

    def test_09_ecdsa_wrong_message_fails_closed(self):
        private = ec.generate_private_key(ec.SECP256R1())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA256()))
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
                message=b"wrong", signature=sig,
            )

    def test_10_ecdsa_wrong_curve_fails_closed(self):
        private = ec.generate_private_key(ec.SECP384R1())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA256()))
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=sig,
            )

    def test_11_ecdsa_wrong_hash_fails_closed(self):
        private = ec.generate_private_key(ec.SECP256R1())
        sig = private.sign(self.MESSAGE, ec.ECDSA(hashes.SHA384()))
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=sig,
            )

    def test_12_ecdsa_non_der_signature_fails_closed(self):
        private = ec.generate_private_key(ec.SECP256R1())
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=b"not-der",
            )

    def test_13_rsa_pss_sha256_valid_signature(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        sig = private.sign(
            self.MESSAGE,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        result = v40.verify_bound_signature(
            signature_algorithm="RSA-PSS-SHA256", public_key_der=self.der(private.public_key()),
            message=self.MESSAGE, signature=sig,
        )
        self.assertTrue(result["signature_valid"])

    def test_14_rsa_pkcs1v15_rejected(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        sig = private.sign(self.MESSAGE, padding.PKCS1v15(), hashes.SHA256())
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="RSA-PSS-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=sig,
            )

    def test_15_rsa_pss_wrong_mgf_hash_rejected(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        sig = private.sign(
            self.MESSAGE,
            padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=32),
            hashes.SHA256(),
        )
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="RSA-PSS-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=sig,
            )

    def test_16_rsa_pss_wrong_salt_length_rejected(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        sig = private.sign(
            self.MESSAGE,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=20),
            hashes.SHA256(),
        )
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="RSA-PSS-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=sig,
            )

    def test_17_cross_algorithm_key_type_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ECDSA-P256-SHA256", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=private.sign(self.MESSAGE),
            )

    def test_18_unknown_algorithm_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ED448", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=private.sign(self.MESSAGE),
            )

    def test_19_empty_or_non_bytes_inputs_rejected(self):
        private = ed25519.Ed25519PrivateKey.generate()
        der = self.der(private.public_key())
        sig = private.sign(self.MESSAGE)
        for kwargs in (
            {"public_key_der": b"", "message": self.MESSAGE, "signature": sig},
            {"public_key_der": der, "message": b"", "signature": sig},
            {"public_key_der": der, "message": self.MESSAGE, "signature": b""},
            {"public_key_der": "bad", "message": self.MESSAGE, "signature": sig},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(PermissionError):
                v40.verify_bound_signature(signature_algorithm="ED25519", **kwargs)

    def test_20_dependency_version_mismatch_fails_closed(self):
        private = ed25519.Ed25519PrivateKey.generate()
        with patch.object(v40.importlib.metadata, "version", return_value="49.0.0"), self.assertRaises(PermissionError):
            v40.verify_bound_signature(
                signature_algorithm="ED25519", public_key_der=self.der(private.public_key()),
                message=self.MESSAGE, signature=private.sign(self.MESSAGE),
            )

    def test_21_result_never_escalates_authority_or_model_state(self):
        private = ed25519.Ed25519PrivateKey.generate()
        result = v40.verify_bound_signature(
            signature_algorithm="ED25519", public_key_der=self.der(private.public_key()),
            message=self.MESSAGE, signature=private.sign(self.MESSAGE),
        )
        for key in (
            "external_signature_verified", "external_verifier_identity_verified",
            "external_authority_attested", "external_trust_anchor_verified",
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "ready_for_model_contact", "model_qualified",
        ):
            self.assertIs(result[key], False)

    def test_22_direct_script_report_is_model_free(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep.py"
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=str(repo_root), capture_output=True, text=True, check=True
        )
        self.assertIn('"status": "PASS"', completed.stdout)
        self.assertIn('"model_contact_performed": false', completed.stdout)
        self.assertIn('"cryptographic_verification_performed": false', completed.stdout)


if __name__ == "__main__":
    unittest.main()
