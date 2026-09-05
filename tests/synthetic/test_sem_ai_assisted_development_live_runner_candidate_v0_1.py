import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts/zs_ki_b_sem_ai_assisted_development_live_runner_candidate_v0_1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("dev_live_runner_v0_1", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSemAiAssistedDevelopmentLiveRunnerCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()

    def test_static_bindings_validate_and_prep_remains_non_authorizing(self):
        prep = self.runner.validate_static_bindings()
        self.assertFalse(prep["execution_authorized"])
        self.assertFalse(prep["model_contact_authorized"])
        self.assertFalse(prep["preflight_authorized"])
        self.assertFalse(prep["ready_for_user_approval"])

    def test_exact_24_machine_cases_are_loaded(self):
        challenges = self.runner.load_challenges()
        self.assertEqual(challenges["case_count"], 24)
        self.assertEqual(len(challenges["cases"]), 24)
        self.assertEqual(len({c["case_id"] for c in challenges["cases"]}), 24)

    def test_request_preview_matches_bound_runtime(self):
        case = self.runner.load_challenges()["cases"][0]
        payload = self.runner.build_request_preview(case)
        self.assertEqual(payload["model"], "ministral-3-14b-instruct-2512")
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertIs(payload["stream"], False)
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertIs(payload["response_format"]["json_schema"]["strict"], True)
        self.assertNotIn("max_completion_tokens", payload)

    def test_execution_gate_rejects_missing_authorization_before_transport(self):
        with self.assertRaises(PermissionError):
            self.runner.validate_execution_gate(authorization=None, preflight_result=None)

    def test_execution_gate_requires_frozen_preflight(self):
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_contact_authorized": True,
            "expected_run_count": 1,
            "expected_model_request_count": 24,
            "automatic_retry_authorized": False,
            "automatic_rerun_authorized": False,
            "output_repair_authorized": False,
        }
        with self.assertRaises(PermissionError):
            self.runner.validate_execution_gate(authorization=auth, preflight_result={"status": "NOT_RUN"})

    def test_fake_transport_executes_exactly_24_without_network(self):
        auth = {
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_contact_authorized": True,
            "expected_run_count": 1,
            "expected_model_request_count": 24,
            "automatic_retry_authorized": False,
            "automatic_rerun_authorized": False,
            "output_repair_authorized": False,
        }
        preflight = {"status": "PASS_FROZEN", "model_id": "ministral-3-14b-instruct-2512", "loaded_context": 32768}
        calls = []

        def fake_transport(**kwargs):
            calls.append(kwargs)
            return json.dumps({"contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate", "source_location_id": "synthetic", "proposals": []}), {"model": "synthetic-no-network"}

        result = self.runner.execute_once(authorization=auth, preflight_result=preflight, transport=fake_transport)
        self.assertEqual(len(calls), 24)
        self.assertEqual(result["observed_model_request_count"], 24)
        self.assertTrue(result["development_only"])
        self.assertFalse(result["qualification_claim_allowed"])
        self.assertFalse(result["automatic_retry_authorized"])
        self.assertFalse(result["automatic_rerun_authorized"])
        self.assertFalse(result["output_repair_authorized"])


if __name__ == "__main__":
    unittest.main()
