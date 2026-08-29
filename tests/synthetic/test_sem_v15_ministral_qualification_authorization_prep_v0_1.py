from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v1_5 as v15

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v15_ministral_qualification_timeout_failure_preserved_v0_1.json"


class MinistralV15QualificationAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = v15.load(v15.AUTH_PATH)

    def test_q01_single_use_authorization_is_consumed_and_closed(self) -> None:
        self.assertEqual(self.auth["status"], "CONSUMED")
        self.assertTrue(self.auth["authorization_consumed"])
        self.assertFalse(self.auth["execution_authorized"])
        self.assertFalse(self.auth["model_run_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])
        self.assertTrue(self.auth["model_contact_performed"])
        self.assertEqual(self.auth["observed_run_count"], 1)
        self.assertEqual(self.auth["observed_model_request_count"], 1)
        self.assertEqual(self.auth["run_outcome"], "EXECUTED_ONCE_FAILED_TIMEOUT")
        self.assertFalse(v15._authorization_matches(self.auth, v15.RUNTIME_MODEL_ID))

    def test_q02_timeout_result_is_preserved_exactly_as_technical_failure(self) -> None:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        manifest = result["manifest"]
        self.assertEqual(result["mode"], "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_5")
        self.assertEqual(manifest["runner_version"], "v1.5")
        self.assertEqual(manifest["observed_model_request_count"], 1)
        self.assertEqual(manifest["request_timeout_seconds"], 1800)
        self.assertEqual(manifest["required_request_timeout_seconds"], 1800)
        self.assertTrue(manifest["execution_authorized"])
        self.assertTrue(manifest["model_run_authorized"])
        self.assertTrue(manifest["model_contact_performed"])
        self.assertTrue(manifest["preflight_pass_observed"])
        self.assertFalse(manifest["model_qualified"])
        self.assertIsNone(result["cases"][0]["model_response_raw"])
        self.assertIn("timed out", result["cases"][0]["endpoint_error"])

    def test_q03_preflight_pass_remains_preserved_after_consumption(self) -> None:
        self.assertTrue(self.auth["preflight_pass_required"])
        self.assertTrue(self.auth["preflight_pass_observed"])
        self.assertTrue(self.auth["v14_timeout_failure_preserved"])
        self.assertTrue(self.auth["timeout_binding_fix_verified_model_free"])

    def test_q04_hypothetical_reopening_still_requires_fresh_authorization(self) -> None:
        auth = copy.deepcopy(self.auth)
        auth["status"] = "EXPLICIT_USER_APPROVED"
        auth["execution_authorized"] = True
        auth["model_run_authorized"] = True
        auth["model_contact_authorized"] = True
        self.assertFalse(v15._authorization_matches(auth, v15.RUNTIME_MODEL_ID))
        auth["authorization_consumed"] = False
        self.assertTrue(v15._authorization_matches(auth, v15.RUNTIME_MODEL_ID))

    def test_q05_exact_scope_remains_synthetic_local_and_not_qualified(self) -> None:
        self.assertEqual(self.auth["runner_version"], v15.RUNNER_VERSION)
        self.assertEqual(self.auth["run_type"], v15.RUN_TYPE)
        self.assertEqual(self.auth["runtime_model_id"], v15.RUNTIME_MODEL_ID)
        self.assertEqual(self.auth["required_request_timeout_seconds"], v15.REQUIRED_TIMEOUT)
        self.assertEqual(self.auth["expected_model_request_count"], 16)
        self.assertEqual(self.auth["retry_count"], 0)
        self.assertFalse(self.auth["output_repair"])
        self.assertTrue(self.auth["synthetic_only"])
        self.assertTrue(self.auth["local_loopback_only"])
        self.assertFalse(self.auth["model_qualified"])
        self.assertFalse(self.auth["benchmark_approved"])
        self.assertFalse(self.auth["pilot_approved"])
        self.assertFalse(self.auth["production_approved"])
        self.assertFalse(self.auth["phase_f_approved"])


if __name__ == "__main__":
    unittest.main()
