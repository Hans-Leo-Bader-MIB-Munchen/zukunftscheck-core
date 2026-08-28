from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_candidate_v0_1.json"


class TestSemV14MinistralAuthorizationCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))

    def test_a01_candidate_is_prepared_but_not_approved(self) -> None:
        self.assertEqual(self.candidate["status"], "PREPARED_NOT_APPROVED")
        self.assertTrue(self.candidate["explicit_user_approval_required"])
        self.assertFalse(self.candidate["execution_authorized"])
        self.assertFalse(self.candidate["model_run_authorized"])
        self.assertFalse(self.candidate["model_contact_authorized"])

    def test_a02_candidate_binds_merged_prerun_package(self) -> None:
        self.assertEqual(
            self.candidate["bound_main_commit"],
            "5b3d069298e507618dcb6f611640bdfe1c275c25",
        )
        self.assertEqual(
            self.candidate["prerun_package"]["git_blob_sha"],
            "917f411028ea501782d582719b31bccc3b91eb9a",
        )

    def test_a03_exact_run_identity_is_bound(self) -> None:
        self.assertEqual(self.candidate["runner_version"], "v1.4")
        self.assertEqual(
            self.candidate["run_type"],
            "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015",
        )
        self.assertEqual(
            self.candidate["model"],
            "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        )
        self.assertEqual(self.candidate["preferred_quantization"], "Q4_K_M")

    def test_a04_one_shot_constraints_are_unchanged(self) -> None:
        self.assertEqual(self.candidate["expected_model_request_count"], 16)
        self.assertEqual(self.candidate["required_loaded_context_length"], 32768)
        self.assertEqual(self.candidate["required_request_timeout_seconds"], 1800)
        self.assertTrue(self.candidate["single_run_only"])
        self.assertEqual(self.candidate["retry_count"], 0)
        self.assertFalse(self.candidate["output_repair"])

    def test_a05_semantic_architecture_is_unchanged(self) -> None:
        self.assertEqual(self.candidate["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertEqual(self.candidate["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertEqual(
            self.candidate["generic_system_composition_version"],
            "semantic-system-composition-v0.1",
        )
        self.assertEqual(self.candidate["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(self.candidate["non_profile_cases_boundary_only"])

    def test_a06_local_identity_preflight_is_still_open(self) -> None:
        self.assertTrue(self.candidate["local_identity_preflight_required"])
        self.assertFalse(self.candidate["local_identity_preflight_completed"])
        self.assertIsNone(self.candidate["exact_loaded_model_id"])
        self.assertIsNone(self.candidate["observed_loaded_context_length"])
        self.assertIsNone(self.candidate["observed_quantization"])

    def test_a07_no_install_load_or_preflight_is_authorized(self) -> None:
        self.assertFalse(self.candidate["download_authorized"])
        self.assertFalse(self.candidate["model_load_authorized"])
        self.assertFalse(self.candidate["localhost_preflight_authorized"])
        self.assertFalse(self.candidate["model_contact_performed"])
        self.assertTrue(self.candidate["v13_authorization_reuse_forbidden"])

    def test_a08_next_gate_requires_separate_local_preflight_authorization(self) -> None:
        self.assertEqual(
            self.candidate["next_gate"],
            "SEPARATE_LOCAL_MODEL_INSTALL_LOAD_PREFLIGHT_AUTHORIZATION",
        )
        self.assertTrue(self.candidate["single_use_authorization_required"])
        self.assertFalse(self.candidate["authorization_consumed"])
        self.assertFalse(self.candidate["model_qualified"])


if __name__ == "__main__":
    unittest.main()
