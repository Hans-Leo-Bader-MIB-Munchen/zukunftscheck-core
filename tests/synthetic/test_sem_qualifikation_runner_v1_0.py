from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class SemQualificationRunnerV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = importlib.import_module("scripts.zs_ki_b_sem_qualifikation_runner_v1_0")

    def test_r01_timeout_is_explicitly_bound_to_1800_seconds(self) -> None:
        self.assertEqual(self.mod.REQUEST_TIMEOUT_SECONDS, 1800.0)

    def test_r02_dry_run_is_model_free_and_records_timeout(self) -> None:
        payload = self.mod.build_dry_run_manifest(model="qwen3-14b")
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_0")
        self.assertEqual(manifest["run_type"], self.mod.RUN_TYPE)
        self.assertEqual(manifest["runner_version"], "v1.0")
        self.assertEqual(manifest["request_timeout_seconds"], 1800)
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertFalse(manifest["execution_attempted"])

    def test_r03_pending_authorization_blocks_execution(self) -> None:
        with self.assertRaises(PermissionError):
            self.mod.validate_execution_authorization("qwen3-14b")

    def test_r04_approved_authorization_must_bind_timeout_and_model(self) -> None:
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "run_type": self.mod.RUN_TYPE,
            "model": "qwen3-14b",
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
        original_path = self.mod.AUTH_PATH
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.json"
            path.write_text(json.dumps(auth), encoding="utf-8")
            try:
                self.mod.AUTH_PATH = path
                accepted = self.mod.validate_execution_authorization("qwen3-14b")
                self.assertEqual(accepted["required_request_timeout_seconds"], 1800)
                with self.assertRaises(PermissionError):
                    self.mod.validate_execution_authorization("other-model")
                auth["required_request_timeout_seconds"] = 600
                path.write_text(json.dumps(auth), encoding="utf-8")
                with self.assertRaises(PermissionError):
                    self.mod.validate_execution_authorization("qwen3-14b")
            finally:
                self.mod.AUTH_PATH = original_path
                self.mod._configure_v09()

    def test_r05_transport_wrapper_passes_1800_seconds_without_real_model_call(self) -> None:
        captured = {}

        def fake_chat(**kwargs):
            captured.update(kwargs)
            return "{}", {"choices": []}

        original = self.mod._ORIGINAL_CHAT
        try:
            self.mod._ORIGINAL_CHAT = fake_chat
            self.mod.chat_completion_structured(
                base_url="http://127.0.0.1:1234/v1",
                model="qwen3-14b",
                messages=[],
                temperature=0.0,
            )
        finally:
            self.mod._ORIGINAL_CHAT = original
        self.assertEqual(captured["timeout_seconds"], 1800.0)
        self.assertEqual(captured["model"], "qwen3-14b")

    def test_r06_previous_timeout_incident_is_recorded_as_nonsemantic(self) -> None:
        incident = json.loads(self.mod.PREVIOUS_FAILURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(incident["failure_class"], "LOCAL_GENERATION_TIMEOUT")
        self.assertFalse(incident["model_response_observed"])
        self.assertFalse(incident["semantic_evaluation_reached"])
        self.assertFalse(incident["gold_evaluation_reached"])
        self.assertFalse(incident["rerun_authorized"])


if __name__ == "__main__":
    unittest.main()
