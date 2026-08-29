from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as runner

ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_v0_1.json"
AUDIT_TEST_COMMIT = "0" * 40


class TestSemQualificationRunnerV14MinistralBinding(unittest.TestCase):
    def test_r01_runner_identity_and_model_are_new(self) -> None:
        self.assertEqual(runner.RUNNER_VERSION, "v1.4")
        self.assertEqual(
            runner.RUN_TYPE,
            "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015",
        )
        self.assertEqual(
            runner.MODEL_REPOSITORY,
            "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        )
        self.assertEqual(runner.RUNTIME_MODEL_ID, "ministral-3-14b-instruct-2512")
        self.assertEqual(runner.MODEL, runner.RUNTIME_MODEL_ID)

    def test_r02_authorization_is_consumed_and_closed_after_timeout(self) -> None:
        auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "CONSUMED_EXECUTED_ONCE_FAILED_TIMEOUT")
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["model_run_authorized"])
        self.assertFalse(auth["model_contact_authorized"])
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["model_contact_performed"])
        self.assertEqual(auth["observed_model_request_count"], 1)

    def test_r03_execution_validation_fails_closed_after_consumption(self) -> None:
        with self.assertRaises(PermissionError):
            runner.validate_execution_authorization(runner.MODEL)

    def test_r04_wrong_model_cannot_be_authorized(self) -> None:
        auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        auth["status"] = "EXPLICIT_USER_APPROVED"
        auth["execution_authorized"] = True
        auth["model_run_authorized"] = True
        auth["model_contact_authorized"] = True
        auth["authorization_consumed"] = False
        self.assertFalse(runner._authorization_matches(auth, "qwen3-14b"))

    def test_r05_dry_run_manifest_preserves_semantic_architecture(self) -> None:
        with patch(
            "scripts.zs_ki_b_sem_qualifikation_runner_v0_8.current_git_commit",
            return_value=AUDIT_TEST_COMMIT,
        ):
            payload = runner.build_dry_run_manifest(model=runner.MODEL)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_4")
        self.assertEqual(manifest["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertEqual(manifest["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertEqual(
            manifest["generic_system_composition_version"],
            "semantic-system-composition-v0.1",
        )
        self.assertEqual(manifest["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(manifest["non_profile_cases_boundary_only"])

    def test_r06_dry_run_never_authorizes_execution(self) -> None:
        with patch(
            "scripts.zs_ki_b_sem_qualifikation_runner_v0_8.current_git_commit",
            return_value=AUDIT_TEST_COMMIT,
        ):
            payload = runner.build_dry_run_manifest(model=runner.MODEL)
        manifest = payload["manifest"]
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertTrue(manifest["v13_authorization_reuse_forbidden"])

    def test_r07_one_shot_constraints_are_bound(self) -> None:
        auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(auth["expected_model_request_count"], 16)
        self.assertEqual(auth["required_loaded_context_length"], 32768)
        self.assertEqual(auth["required_request_timeout_seconds"], 1800)
        self.assertTrue(auth["single_run_only"])
        self.assertEqual(auth["retry_count"], 0)
        self.assertFalse(auth["output_repair"])
        self.assertTrue(auth["synthetic_only"])
        self.assertTrue(auth["local_loopback_only"])
        self.assertFalse(auth["remote_cloud"])
        self.assertFalse(auth["real_data"])


if __name__ == "__main__":
    unittest.main()
