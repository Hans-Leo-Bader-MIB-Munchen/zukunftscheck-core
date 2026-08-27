from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path


class SemModelComparisonGemmaV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = importlib.import_module("scripts.zs_ki_b_sem_model_comparison_runner_gemma_v0_1")

    @classmethod
    def tearDownClass(cls) -> None:
        # The comparison wrapper deliberately reuses historical runner modules.
        # Reload them bottom-up after this class so full-suite test order cannot
        # inherit any transient comparison binding or nested _configure() state.
        base = cls.mod.v11.v10.v09.base
        v09 = cls.mod.v11.v10.v09
        v10 = cls.mod.v11.v10
        v11 = cls.mod.v11
        importlib.reload(base)
        importlib.reload(v09)
        importlib.reload(v10)
        importlib.reload(v11)

    def test_g01_exact_gemma_model_is_bound(self) -> None:
        self.assertEqual(self.mod.MODEL, "gemma-3-12b-it-qat")
        self.assertEqual(self.mod.PROMPT_VERSION, "zs_ki_b_sem_qualifikation_system_v0_6")

    def test_g02_pending_authorization_blocks_execution(self) -> None:
        auth = {
            "status": "PENDING_USER_APPROVAL",
            "run_type": self.mod.RUN_TYPE,
            "model": self.mod.MODEL,
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
            "comparison_plan_version": self.mod.COMPARISON_PLAN_VERSION,
            "qwen3_14b_rerun_authorized": False,
        }
        original = self.mod.AUTH_PATH
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.json"
            path.write_text(json.dumps(auth), encoding="utf-8")
            try:
                self.mod.AUTH_PATH = path
                with self.assertRaises(PermissionError):
                    self.mod.validate_execution_authorization(self.mod.MODEL)
            finally:
                self.mod.AUTH_PATH = original

    def test_g03_wrong_model_is_blocked_even_with_approved_auth(self) -> None:
        with self.assertRaises(PermissionError):
            self.mod.validate_execution_authorization("qwen3-14b")

    def test_g04_dry_run_is_model_free_and_records_comparison(self) -> None:
        before_v10_version = self.mod.v11.v10.RUNNER_VERSION
        before_v11_version = self.mod.v11.RUNNER_VERSION
        payload = self.mod.build_dry_run_manifest(model=self.mod.MODEL)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_MODEL_COMPARISON_GEMMA_V0_1")
        self.assertEqual(manifest["comparison_model"], self.mod.MODEL)
        self.assertEqual(manifest["reference_model"], "qwen3-14b")
        self.assertFalse(manifest["execution_attempted"])
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertEqual(self.mod.v11.v10.RUNNER_VERSION, before_v10_version)
        self.assertEqual(self.mod.v11.RUNNER_VERSION, before_v11_version)

    def test_g05_frozen_semantic_assets_remain_reused_without_state_leak(self) -> None:
        base = self.mod.v11.v10.v09.base
        before_version = base.RUNNER_VERSION
        before_failure = self.mod.v11.v10.v09.PREVIOUS_FAILURE_PATH
        with self.mod._temporary_bindings():
            self.assertTrue(base.SUITE_PATH.name.endswith("qualification_suite_frozen_v0_1.json"))
            self.assertTrue(base.GOLD_PATH.name.endswith("human_gold_frozen_v0_1.json"))
            self.assertTrue(base.POLICY_PATH.name.endswith("qualification_policy_frozen_v0_1.json"))
            self.assertTrue(base.MEANINGS_PATH.name.endswith("reference_question_meanings_v0_7.json"))
            self.assertEqual(base.CONTRACT_VERSION, "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")
            self.assertEqual(base.RUNNER_VERSION, self.mod.RUNNER_VERSION)
        self.assertEqual(base.RUNNER_VERSION, before_version)
        self.assertEqual(self.mod.v11.v10.v09.PREVIOUS_FAILURE_PATH, before_failure)


if __name__ == "__main__":
    unittest.main()
