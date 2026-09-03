from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_crypto_artifact_runtime_binding_v3_9_prep as v39


class TestSemV39CryptoArtifactRuntimeBindingPrep(unittest.TestCase):
    def setUp(self):
        self.binding = v39.build_artifact_runtime_binding_preview()

    def test_01_base_binding_exact(self):
        self.assertEqual(v39.BASE_MAIN_COMMIT, "03acd43461cb75aadf9d4594bec34ccd30982ee1")

    def test_02_v38_source_blob_exact(self):
        self.assertEqual(v39.SOURCE_V38_SCRIPT_BLOB_SHA, "5c6ccdeeb94e086dfea48361279461c0d5cad2f8")
        self.assertEqual(v39._validate_loaded_v38_blob(), v39.SOURCE_V38_SCRIPT_BLOB_SHA)

    def test_03_backend_binding_exact(self):
        self.assertEqual(v39.BACKEND_REQUIREMENT, "cryptography==50.0.1")
        self.assertEqual(self.binding["source_v38_backend_binding_sha256"], v39.v38.build_backend_binding_preview()["backend_binding_sha256"])

    def test_04_exact_artifact_bound(self):
        self.assertEqual(v39.ARTIFACT_FILENAME, "cryptography-50.0.1-cp311-abi3-win_amd64.whl")
        self.assertEqual(v39.ARTIFACT_SHA256, "aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648")
        self.assertEqual(v39.ARTIFACT_INTERPRETER_TAG, "cp311")
        self.assertEqual(v39.ARTIFACT_ABI_TAG, "abi3")
        self.assertEqual(v39.ARTIFACT_PLATFORM_TAG, "win_amd64")

    def test_05_artifact_provenance_metadata_bound_without_attestation_claim(self):
        self.assertEqual(v39.ARTIFACT_PUBLISHER, "pyca/cryptography")
        self.assertEqual(v39.ARTIFACT_SOURCE_COMMIT, "dc1125347f52b36b7070332910c680e68db0f478")
        self.assertIs(v39.ARTIFACT_TRUSTED_PUBLISHING_REPORTED, True)
        self.assertIs(v39.ARTIFACT_ATTESTATION_VERIFIED, False)

    def test_06_binding_validates_exactly(self):
        self.assertEqual(v39.validate_artifact_runtime_binding_preview(self.binding), self.binding)

    def test_07_runtime_target_exact(self):
        self.assertEqual(v39.TARGET_PYTHON_IMPLEMENTATION, "CPython")
        self.assertEqual(v39.TARGET_PYTHON_MIN, (3, 11))
        self.assertEqual(v39.TARGET_SYS_PLATFORM, "win32")
        self.assertEqual(v39.TARGET_MACHINE_ACCEPTED, frozenset({"AMD64", "x86_64"}))
        self.assertEqual(v39.TARGET_POINTER_BITS, 64)

    def test_08_runtime_positive_synthetic(self):
        report = v39.validate_runtime_facts(
            implementation="CPython", version=(3, 11), sys_platform="win32", machine="AMD64", pointer_bits=64
        )
        self.assertTrue(report["runtime_target_verified"])
        self.assertEqual(report["compatible_artifact_filename"], v39.ARTIFACT_FILENAME)

    def test_09_wrong_implementation_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="PyPy", version=(3, 11), sys_platform="win32", machine="AMD64", pointer_bits=64
            )

    def test_10_old_python_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="CPython", version=(3, 10), sys_platform="win32", machine="AMD64", pointer_bits=64
            )

    def test_11_wrong_platform_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="CPython", version=(3, 11), sys_platform="linux", machine="x86_64", pointer_bits=64
            )

    def test_12_wrong_machine_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="CPython", version=(3, 11), sys_platform="win32", machine="ARM64", pointer_bits=64
            )

    def test_13_wrong_pointer_width_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="CPython", version=(3, 11), sys_platform="win32", machine="AMD64", pointer_bits=32
            )

    def test_14_invalid_version_type_rejected(self):
        with self.assertRaises(PermissionError):
            v39.validate_runtime_facts(
                implementation="CPython", version=(3, True), sys_platform="win32", machine="AMD64", pointer_bits=64
            )

    def test_15_sha256_file_is_real_sha256(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.bin"
            p.write_bytes(b"abc")
            self.assertEqual(v39._sha256_file(p), hashlib.sha256(b"abc").hexdigest())

    def test_16_wrong_artifact_filename_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "renamed.whl"
            p.write_bytes(b"x")
            with self.assertRaises(PermissionError):
                v39.verify_distribution_artifact(p)

    def test_17_wrong_artifact_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / v39.ARTIFACT_FILENAME
            p.write_bytes(b"not-the-wheel")
            with self.assertRaises(PermissionError):
                v39.verify_distribution_artifact(p)

    def test_18_positive_artifact_path_sets_only_hash_verified(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / v39.ARTIFACT_FILENAME
            p.write_bytes(b"synthetic")
            with patch.object(v39, "_sha256_file", return_value=v39.ARTIFACT_SHA256):
                report = v39.verify_distribution_artifact(p)
            self.assertTrue(report["dependency_artifact_hash_verified"])
            self.assertFalse(report["dependency_installed"])
            self.assertFalse(report["dependency_imported"])
            self.assertFalse(report["cryptographic_backend_present"])
            self.assertFalse(report["external_signature_verified"])
            self.assertFalse(report["model_contact_authorized"])

    def test_19_extra_field_injection_rejected_after_rehash(self):
        forged = copy.deepcopy(self.binding)
        forged["attacker_note"] = "x"
        forged["artifact_runtime_binding_sha256"] = v39._sha256_payload(
            {k: val for k, val in forged.items() if k != "artifact_runtime_binding_sha256"}
        )
        with self.assertRaises(PermissionError):
            v39.validate_artifact_runtime_binding_preview(forged)

    def test_20_false_runtime_or_hash_escalation_rejected(self):
        for key in ("runtime_target_verified", "dependency_artifact_hash_verified"):
            forged = copy.deepcopy(self.binding)
            forged[key] = True
            forged["artifact_runtime_binding_sha256"] = v39._sha256_payload(
                {k: val for k, val in forged.items() if k != "artifact_runtime_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v39.validate_artifact_runtime_binding_preview(forged)

    def test_21_install_or_backend_presence_escalation_rejected(self):
        forged = copy.deepcopy(self.binding)
        forged["dependency_installed"] = True
        forged["dependency_imported"] = True
        forged["cryptographic_backend_present"] = True
        forged["artifact_runtime_binding_sha256"] = v39._sha256_payload(
            {k: val for k, val in forged.items() if k != "artifact_runtime_binding_sha256"}
        )
        with self.assertRaises(PermissionError):
            v39.validate_artifact_runtime_binding_preview(forged)

    def test_22_changed_loaded_v38_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "v38.py"
            fake.write_bytes(b"changed-v38")
            with patch.object(v39.v38, "__file__", str(fake)):
                with self.assertRaises(PermissionError):
                    v39.build_artifact_runtime_binding_preview()

    def test_23_no_crypto_import_or_verifier_helper(self):
        names = set(vars(v39))
        self.assertNotIn("cryptography", names)
        self.assertNotIn("verify_signature", names)
        self.assertNotIn("InvalidSignature", names)

    def test_24_authorization_and_crypto_flags_remain_false(self):
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "ready_for_model_contact", "model_qualified", "cryptographic_verification_performed",
            "external_signature_verified", "external_authority_attested", "external_trust_anchor_verified",
        ):
            self.assertIs(self.binding[key], False)

    def test_25_live_install_crypto_use_rejected(self):
        with self.assertRaises(PermissionError):
            v39.reject_any_install_crypto_or_live_use()

    def test_26_report_is_non_authorizing(self):
        report = v39.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["runtime_target_verified"])
        self.assertFalse(report["dependency_artifact_hash_verified"])
        self.assertFalse(report["dependency_installed"])
        self.assertFalse(report["model_contact_authorized"])


if __name__ == "__main__":
    unittest.main()
