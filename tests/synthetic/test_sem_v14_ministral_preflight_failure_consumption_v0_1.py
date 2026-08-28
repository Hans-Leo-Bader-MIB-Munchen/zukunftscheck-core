from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_v0_1.json"
FAILURE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_failure_manifest_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemV14MinistralPreflightFailureConsumptionV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auth = load(AUTH_PATH)
        cls.failure = load(FAILURE_PATH)

    def test_p01_authorization_is_consumed_and_all_contact_gates_closed(self) -> None:
        a = self.auth
        self.assertEqual(a["status"], "CONSUMED")
        self.assertTrue(a["authorization_consumed"])
        self.assertFalse(a["download_authorized"])
        self.assertFalse(a["model_load_authorized"])
        self.assertFalse(a["localhost_preflight_authorized"])
        self.assertFalse(a["model_contact_authorized"])
        self.assertFalse(a["generation_authorized"])
        self.assertFalse(a["qualification_execution_authorized"])

    def test_p02_exactly_one_preflight_contact_and_zero_generation_are_preserved(self) -> None:
        a = self.auth
        f = self.failure
        self.assertEqual(a["observed_preflight_contact_count"], 1)
        self.assertEqual(f["observed_preflight_contact_count"], 1)
        self.assertEqual(a["observed_generation_request_count"], 0)
        self.assertEqual(f["observed_generation_request_count"], 0)
        self.assertFalse(f["qualification_run_started"])

    def test_p03_identity_binding_failure_is_preserved_exactly(self) -> None:
        expected = "authorized model instance 'mistralai/Ministral-3-14B-Instruct-2512-GGUF' is not loaded in LM Studio"
        self.assertEqual(self.auth["preflight_outcome"], "EXECUTED_ONCE_FAILED_IDENTITY_BINDING")
        self.assertEqual(self.failure["outcome"], "EXECUTED_ONCE_FAILED_IDENTITY_BINDING")
        self.assertEqual(self.auth["failure_classification"], "IDENTITY_BINDING_MISMATCH")
        self.assertEqual(self.failure["failure_classification"], "IDENTITY_BINDING_MISMATCH")
        self.assertEqual(self.auth["failure_message"], expected)
        self.assertEqual(self.failure["failure_message"], expected)

    def test_p04_exact_loaded_model_id_remains_unresolved_not_inferred_from_ui(self) -> None:
        self.assertIsNone(self.auth["exact_loaded_model_id_observed"])
        self.assertIsNone(self.failure["exact_loaded_model_id_observed"])
        self.assertEqual(self.failure["ui_observation_only_not_authoritative"], "ministral-3-14b-instruct-2512")

    def test_p05_no_new_preflight_or_qualification_authorization_is_created(self) -> None:
        self.assertFalse(self.auth["new_preflight_authorization_granted"])
        self.assertFalse(self.auth["new_qualification_authorization_granted"])
        self.assertFalse(self.failure["generation_authorized"])
        self.assertFalse(self.failure["qualification_execution_authorized"])
        self.assertFalse(self.failure["model_qualified"])

    def test_p06_provenance_is_bound_to_authorized_execution_main(self) -> None:
        expected_commit = "d604207e7ddfa5e76ac62c16bbabb2a846d1dd03"
        self.assertEqual(self.auth["executed_on_main_commit"], expected_commit)
        self.assertEqual(self.failure["executed_on_main_commit"], expected_commit)
        self.assertEqual(self.failure["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(self.failure["required_quantization"], "Q4_K_M")
        self.assertEqual(self.failure["required_loaded_context_length"], 32768)


if __name__ == "__main__":
    unittest.main()
