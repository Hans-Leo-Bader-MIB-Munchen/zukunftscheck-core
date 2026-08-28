from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3_1 as v131

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_RESULT = ROOT / "tests/fixtures/zs_ki_b_sem_v13_execution_result_2026_013_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemQualificationRunnerV131Provenance(unittest.TestCase):
    def test_p01_historical_v13_result_remains_unchanged_and_exposes_known_defects(self) -> None:
        result = load(HISTORICAL_RESULT)
        self.assertEqual(result["mode"], "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9")
        self.assertEqual(result["manifest"]["observed_model_request_count"], 2)
        self.assertFalse(result["manifest"]["model_contact_performed"])

    def test_p02_failed_mode_is_normalized_to_v131(self) -> None:
        payload = {
            "mode": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9",
            "manifest": {"observed_model_request_count": 2},
        }
        normalized = v131.normalize_execution_provenance(payload)
        self.assertEqual(normalized["mode"], "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_3_1")
        self.assertEqual(normalized["manifest"]["runner_version"], "v1.3.1")
        self.assertEqual(normalized["manifest"]["run_type"], v131.RUN_TYPE)

    def test_p03_any_observed_generation_request_marks_model_contact_true(self) -> None:
        payload = {
            "mode": "EXECUTING_SEM_QUALIFICATION_V0_9",
            "manifest": {"observed_model_request_count": 1, "model_contact_performed": False},
        }
        normalized = v131.normalize_execution_provenance(payload)
        self.assertTrue(normalized["manifest"]["model_contact_performed"])

    def test_p04_zero_observed_requests_keeps_model_contact_false(self) -> None:
        payload = {
            "mode": "PRECONDITION_FAILED_SEM_QUALIFICATION_V0_9",
            "manifest": {"observed_model_request_count": 0, "model_contact_performed": True},
        }
        normalized = v131.normalize_execution_provenance(payload)
        self.assertFalse(normalized["manifest"]["model_contact_performed"])
        self.assertEqual(normalized["mode"], "PRECONDITION_FAILED_SEM_QUALIFICATION_V1_3_1")

    def test_p05_normalization_does_not_mutate_case_or_model_response_content(self) -> None:
        payload = {
            "mode": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9",
            "manifest": {"observed_model_request_count": 2},
            "cases": [
                {
                    "case_id": "PF2",
                    "model_response_raw": "raw-output",
                    "model_response": {"proposals": [{"normalized_statement": "unchanged"}]},
                    "boundary_evaluation": {"stop_code": "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED"},
                }
            ],
        }
        before_cases = copy.deepcopy(payload["cases"])
        v131.normalize_execution_provenance(payload)
        self.assertEqual(payload["cases"], before_cases)

    def test_p06_consumed_v13_authorization_cannot_authorize_v131(self) -> None:
        with self.assertRaises(PermissionError):
            v131.validate_execution_authorization("qwen3-14b")

    def test_p07_dry_run_is_v131_and_performs_no_model_contact(self) -> None:
        with patch.object(v131.v13.v11.v10.v09.base, "current_git_commit", return_value="0" * 40):
            payload = v131.build_dry_run_manifest(model="qwen3-14b")
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_3_1")
        self.assertEqual(payload["manifest"]["runner_version"], "v1.3.1")
        self.assertEqual(payload["manifest"]["run_type"], v131.RUN_TYPE)
        self.assertFalse(payload["manifest"]["model_contact_performed"])
        self.assertTrue(payload["manifest"]["provenance_correction_only"])


if __name__ == "__main__":
    unittest.main()
