from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path


class SemQualificationRunnerV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = importlib.import_module("scripts.zs_ki_b_sem_qualifikation_runner_v1_1")

    def test_r01_prompt_v06_is_bound(self) -> None:
        self.mod._configure()
        self.assertEqual(self.mod.PROMPT_VERSION, "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertTrue(self.mod.PROMPT_PATH.name.endswith("v0_6.txt"))
        self.assertEqual(self.mod.v10.v09.base.PROMPT_VERSION, self.mod.PROMPT_VERSION)
        self.assertEqual(self.mod.v10.v09.base.PROMPT_PATH, self.mod.PROMPT_PATH)

    def test_r02_pending_authorization_blocks_execution(self) -> None:
        with self.assertRaises(PermissionError):
            self.mod.validate_execution_authorization("qwen3-14b")

    def test_r03_authorization_must_bind_prompt_v06(self) -> None:
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "run_type": self.mod.RUN_TYPE,
            "model": "qwen3-14b",
            "prompt_version": self.mod.PROMPT_VERSION,
            "required_loaded_context_length": 32768,
            "required_request_timeout_seconds": 1800,
            "expected_model_request_count": 16,
            "synthetic_only": True,
            "local_loopback_only": True,
            "single_run_only": True,
            "retry_count": 0,
            "output_repair": False,
            "remote_cloud": False,
            "real_data": False,
        }
        original = self.mod.AUTH_PATH
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.json"
            path.write_text(json.dumps(auth), encoding="utf-8")
            try:
                self.mod.AUTH_PATH = path
                accepted = self.mod.validate_execution_authorization("qwen3-14b")
                self.assertEqual(accepted["prompt_version"], self.mod.PROMPT_VERSION)
                auth["prompt_version"] = "zs_ki_b_sem_qualifikation_system_v0_5"
                path.write_text(json.dumps(auth), encoding="utf-8")
                with self.assertRaises(PermissionError):
                    self.mod.validate_execution_authorization("qwen3-14b")
            finally:
                self.mod.AUTH_PATH = original
                self.mod._configure()

    def test_r04_configuration_reuses_frozen_semantic_assets(self) -> None:
        self.mod._configure()
        base = self.mod.v10.v09.base
        self.assertTrue(base.SUITE_PATH.name.endswith("qualification_suite_frozen_v0_1.json"))
        self.assertTrue(base.GOLD_PATH.name.endswith("human_gold_frozen_v0_1.json"))
        self.assertTrue(base.POLICY_PATH.name.endswith("qualification_policy_frozen_v0_1.json"))
        self.assertTrue(base.MEANINGS_PATH.name.endswith("reference_question_meanings_v0_7.json"))
        self.assertEqual(base.CONTRACT_VERSION, "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")

    def test_r05_dry_run_declares_prompt_change_only_and_no_execution(self) -> None:
        payload = self.mod.build_dry_run_manifest(model="qwen3-14b")
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_1")
        self.assertEqual(manifest["runner_version"], "v1.1")
        self.assertEqual(manifest["prompt_version"], self.mod.PROMPT_VERSION)
        self.assertTrue(manifest["prompt_change_only"])
        self.assertFalse(manifest["execution_attempted"])
        self.assertFalse(manifest["execution_authorized"])
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertTrue(manifest["previous_semantic_failure_recorded"])


if __name__ == "__main__":
    unittest.main()
