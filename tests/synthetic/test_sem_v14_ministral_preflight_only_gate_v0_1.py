#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_preflight_only_v1_0 as preflight
import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as v13
import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14

ROOT = Path(__file__).resolve().parents[2]


class MinistralPreflightOnlyGateTests(unittest.TestCase):
    def test_r01_live_gate_matches_exact_preflight_only_approval(self) -> None:
        payload = json.loads(preflight.AUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "EXPLICIT_USER_APPROVED_PREFLIGHT_ONLY")
        self.assertTrue(payload["download_authorized"])
        self.assertTrue(payload["model_load_authorized"])
        self.assertTrue(payload["localhost_preflight_authorized"])
        self.assertTrue(payload["model_contact_authorized"])
        self.assertFalse(payload["generation_authorized"])
        self.assertFalse(payload["qualification_execution_authorized"])
        self.assertEqual(payload["generation_request_count_max"], 0)
        self.assertTrue(payload["single_use_preflight_only"])
        self.assertFalse(payload["authorization_consumed"])
        self.assertFalse(payload["model_qualified"])

    def test_r02_closed_gate_fails_before_any_preflight_contact(self) -> None:
        denied = {
            "status": "NOT_APPROVED",
            "preflight_version": preflight.PREFLIGHT_VERSION,
            "preflight_type": preflight.PREFLIGHT_TYPE,
            "model": preflight.MODEL,
            "required_quantization": preflight.REQUIRED_QUANTIZATION,
            "required_base_url": preflight.REQUIRED_BASE_URL,
            "required_loaded_context_length": preflight.REQUIRED_CONTEXT,
            "download_authorized": False,
            "model_load_authorized": False,
            "localhost_preflight_authorized": False,
            "model_contact_authorized": False,
            "generation_authorized": False,
            "qualification_execution_authorized": False,
            "generation_request_count_max": 0,
            "synthetic_only": True,
            "local_loopback_only": True,
            "remote_cloud": False,
            "real_data": False,
            "authorization_consumed": False,
        }
        with patch.object(preflight, "load", return_value=denied), patch.object(
            preflight.v09, "preflight_loaded_model"
        ) as contact:
            with self.assertRaises(PermissionError):
                preflight.perform_preflight_only()
            contact.assert_not_called()

    def test_r03_exact_base_url_is_enforced_before_contact(self) -> None:
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model"
        ) as contact:
            with self.assertRaises(PermissionError):
                preflight.perform_preflight_only(base_url="http://localhost:1234/v1")
            contact.assert_not_called()

    def test_r04_authorized_preflight_has_zero_generation_and_exact_identity(self) -> None:
        result = {
            "endpoint": "http://127.0.0.1:1234/api/v1/models",
            "loaded_instance_id": preflight.MODEL,
            "loaded_context_length": 32768,
            "required_loaded_context_length": 32768,
            "quantization": "Q4_K_M",
            "generation_request_count": 0,
        }
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model", return_value=result
        ) as contact:
            payload = preflight.perform_preflight_only()
        contact.assert_called_once_with(base_url=preflight.REQUIRED_BASE_URL, model=preflight.MODEL)
        self.assertEqual(payload["mode"], "PREFLIGHT_ONLY_PASSED")
        self.assertEqual(payload["generation_request_count"], 0)
        self.assertFalse(payload["generation_authorized"])
        self.assertFalse(payload["qualification_execution_authorized"])
        self.assertFalse(payload["model_qualified"])

    def test_r05_quantization_mismatch_fails_closed(self) -> None:
        result = {
            "loaded_instance_id": preflight.MODEL,
            "loaded_context_length": 32768,
            "quantization": "Q5_K_M",
            "generation_request_count": 0,
        }
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model", return_value=result
        ):
            with self.assertRaises(RuntimeError):
                preflight.perform_preflight_only()

    def test_r06_loaded_model_id_mismatch_fails_closed(self) -> None:
        result = {
            "loaded_instance_id": "some-other-model",
            "loaded_context_length": 32768,
            "quantization": "Q4_K_M",
            "generation_request_count": 0,
        }
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model", return_value=result
        ):
            with self.assertRaises(RuntimeError):
                preflight.perform_preflight_only()

    def test_r07_v14_runtime_guard_identity_is_explicitly_preserved(self) -> None:
        v14._install_bindings()
        base = v13.v11.v10.v09.base
        self.assertIs(base.evaluate_boundary, v13.evaluate_runtime_guard)

    def test_r08_preflight_module_contains_no_generation_call(self) -> None:
        source = (ROOT / "scripts/zs_ki_b_sem_ministral_preflight_only_v1_0.py").read_text(encoding="utf-8")
        self.assertNotIn("chat_completion_structured(", source)
        self.assertNotIn("for case in", source)
        self.assertIn("generation_request_count", source)


if __name__ == "__main__":
    unittest.main()
