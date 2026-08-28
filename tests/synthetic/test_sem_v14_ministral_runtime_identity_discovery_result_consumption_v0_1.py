from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_runtime_identity_discovery_v1_0 as discovery

ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_runtime_identity_discovery_authorization_v0_1.json"
RESULT_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_runtime_identity_discovery_result_v0_1.json"


class MinistralRuntimeIdentityDiscoveryResultConsumptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        self.result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    def test_c01_authorization_is_consumed_and_contact_gate_closed(self) -> None:
        self.assertEqual(self.auth["status"], "CONSUMED")
        self.assertTrue(self.auth["authorization_consumed"])
        self.assertFalse(self.auth["localhost_inventory_contact_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])
        self.assertFalse(self.auth["generation_authorized"])
        self.assertFalse(self.auth["qualification_execution_authorized"])

    def test_c02_consumed_gate_blocks_second_contact(self) -> None:
        with patch.object(discovery.urllib.request, "urlopen") as contact:
            with self.assertRaises(PermissionError):
                discovery.perform_discovery_only()
            contact.assert_not_called()

    def test_c03_exact_observation_is_preserved(self) -> None:
        row = self.result["loaded_instances"][0]
        self.assertEqual(row["runtime_instance_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(row["model_key"], "ministral-3-14b-instruct-2512")
        self.assertEqual(row["quantization"], "Q4_K_M")
        self.assertEqual(row["loaded_context_length"], 32768)
        self.assertEqual(row["max_context_length"], 262144)
        self.assertEqual(row["format"], "gguf")

    def test_c04_one_inventory_zero_generation_no_qualification(self) -> None:
        self.assertEqual(self.result["inventory_request_count"], 1)
        self.assertEqual(self.result["generation_request_count"], 0)
        self.assertFalse(self.result["generation_authorized"])
        self.assertFalse(self.result["qualification_execution_authorized"])
        self.assertFalse(self.result["model_qualified"])

    def test_c05_observation_is_not_binding(self) -> None:
        self.assertFalse(self.result["runtime_identity_bound"])
        self.assertTrue(self.result["binding_requires_separate_model_free_review"])
        self.assertFalse(self.auth["runtime_identity_bound"])
        self.assertFalse(self.auth["new_binding_authorization_granted"])

    def test_c06_execution_commit_is_not_inferred(self) -> None:
        self.assertIsNone(self.result["execution_main_commit"])
        self.assertIsNone(self.auth["execution_main_commit"])
        self.assertIn("not", self.result["execution_main_commit_note"].lower())


if __name__ == "__main__":
    unittest.main()
