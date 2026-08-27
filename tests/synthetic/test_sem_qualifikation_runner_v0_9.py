from __future__ import annotations

import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class _FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


class SemQualificationRunnerV09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = importlib.import_module("scripts.zs_ki_b_sem_qualifikation_runner_v0_9")

    def _auth(self, *, status: str = "EXPLICIT_USER_APPROVED", model: str = "qwen3-14b") -> dict:
        return {
            "status": status,
            "run_type": self.mod.RUN_TYPE,
            "model": model,
            "required_loaded_context_length": 32768,
            "expected_model_request_count": 16,
            "synthetic_only": True,
            "local_loopback_only": True,
            "single_run_only": True,
            "retry_count": 0,
            "output_repair": False,
            "remote_cloud": False,
            "real_data": False,
        }

    def _models_payload(self, *, model: str = "qwen3-14b", context: int = 32768) -> dict:
        return {
            "models": [{
                "type": "llm",
                "key": model,
                "quantization": {"name": "Q6_K", "bits_per_weight": 6},
                "loaded_instances": [{"id": model, "config": {"context_length": context, "parallel": 4}}],
                "max_context_length": 40960,
                "format": "gguf",
            }]
        }

    def test_r01_new_run_is_separately_versioned(self) -> None:
        self.assertEqual(self.mod.RUNNER_VERSION, "v0.9")
        self.assertTrue(self.mod.RUN_TYPE.endswith("2026-009"))
        self.assertEqual(self.mod.REQUIRED_LOADED_CONTEXT_LENGTH, 32768)

    def test_r02_pending_authorization_is_not_execution_authorization(self) -> None:
        payload = self.mod.build_dry_run_manifest(model="qwen3-14b")
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V0_9")
        self.assertFalse(payload["manifest"]["execution_attempted"])
        self.assertFalse(payload["manifest"]["execution_authorized"])
        self.assertEqual(payload["manifest"]["observed_model_request_count"], 0)

    def test_r03_exact_model_identifier_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / "auth.json"
            auth_path.write_text(json.dumps(self._auth(model="qwen3-14b")), encoding="utf-8")
            with patch.object(self.mod, "AUTH_PATH", auth_path):
                self.mod.validate_execution_authorization("qwen3-14b")
                with self.assertRaisesRegex(PermissionError, "authorized model mismatch"):
                    self.mod.validate_execution_authorization("qwen/qwen3-8b")

    def test_r04_pending_status_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / "auth.json"
            auth_path.write_text(json.dumps(self._auth(status="PENDING_USER_APPROVAL")), encoding="utf-8")
            with patch.object(self.mod, "AUTH_PATH", auth_path):
                with self.assertRaisesRegex(PermissionError, "not EXPLICIT_USER_APPROVED"):
                    self.mod.validate_execution_authorization("qwen3-14b")

    def test_r05_preflight_accepts_exact_loaded_model_at_32768(self) -> None:
        fake = _FakeHttpResponse(self._models_payload(context=32768))
        with patch.object(self.mod.urllib.request, "urlopen", return_value=fake):
            result = self.mod.preflight_loaded_model(
                base_url="http://127.0.0.1:1234/v1", model="qwen3-14b"
            )
        self.assertEqual(result["loaded_instance_id"], "qwen3-14b")
        self.assertEqual(result["loaded_context_length"], 32768)
        self.assertEqual(result["generation_request_count"], 0)

    def test_r06_preflight_rejects_8192_before_generation(self) -> None:
        fake = _FakeHttpResponse(self._models_payload(context=8192))
        with patch.object(self.mod.urllib.request, "urlopen", return_value=fake):
            with self.assertRaisesRegex(RuntimeError, "loaded context too small"):
                self.mod.preflight_loaded_model(
                    base_url="http://127.0.0.1:1234/v1", model="qwen3-14b"
                )

    def test_r07_preflight_rejects_different_loaded_identifier(self) -> None:
        fake = _FakeHttpResponse(self._models_payload(model="qwen/qwen3-8b", context=32768))
        with patch.object(self.mod.urllib.request, "urlopen", return_value=fake):
            with self.assertRaisesRegex(RuntimeError, "is not loaded"):
                self.mod.preflight_loaded_model(
                    base_url="http://127.0.0.1:1234/v1", model="qwen3-14b"
                )

    def test_r08_cloud_endpoint_is_rejected_before_preflight(self) -> None:
        with self.assertRaises(Exception):
            self.mod.preflight_loaded_model(base_url="https://api.anthropic.com/v1", model="qwen3-14b")

    def test_r09_previous_failure_is_recorded_as_nonsemantic(self) -> None:
        incident = json.loads(self.mod.PREVIOUS_FAILURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(incident["failure_class"], "LOCAL_CONTEXT_WINDOW_TOO_SMALL")
        self.assertFalse(incident["model_response_observed"])
        self.assertFalse(incident["semantic_evaluation_reached"])
        self.assertFalse(incident["rerun_authorized"])


if __name__ == "__main__":
    unittest.main()
