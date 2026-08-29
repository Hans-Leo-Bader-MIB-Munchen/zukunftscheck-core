from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_preflight_only_v1_1 as preflight
import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_result_v1_1_preserved_v0_1.json"


class MinistralPreflightV11PassConsumptionTests(unittest.TestCase):
    def test_c01_preflight_authorization_is_consumed_and_closed(self) -> None:
        auth = json.loads(preflight.AUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "CONSUMED")
        self.assertTrue(auth["authorization_consumed"])
        self.assertFalse(auth["localhost_preflight_authorized"])
        self.assertFalse(auth["model_contact_authorized"])
        self.assertFalse(auth["generation_authorized"])
        self.assertFalse(auth["qualification_execution_authorized"])

    def test_c02_consumed_preflight_cannot_contact_again(self) -> None:
        with patch.object(preflight.v09, "preflight_loaded_model") as contact:
            with self.assertRaises(PermissionError):
                preflight.perform_preflight_only()
            contact.assert_not_called()

    def test_c03_preserved_result_matches_observed_identity_and_runtime(self) -> None:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PRESERVED_PREFLIGHT_PASS")
        self.assertEqual(result["runtime_model_id"], v14.RUNTIME_MODEL_ID)
        self.assertEqual(result["preflight"]["model_key"], v14.RUNTIME_MODEL_ID)
        self.assertEqual(result["preflight"]["loaded_instance_id"], v14.RUNTIME_MODEL_ID)
        self.assertEqual(result["preflight"]["quantization"], "Q4_K_M")
        self.assertEqual(result["preflight"]["loaded_context_length"], 32768)
        self.assertEqual(result["preflight"]["max_context_length"], 262144)
        self.assertEqual(result["preflight"]["format"], "gguf")

    def test_c04_exactly_one_inventory_and_zero_generation_are_preserved(self) -> None:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(result["inventory_request_count"], 1)
        self.assertEqual(result["generation_request_count"], 0)
        self.assertFalse(result["generation_authorized"])
        self.assertFalse(result["qualification_execution_authorized"])
        self.assertFalse(result["model_qualified"])

    def test_c05_qualification_gate_records_preflight_pass_and_current_consumed_v14_state(self) -> None:
        auth = v14.load(v14.AUTH_PATH)
        self.assertEqual(auth["status"], "CONSUMED_EXECUTED_ONCE_FAILED_TIMEOUT")
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["preflight_pass_required"])
        self.assertTrue(auth["preflight_pass_observed"])
        self.assertFalse(auth["qualification_authorization_ready_for_separate_user_decision"])
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["model_run_authorized"])
        self.assertFalse(auth["model_contact_authorized"])
        self.assertTrue(auth["model_contact_performed"])
        self.assertFalse(auth["model_qualified"])

    def test_c06_current_qualification_authorization_still_fails_closed(self) -> None:
        auth = v14.load(v14.AUTH_PATH)
        self.assertFalse(v14._authorization_matches(auth, v14.RUNTIME_MODEL_ID))
        with self.assertRaises(PermissionError):
            v14.validate_execution_authorization(v14.RUNTIME_MODEL_ID)

    def test_c07_execution_commit_is_not_inferred(self) -> None:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        preflight_auth = json.loads(preflight.AUTH_PATH.read_text(encoding="utf-8"))
        self.assertIsNone(result["execution_main_commit"])
        self.assertIsNone(preflight_auth["execution_main_commit"])


if __name__ == "__main__":
    unittest.main()
