from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_crypto_backend_dependency_binding_v3_8_prep as v38


class TestSemV38CryptoBackendDependencyBindingPrep(unittest.TestCase):
    def setUp(self):
        self.binding = v38.build_backend_binding_preview()

    def test_01_base_binding_exact(self):
        self.assertEqual(v38.BASE_MAIN_COMMIT, "71d5a70420b4c976c0e822ba34514a63c6b7ac87")

    def test_02_backend_dependency_is_exactly_pinned(self):
        self.assertEqual(v38.BACKEND_PACKAGE, "cryptography")
        self.assertEqual(v38.BACKEND_VERSION, "50.0.1")
        self.assertEqual(v38.BACKEND_REQUIREMENT, "cryptography==50.0.1")

    def test_03_binding_validates_exactly(self):
        self.assertEqual(v38.validate_backend_binding_preview(self.binding), self.binding)

    def test_04_exact_three_algorithms_bound(self):
        self.assertEqual(set(v38.ALGORITHM_PROFILES), {"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"})

    def test_05_uniform_public_key_serialization(self):
        self.assertEqual(v38.PUBLIC_KEY_SERIALIZATION, "DER_SUBJECT_PUBLIC_KEY_INFO")
        for profile in v38.ALGORITHM_PROFILES.values():
            self.assertEqual(profile["public_key_serialization"], "DER_SUBJECT_PUBLIC_KEY_INFO")

    def test_06_ed25519_semantics_exact(self):
        profile = v38.validate_algorithm_request("ED25519", self.binding)
        self.assertEqual(profile["public_key_type"], "Ed25519PublicKey")
        self.assertEqual(profile["message_mode"], "DIRECT_MESSAGE_BYTES")
        self.assertIsNone(profile["hash_algorithm"])
        self.assertEqual(profile["signature_encoding"], "RAW_64_BYTES")

    def test_07_ecdsa_semantics_exact(self):
        profile = v38.validate_algorithm_request("ECDSA-P256-SHA256", self.binding)
        self.assertEqual(profile["curve"], "SECP256R1")
        self.assertEqual(profile["hash_algorithm"], "SHA256")
        self.assertEqual(profile["signature_encoding"], "ASN1_DER_ECDSA_R_S")

    def test_08_rsa_pss_semantics_exact(self):
        profile = v38.validate_algorithm_request("RSA-PSS-SHA256", self.binding)
        self.assertEqual(profile["rsa_padding"], "PSS")
        self.assertEqual(profile["mgf_hash"], "SHA256")
        self.assertEqual(profile["hash_algorithm"], "SHA256")
        self.assertEqual(profile["pss_salt_length"], 32)

    def test_09_unknown_algorithm_rejected(self):
        with self.assertRaises(PermissionError):
            v38.validate_algorithm_request("RSA-PKCS1V15-SHA256", self.binding)

    def test_10_extra_field_injection_rejected_even_if_rehashed(self):
        forged = copy.deepcopy(self.binding)
        forged["attacker_note"] = "extra"
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_11_positive_verification_escalation_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["cryptographic_verification_performed"] = True
        forged["external_signature_verified"] = True
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_12_dependency_presence_escalation_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["dependency_imported"] = True
        forged["cryptographic_backend_present"] = True
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_13_algorithm_profile_substitution_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["algorithm_profiles"]["RSA-PSS-SHA256"]["pss_salt_length"] = "MAX_LENGTH"
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_14_version_substitution_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["backend_version"] = "50.0.0"
        forged["backend_requirement"] = "cryptography==50.0.0"
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_15_v37_source_binding_exact(self):
        self.assertEqual(self.binding["source_v37_prep_version"], v38.v37.PREP_VERSION)
        self.assertEqual(self.binding["source_v37_request_version"], v38.v37.REQUEST_VERSION)
        self.assertEqual(self.binding["source_v37_script_blob_sha"], "a7c2192983be9c580b3dd8b8e68ee3e80e7afb02")
        self.assertEqual(v38._validate_loaded_v37_blob(), "a7c2192983be9c580b3dd8b8e68ee3e80e7afb02")

    def test_16_no_crypto_backend_import_or_verifier_helper(self):
        names = set(vars(v38))
        self.assertNotIn("cryptography", names)
        self.assertNotIn("verify_signature", names)
        self.assertNotIn("InvalidSignature", names)

    def test_17_no_authorization_state_can_become_true(self):
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "ready_for_model_contact", "model_qualified", "external_signature_verified",
            "external_authority_attested", "external_trust_anchor_verified",
        ):
            self.assertIs(self.binding[key], False)

    def test_18_live_crypto_use_rejected_unconditionally(self):
        with self.assertRaises(PermissionError):
            v38.reject_any_crypto_or_live_use()

    def test_19_report_is_explicitly_non_authorizing(self):
        report = v38.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["dependency_imported"])
        self.assertFalse(report["cryptographic_verification_performed"])
        self.assertFalse(report["model_contact_authorized"])

    def test_20_dependency_artifact_hash_is_required_but_not_verified(self):
        self.assertIs(self.binding["dependency_artifact_hash_required"], True)
        self.assertIs(self.binding["dependency_artifact_hash_verified"], False)

    def test_21_artifact_hash_verification_escalation_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["dependency_artifact_hash_verified"] = True
        forged["backend_binding_sha256"] = v38._sha256_payload({k: val for k, val in forged.items() if k != "backend_binding_sha256"})
        with self.assertRaises(PermissionError):
            v38.validate_backend_binding_preview(forged)

    def test_22_changed_loaded_v37_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "v37.py"
            fake.write_bytes(b"changed-v37-source")
            with patch.object(v38.v37, "__file__", str(fake)):
                with self.assertRaises(PermissionError):
                    v38.build_backend_binding_preview()


if __name__ == "__main__":
    unittest.main()
