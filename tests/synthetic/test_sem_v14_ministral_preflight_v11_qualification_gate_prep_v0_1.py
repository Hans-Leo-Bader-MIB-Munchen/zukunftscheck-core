from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_preflight_only_v1_1 as preflight
import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14

ROOT = Path(__file__).resolve().parents[2]


class MinistralPreflightV11QualificationGatePrepTests(unittest.TestCase):
    def _consumed_preflight_auth(self) -> dict:
        return json.loads(preflight.AUTH_PATH.read_text(encoding="utf-8"))

    def _hypothetical_approved_preflight_auth(self) -> dict:
        auth = copy.deepcopy(self._consumed_preflight_auth())
        auth["status"] = "EXPLICIT_USER_APPROVED_PREFLIGHT_ONLY"
        auth["localhost_preflight_authorized"] = True
        auth["model_contact_authorized"] = True
        auth["authorization_consumed"] = False
        return auth

    def test_p01_current_preflight_authorization_is_consumed_but_pass_is_preserved(self) -> None:
        auth = self._consumed_preflight_auth()
        self.assertEqual(auth["status"], "CONSUMED")
        self.assertEqual(auth["model_repository"], v14.MODEL_REPOSITORY)
        self.assertEqual(auth["runtime_model_id"], v14.RUNTIME_MODEL_ID)
        self.assertFalse(auth["localhost_preflight_authorized"])
        self.assertFalse(auth["model_contact_authorized"])
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["preflight_pass_observed"])
        self.assertEqual(auth["observed_inventory_request_count"], 1)
        self.assertEqual(auth["observed_generation_request_count"], 0)
        self.assertFalse(auth["model_qualified"])

    def test_p02_consumed_gate_stops_before_preflight_contact(self) -> None:
        with patch.object(preflight.v09, "preflight_loaded_model") as contact:
            with self.assertRaises(PermissionError):
                preflight.perform_preflight_only()
            contact.assert_not_called()

    def test_p03_wrong_base_url_stops_before_preflight_contact(self) -> None:
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model"
        ) as contact:
            with self.assertRaises(PermissionError):
                preflight.perform_preflight_only(base_url="http://localhost:1234/v1")
            contact.assert_not_called()

    def test_p04_historical_approved_shape_still_matches_when_reconstructed(self) -> None:
        auth = self._hypothetical_approved_preflight_auth()
        self.assertTrue(preflight._authorization_matches(auth))
        altered = copy.deepcopy(auth)
        altered["runtime_model_id"] = v14.MODEL_REPOSITORY
        self.assertFalse(preflight._authorization_matches(altered))

    def test_p05_mocked_preflight_passes_with_zero_generation(self) -> None:
        observed = {
            "loaded_instance_id": v14.RUNTIME_MODEL_ID,
            "loaded_context_length": 32768,
            "quantization": "Q4_K_M",
            "generation_request_count": 0,
        }
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model", return_value=observed
        ) as contact:
            result = preflight.perform_preflight_only()
        contact.assert_called_once_with(base_url=preflight.REQUIRED_BASE_URL, model=v14.RUNTIME_MODEL_ID)
        self.assertEqual(result["mode"], "PREFLIGHT_ONLY_V1_1_PASSED")
        self.assertEqual(result["inventory_request_count"], 1)
        self.assertEqual(result["generation_request_count"], 0)
        self.assertFalse(result["qualification_execution_authorized"])
        self.assertFalse(result["model_qualified"])

    def test_p06_mismatched_runtime_id_fails_closed(self) -> None:
        observed = {
            "loaded_instance_id": "wrong-runtime-id",
            "loaded_context_length": 32768,
            "quantization": "Q4_K_M",
            "generation_request_count": 0,
        }
        with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
            preflight.v09, "preflight_loaded_model", return_value=observed
        ):
            with self.assertRaises(RuntimeError):
                preflight.perform_preflight_only()

    def test_p07_quantization_and_context_fail_closed(self) -> None:
        for observed in (
            {
                "loaded_instance_id": v14.RUNTIME_MODEL_ID,
                "loaded_context_length": 32768,
                "quantization": "Q5_K_M",
                "generation_request_count": 0,
            },
            {
                "loaded_instance_id": v14.RUNTIME_MODEL_ID,
                "loaded_context_length": 16384,
                "quantization": "Q4_K_M",
                "generation_request_count": 0,
            },
        ):
            with patch.object(preflight, "validate_preflight_authorization", return_value={}), patch.object(
                preflight.v09, "preflight_loaded_model", return_value=observed
            ):
                with self.assertRaises(RuntimeError):
                    preflight.perform_preflight_only()

    def test_p08_current_v14_qualification_authorization_is_consumed_and_closed(self) -> None:
        auth = v14.load(v14.AUTH_PATH)
        self.assertEqual(auth["status"], "CONSUMED_EXECUTED_ONCE_FAILED_TIMEOUT")
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["preflight_pass_required"])
        self.assertTrue(auth["preflight_pass_observed"])
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["model_run_authorized"])
        self.assertFalse(auth["model_contact_authorized"])

    def test_p09_hypothetical_fresh_qualification_auth_still_requires_preflight_pass(self) -> None:
        auth = copy.deepcopy(v14.load(v14.AUTH_PATH))
        auth["status"] = "EXPLICIT_USER_APPROVED"
        auth["authorization_consumed"] = False
        auth["execution_authorized"] = True
        auth["model_run_authorized"] = True
        auth["model_contact_authorized"] = True
        auth["preflight_pass_observed"] = False
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))
        auth["preflight_pass_observed"] = True
        self.assertTrue(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))

    def test_p10_preflight_source_contains_no_generation_path(self) -> None:
        source = (ROOT / "scripts/zs_ki_b_sem_ministral_preflight_only_v1_1.py").read_text(encoding="utf-8")
        self.assertNotIn("chat_completion_structured(", source)
        self.assertNotIn("/chat/completions", source)
        self.assertIn("preflight_loaded_model", source)
        self.assertIn("RUNTIME_MODEL_ID", source)
        self.assertIn("generation_request_count", source)


if __name__ == "__main__":
    unittest.main()
