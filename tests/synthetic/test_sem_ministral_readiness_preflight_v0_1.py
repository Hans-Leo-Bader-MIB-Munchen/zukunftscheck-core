from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ministral_readiness_preflight_v0_1.json"


class TestSemMinistralReadinessPreflightV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_p01_plan_is_model_free_and_not_authorized(self) -> None:
        self.assertEqual(cls := self.plan["status"], "MODEL_FREE_READINESS_PLAN_NOT_AUTHORIZED")
        self.assertFalse(self.plan["download_authorized"])
        self.assertFalse(self.plan["model_load_authorized"])
        self.assertFalse(self.plan["localhost_preflight_authorized"])
        self.assertFalse(self.plan["model_contact_authorized"])
        self.assertFalse(self.plan["execution_authorized"])

    def test_p02_candidate_and_context_are_bound(self) -> None:
        self.assertEqual(
            self.plan["selected_candidate"],
            "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        )
        self.assertEqual(self.plan["preferred_quantization"], "Q4_K_M")
        self.assertEqual(self.plan["required_project_context_length"], 32768)

    def test_p03_new_runner_and_auth_path_are_required(self) -> None:
        self.assertEqual(self.plan["future_runner_version"], "v1.4")
        self.assertIn("v1_4", self.plan["future_runner_path"])
        self.assertIn("v14", self.plan["future_authorization_path"])
        self.assertTrue(self.plan["separate_single_use_authorization_required"])
        self.assertTrue(self.plan["v13_authorization_reuse_forbidden"])

    def test_p04_one_shot_execution_constraints_are_preserved(self) -> None:
        self.assertEqual(self.plan["expected_model_request_count"], 16)
        self.assertEqual(self.plan["retry_count"], 0)
        self.assertFalse(self.plan["output_repair"])
        self.assertEqual(self.plan["required_request_timeout_seconds"], 1800)
        self.assertTrue(self.plan["synthetic_only"])
        self.assertTrue(self.plan["local_loopback_only"])
        self.assertFalse(self.plan["remote_cloud"])
        self.assertFalse(self.plan["real_data"])

    def test_p05_semantic_architecture_is_unchanged(self) -> None:
        self.assertEqual(self.plan["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertEqual(self.plan["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertEqual(
            self.plan["generic_system_composition_version"],
            "semantic-system-composition-v0.1",
        )
        self.assertEqual(self.plan["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(self.plan["non_profile_cases_boundary_only"])
        self.assertFalse(self.plan["frozen_assets_changed"])

    def test_p06_exact_loaded_model_and_context_must_be_checked_later(self) -> None:
        self.assertTrue(self.plan["exact_loaded_model_id_must_be_frozen_later"])
        self.assertTrue(self.plan["loaded_context_must_be_checked_before_generation"])
        self.assertEqual(self.plan["required_base_url"], "http://127.0.0.1:1234/v1")

    def test_p07_next_gate_is_model_free_runner_v14_binding(self) -> None:
        self.assertEqual(self.plan["next_gate"], "MODEL_FREE_RUNNER_V1_4_MINISTRAL_BINDING")
        self.assertFalse(self.plan["qualification_run_authorized"])
        self.assertFalse(self.plan["model_qualified"])


if __name__ == "__main__":
    unittest.main()
