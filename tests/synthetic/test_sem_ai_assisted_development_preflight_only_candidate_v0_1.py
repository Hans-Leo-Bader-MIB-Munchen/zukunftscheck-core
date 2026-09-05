import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts/zs_ki_b_sem_ai_assisted_development_preflight_only_candidate_v0_1.py"


def load_candidate():
    spec = importlib.util.spec_from_file_location("dev_preflight_v0_1", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSemAiAssistedDevelopmentPreflightOnlyCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load_candidate()

    def test_static_runtime_binding_is_exact_and_non_authorizing(self):
        binding = self.candidate.validate_static_binding()
        self.assertFalse(binding["execution_authorized"])
        self.assertFalse(binding["model_contact_authorized"])
        self.assertFalse(binding["preflight_authorized"])

    def test_missing_preflight_authorization_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.candidate.validate_preflight_authorization(None)

    def test_preflight_authorization_requires_zero_generation_requests(self):
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "preflight_authorized": True,
            "model_contact_authorized": True,
            "execution_authorized": False,
            "expected_preflight_run_count": 1,
            "expected_generation_request_count": 1,
        }
        with self.assertRaises(PermissionError):
            self.candidate.validate_preflight_authorization(auth)

    def test_fake_probe_passes_without_network_and_zero_generation(self):
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "preflight_authorized": True,
            "model_contact_authorized": True,
            "execution_authorized": False,
            "expected_preflight_run_count": 1,
            "expected_generation_request_count": 0,
        }
        def fake_probe(**kwargs):
            self.assertEqual(kwargs["base_url"], "http://127.0.0.1:1234/v1")
            return {
                "model_id": "ministral-3-14b-instruct-2512",
                "model_repository": "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
                "quantization": "Q4_K_M",
                "loaded_context": 32768,
            }
        result = self.candidate.execute_preflight(authorization=auth, probe=fake_probe)
        self.assertEqual(result["status"], "PASS_FROZEN_CANDIDATE")
        self.assertEqual(result["generation_request_count"], 0)
        self.assertFalse(result["development_execution_authorized"])
        self.assertFalse(result["qualification_claim_allowed"])

    def test_context_below_minimum_fails_closed(self):
        result = self.candidate.evaluate_probe({
            "model_id": "ministral-3-14b-instruct-2512",
            "model_repository": "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
            "quantization": "Q4_K_M",
            "loaded_context": 16384,
        })
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertFalse(result["checks"]["loaded_context_min"])


if __name__ == "__main__":
    unittest.main()
