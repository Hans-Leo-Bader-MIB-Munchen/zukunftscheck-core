from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_runtime_identity_discovery_v1_0 as discovery

ROOT = Path(__file__).resolve().parents[2]


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._raw


class MinistralRuntimeIdentityDiscoveryTests(unittest.TestCase):
    def test_d01_live_gate_matches_exact_discovery_only_approval(self) -> None:
        auth = json.loads(discovery.AUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "EXPLICIT_USER_APPROVED_DISCOVERY_ONLY")
        self.assertTrue(auth["localhost_inventory_contact_authorized"])
        self.assertTrue(auth["model_contact_authorized"])
        self.assertFalse(auth["generation_authorized"])
        self.assertFalse(auth["qualification_execution_authorized"])
        self.assertEqual(auth["generation_request_count_max"], 0)
        self.assertEqual(auth["inventory_request_count_max"], 1)
        self.assertTrue(auth["single_use_discovery_only"])
        self.assertFalse(auth["authorization_consumed"])
        self.assertFalse(auth["runtime_identity_bound"])
        self.assertFalse(auth["model_qualified"])
        self.assertTrue(auth["explicit_user_approval_received"])

    def test_d02_closed_gate_stops_before_inventory_contact(self) -> None:
        denied = {
            "status": "PREPARED_NOT_APPROVED",
            "discovery_version": discovery.DISCOVERY_VERSION,
            "discovery_type": discovery.DISCOVERY_TYPE,
            "model_repository": discovery.MODEL_REPOSITORY,
            "required_quantization": discovery.REQUIRED_QUANTIZATION,
            "required_base_url": discovery.REQUIRED_BASE_URL,
            "required_loaded_context_length": discovery.REQUIRED_CONTEXT,
            "localhost_inventory_contact_authorized": False,
            "model_contact_authorized": False,
            "generation_authorized": False,
            "qualification_execution_authorized": False,
            "generation_request_count_max": 0,
            "inventory_request_count_max": 1,
            "single_use_discovery_only": True,
            "synthetic_only": True,
            "local_loopback_only": True,
            "remote_cloud": False,
            "real_data": False,
            "authorization_consumed": False,
        }
        with patch.object(discovery, "load", return_value=denied), patch.object(
            discovery.urllib.request, "urlopen"
        ) as contact:
            with self.assertRaises(PermissionError):
                discovery.perform_discovery_only()
            contact.assert_not_called()

    def test_d03_exact_base_url_is_enforced_before_contact(self) -> None:
        with patch.object(discovery, "validate_discovery_authorization", return_value={}), patch.object(
            discovery.urllib.request, "urlopen"
        ) as contact:
            with self.assertRaises(PermissionError):
                discovery.perform_discovery_only(base_url="http://localhost:1234/v1")
            contact.assert_not_called()

    def test_d04_discovery_observes_runtime_id_without_binding_it(self) -> None:
        payload = {
            "models": [
                {
                    "key": "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
                    "format": "gguf",
                    "quantization": {"name": "Q4_K_M"},
                    "max_context_length": 262144,
                    "loaded_instances": [
                        {"id": "ministral-3-14b-instruct-2512", "config": {"context_length": 32768}}
                    ],
                }
            ]
        }
        with patch.object(discovery, "validate_discovery_authorization", return_value={}), patch.object(
            discovery.urllib.request, "urlopen", return_value=_FakeResponse(payload)
        ) as contact:
            result = discovery.perform_discovery_only()
        self.assertEqual(contact.call_count, 1)
        self.assertEqual(result["mode"], "RUNTIME_IDENTITY_DISCOVERY_OBSERVED_NOT_BOUND")
        self.assertEqual(result["loaded_instances"][0]["runtime_instance_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(result["compatible_loaded_instances"][0]["quantization"], "Q4_K_M")
        self.assertFalse(result["runtime_identity_bound"])
        self.assertTrue(result["binding_requires_separate_model_free_review"])
        self.assertEqual(result["inventory_request_count"], 1)
        self.assertEqual(result["generation_request_count"], 0)
        self.assertFalse(result["model_qualified"])

    def test_d05_discovery_does_not_require_repo_id_equal_runtime_id(self) -> None:
        payload = {
            "models": [
                {
                    "key": "repo-key",
                    "quantization": {"name": "Q4_K_M"},
                    "loaded_instances": [
                        {"id": "runtime-id-different-from-repo", "config": {"context_length": 65536}}
                    ],
                }
            ]
        }
        loaded = discovery._extract_loaded_instances(payload)
        self.assertEqual(loaded[0]["runtime_instance_id"], "runtime-id-different-from-repo")
        self.assertEqual(loaded[0]["model_key"], "repo-key")

    def test_d06_incompatible_quantization_is_observed_but_not_compatible(self) -> None:
        payload = {
            "models": [
                {
                    "key": "repo-key",
                    "quantization": {"name": "Q5_K_M"},
                    "loaded_instances": [
                        {"id": "runtime-id", "config": {"context_length": 32768}}
                    ],
                }
            ]
        }
        with patch.object(discovery, "validate_discovery_authorization", return_value={}), patch.object(
            discovery.urllib.request, "urlopen", return_value=_FakeResponse(payload)
        ):
            result = discovery.perform_discovery_only()
        self.assertEqual(len(result["loaded_instances"]), 1)
        self.assertEqual(result["compatible_loaded_instances"], [])
        self.assertFalse(result["runtime_identity_bound"])

    def test_d07_no_loaded_instance_fails_closed(self) -> None:
        payload = {"models": [{"key": "repo-key", "loaded_instances": []}]}
        with patch.object(discovery, "validate_discovery_authorization", return_value={}), patch.object(
            discovery.urllib.request, "urlopen", return_value=_FakeResponse(payload)
        ):
            with self.assertRaises(RuntimeError):
                discovery.perform_discovery_only()

    def test_d08_source_contains_no_generation_path(self) -> None:
        source = (ROOT / "scripts/zs_ki_b_sem_ministral_runtime_identity_discovery_v1_0.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("chat_completion_structured(", source)
        self.assertNotIn("/chat/completions", source)
        self.assertNotIn("for case in", source)
        self.assertIn("/api/v1/models", source)
        self.assertIn("runtime_identity_bound", source)


if __name__ == "__main__":
    unittest.main()
