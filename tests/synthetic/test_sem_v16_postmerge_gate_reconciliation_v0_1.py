from __future__ import annotations

import json
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v1_6 as v16

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_AUTH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_v0_2.json"
V15_AUTH = ROOT / "tests/fixtures/zs_ki_b_sem_v15_ministral_model_run_authorization_v0_1.json"
V15_RESULT = ROOT / "tests/fixtures/zs_ki_b_sem_v15_ministral_qualification_timeout_failure_preserved_v0_1.json"


class V16PostMergeGateReconciliationTests(unittest.TestCase):
    def test_g01_preflight_authorization_is_consumed_while_pass_evidence_remains_true(self) -> None:
        auth = json.loads(PREFLIGHT_AUTH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "CONSUMED")
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["preflight_pass_observed"])
        self.assertFalse(auth["localhost_preflight_authorized"])
        self.assertFalse(auth["model_contact_authorized"])

    def test_g02_v16_dry_run_reports_preserved_preflight_pass(self) -> None:
        dry = v16.build_dry_run_manifest()
        self.assertEqual(dry["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_6")
        self.assertEqual(dry["manifest"]["runner_version"], "v1.6")
        self.assertTrue(dry["manifest"]["preflight_pass_observed"])
        self.assertFalse(dry["manifest"]["execution_authorized"])
        self.assertFalse(dry["manifest"]["model_run_authorized"])
        self.assertFalse(dry["manifest"]["model_contact_performed"])
        self.assertFalse(dry["manifest"]["model_qualified"])

    def test_g03_v16_execution_remains_fail_closed(self) -> None:
        with self.assertRaises(PermissionError):
            v16.validate_execution_authorization(v16.RUNTIME_MODEL_ID)

    def test_g04_v15_single_use_authorization_is_consumed(self) -> None:
        auth = json.loads(V15_AUTH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "CONSUMED")
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(auth["model_contact_performed"])
        self.assertEqual(auth["observed_model_request_count"], 1)
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["model_run_authorized"])
        self.assertFalse(auth["model_contact_authorized"])

    def test_g05_v15_failure_is_timeout_not_semantic_fail(self) -> None:
        result = json.loads(V15_RESULT.read_text(encoding="utf-8"))
        self.assertEqual(result["manifest"]["observed_model_request_count"], 1)
        self.assertEqual(result["manifest"]["request_timeout_seconds"], 1800)
        self.assertTrue(result["manifest"]["preflight_pass_observed"])
        self.assertIsNone(result["cases"][0]["model_response_raw"])
        self.assertIsNone(result["cases"][0]["model_response"])
        self.assertIn("timed out", result["cases"][0]["endpoint_error"])
        self.assertFalse(result["manifest"]["model_qualified"])


if __name__ == "__main__":
    unittest.main()
