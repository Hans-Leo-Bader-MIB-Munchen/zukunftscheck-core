from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_prerun_package_v0_1 as prep


class TestSemMinistralQualificationPrerunPackage(unittest.TestCase):
    def test_01_exact_base_and_reentry_binding(self):
        self.assertEqual(prep.BASE_MAIN_COMMIT, "28c582ab3b075298c5ca029f74005e1a8928fa9d")
        self.assertEqual(prep.REENTRY_BLOB_SHA, "1f11af89eb75349d2c3cf098800c397ad4f0d9a6")
        prep._validate_reentry_source_before_import()

    def test_02_package_is_prepared_not_authorized(self):
        package = prep.build_prerun_package()
        self.assertEqual(package["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(package["authorization_gate"]["state"], "CLOSED")
        self.assertTrue(package["authorization_gate"]["explicit_user_single_run_approval_required"])
        self.assertTrue(package["authorization_gate"]["separate_authorization_artifact_required"])
        self.assertTrue(package["authorization_gate"]["no_execution_from_prerun_package"])

    def test_03_exact_ministral_binding(self):
        package = prep.build_prerun_package()
        self.assertEqual(package["runtime_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(package["model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")

    def test_04_exact_16_case_snapshot(self):
        package = prep.build_prerun_package()
        self.assertEqual(package["expected_model_request_count"], 16)
        self.assertEqual(len(package["ordered_case_ids"]), 16)
        self.assertEqual(len(package["qualification_snapshot_sha256"]), 64)
        self.assertEqual(len(package["ordered_case_ids_sha256"]), 64)

    def test_05_request_bounds_are_exact(self):
        package = prep.build_prerun_package()
        self.assertEqual(package["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(package["max_tokens"], 2048)
        self.assertEqual(package["retry_count"], 0)
        self.assertFalse(package["output_repair"])
        self.assertFalse(package["automatic_retry_authorized"])
        self.assertFalse(package["automatic_rerun_authorized"])

    def test_06_human_gold_remains_model_invisible(self):
        package = prep.build_prerun_package()
        self.assertFalse(package["human_gold"]["model_visible"])
        self.assertEqual(package["human_gold"]["freeze_status"], "HUMAN_APPROVED_FROZEN")

    def test_07_security_chain_is_bound(self):
        package = prep.build_prerun_package()
        bindings = {item["role"]: item for item in package["security_source_bindings"]}
        self.assertEqual(len(bindings), 10)
        for role in (
            "v25_live_runner", "v26_one_shot_authorization", "v27_approval_ceremony",
            "v28_execution_gate", "v29_run_authorization_transform", "v30_proof_enforcing_live_gate",
            "v31_authority_state_atomic_consume", "v32_external_state_atomic_consume",
            "v33_canonical_store_toctou", "v42_authority_root_attestation",
        ):
            self.assertIn(role, bindings)
            self.assertEqual(len(bindings[role]["git_blob_sha"]), 40)

    def test_08_all_authority_and_product_flags_remain_false(self):
        package = prep.build_prerun_package()
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "model_qualified", "benchmark_approved",
            "generalisation_approved", "real_data", "pilot_approved",
            "production_approved", "phase_f_approved",
        ):
            self.assertIs(package[key], False, key)

    def test_09_authorization_consumption_boundary_is_explicit(self):
        package = prep.build_prerun_package()
        self.assertTrue(package["authorization_gate"]["authorization_must_be_consumed_before_first_possible_model_contact"])

    def test_10_package_hash_is_deterministic(self):
        first = prep.build_prerun_package()
        second = prep.build_prerun_package()
        self.assertEqual(first, second)
        self.assertEqual(first["prerun_package_sha256"], second["prerun_package_sha256"])

    def test_11_tampered_package_rejected_even_with_recomputed_hash(self):
        package = prep.build_prerun_package()
        tampered = copy.deepcopy(package)
        tampered["max_tokens"] = 4096
        unsigned = dict(tampered)
        unsigned.pop("prerun_package_sha256")
        tampered["prerun_package_sha256"] = prep._stable_sha256(unsigned)
        with self.assertRaises(PermissionError):
            prep.validate_prerun_package(tampered)

    def test_12_changed_reentry_boundary_fails_closed(self):
        with patch.object(prep.reentry, "EXPECTED_RUNTIME_MODEL_ID", "other-model"):
            with self.assertRaises(PermissionError):
                prep.build_prerun_package()

    def test_13_report_is_model_free_and_not_authorized(self):
        report = prep.build_report()
        self.assertEqual(report["mode"], "MODEL_FREE_MINISTRAL_QUALIFICATION_PRERUN_PREP")
        self.assertEqual(report["status"], "PASS")
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "model_qualified",
        ):
            self.assertIs(report[key], False, key)

    def test_14_module_has_no_execution_transport_or_approval_materialization_entrypoint(self):
        names = set(vars(prep))
        for forbidden in (
            "execute_once", "_default_transport", "_default_preflight",
            "materialize_live_authorization", "build_approval_artifact",
        ):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
