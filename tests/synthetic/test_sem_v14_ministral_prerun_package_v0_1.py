from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_prerun_package_v0_1.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_v0_1.json"


class TestSemV14MinistralPrerunPackageV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
        cls.auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))

    def test_f01_package_identity(self) -> None:
        self.assertEqual(self.package["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(self.package["runner_version"], "v1.4")
        self.assertEqual(
            self.package["run_type"],
            "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015",
        )
        self.assertEqual(
            self.package["model"],
            "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        )

    def test_f02_one_shot_constraints_are_frozen(self) -> None:
        self.assertEqual(self.package["expected_model_request_count"], 16)
        self.assertEqual(self.package["required_loaded_context_length"], 32768)
        self.assertEqual(self.package["required_request_timeout_seconds"], 1800)
        self.assertTrue(self.package["single_run_only"])
        self.assertEqual(self.package["retry_count"], 0)
        self.assertFalse(self.package["output_repair"])

    def test_f03_execution_and_model_contact_remain_closed(self) -> None:
        for key in (
            "download_authorized",
            "model_load_authorized",
            "localhost_preflight_authorized",
            "execution_authorized",
            "model_run_authorized",
            "model_contact_authorized",
            "model_contact_performed",
            "model_qualified",
        ):
            self.assertFalse(self.package[key], key)
        self.assertEqual(self.package["authorization_gate"]["current_state"], "CLOSED")
        self.assertTrue(self.package["authorization_gate"]["no_execution_from_this_prerun_package"])

    def test_f04_authorization_placeholder_is_bound_and_closed(self) -> None:
        artifact = self.package["artifacts"]["authorization_placeholder"]
        self.assertEqual(
            artifact["path"],
            "tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_v0_1.json",
        )
        self.assertEqual(artifact["required_status"], "NOT_APPROVED")
        self.assertEqual(self.auth["status"], "NOT_APPROVED")
        self.assertFalse(self.auth["execution_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])

    def test_f05_runner_and_authorization_git_blob_shas_are_bound(self) -> None:
        self.assertEqual(
            self.package["artifacts"]["runner"]["git_blob_sha"],
            "6024994b87220ef1631fbd63b3abbd11142f8783",
        )
        self.assertEqual(
            self.package["artifacts"]["authorization_placeholder"]["git_blob_sha"],
            "67a4d17b8b0d101f5f1c198691b2f04c760f6080",
        )

    def test_f06_semantic_architecture_is_unchanged(self) -> None:
        self.assertEqual(self.package["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertEqual(self.package["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertEqual(
            self.package["generic_system_composition_version"],
            "semantic-system-composition-v0.1",
        )
        self.assertEqual(self.package["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(self.package["non_profile_cases_boundary_only"])
        self.assertFalse(self.package["frozen_assets_changed"])

    def test_f07_transport_and_data_scope_are_fail_closed(self) -> None:
        self.assertEqual(self.package["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertTrue(self.package["synthetic_only"])
        self.assertTrue(self.package["local_loopback_only"])
        self.assertFalse(self.package["remote_cloud"])
        self.assertFalse(self.package["real_data"])
        self.assertTrue(self.package["authorization_gate"]["v13_authorization_reuse_forbidden"])

    def test_f08_local_identity_gate_requires_later_non_generation_verification(self) -> None:
        gate = self.package["local_identity_gate"]
        self.assertTrue(gate["download_or_install_is_separate_action"])
        self.assertTrue(gate["exact_loaded_model_id_must_be_verified_after_load"])
        self.assertEqual(gate["loaded_context_must_be_at_least"], 32768)
        self.assertEqual(gate["loaded_model_quantization_should_match_preferred"], "Q4_K_M")
        self.assertTrue(gate["no_generation_during_preflight"])


if __name__ == "__main__":
    unittest.main()
