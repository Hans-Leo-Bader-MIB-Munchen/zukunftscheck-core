from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_execution_result_2026_013_v0_1.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_authorization_v0_1.json"
ANALYSIS_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_failure_analysis_pf2_manifest_v0_1.json"
EXPECTED_RESULT_SHA256 = "8717ff6583d2ab38da23f002047f3c6477015c703d1d97e061889c863d45a8c3"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemV13FailurePreservationAndConsumptionV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = load(RESULT_PATH)
        cls.auth = load(AUTH_PATH)
        cls.analysis = load(ANALYSIS_PATH)

    def test_p01_preserved_result_sha256_is_exact(self) -> None:
        actual = hashlib.sha256(RESULT_PATH.read_bytes()).hexdigest()
        self.assertEqual(actual, EXPECTED_RESULT_SHA256)
        self.assertEqual(self.auth["preserved_result_sha256"], EXPECTED_RESULT_SHA256)
        self.assertEqual(self.analysis["source_result_sha256"], EXPECTED_RESULT_SHA256)

    def test_p02_one_shot_authorization_is_consumed_and_closed(self) -> None:
        a = self.auth
        self.assertEqual(a["status"], "CONSUMED")
        self.assertTrue(a["authorization_consumed"])
        self.assertTrue(a["approval_is_single_use"])
        self.assertFalse(a["execution_authorized"])
        self.assertFalse(a["model_run_authorized"])
        self.assertFalse(a["model_contact_authorized"])
        self.assertTrue(a["model_contact_performed"])
        self.assertEqual(a["consumed_observed_run_count"], 1)
        self.assertEqual(a["consumed_observed_model_request_count"], 2)

    def test_p03_result_identity_and_observed_counts_are_preserved(self) -> None:
        m = self.result["manifest"]
        self.assertEqual(m["run_type"], "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-3-GENERIC-COMPOSITION-2026-013")
        self.assertEqual(m["runner_version"], "v1.3")
        self.assertEqual(m["observed_run_count"], 1)
        self.assertEqual(m["observed_model_request_count"], 2)
        self.assertFalse(m["model_qualified"])

    def test_p04_pf1_passed_before_pf2_stop(self) -> None:
        pf1 = self.result["cases"][0]
        self.assertEqual(pf1["case_id"], "ZS-KI-B-SEM-V07-Q-PF1-SYN-001")
        self.assertTrue(pf1["boundary_evaluation"]["passed"])
        self.assertTrue(pf1["gold_evaluation"]["passed"])

    def test_p05_pf2_undercoverage_is_exactly_2_2(self) -> None:
        pf2 = self.result["cases"][1]
        boundary = pf2["boundary_evaluation"]
        completeness = boundary["completeness_result"]
        self.assertEqual(pf2["case_id"], "ZS-KI-B-SEM-V07-Q-PF2-SYN-001")
        self.assertTrue(boundary["formal_boundary_passed"])
        self.assertFalse(boundary["passed"])
        self.assertEqual(boundary["behavior"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertEqual(boundary["stop_code"], "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED")
        self.assertEqual(completeness["required_assignments"], [["2.1", "PF2"], ["2.2", "PF2"]])
        self.assertEqual(completeness["observed_assignments"], [["2.1", "PF2"]])
        self.assertEqual(completeness["missing_required_assignments"], [["2.2", "PF2"]])
        self.assertFalse(completeness["auto_assignment_performed"])
        self.assertFalse(completeness["semantic_repair_performed"])
        self.assertFalse(completeness["model_output_mutated"])

    def test_p06_manifest_provenance_defects_are_recorded_not_rewritten(self) -> None:
        m = self.result["manifest"]
        self.assertEqual(self.result["mode"], "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9")
        self.assertFalse(m["model_contact_performed"])
        self.assertEqual(m["observed_model_request_count"], 2)
        classes = [row["classification"] for row in self.analysis["manifest_provenance_findings"]]
        self.assertEqual(classes, ["INHERITED_MODE_LABEL_MISMATCH", "MODEL_CONTACT_FLAG_FALSE_NEGATIVE"])

    def test_p07_no_downstream_approval_or_second_run_is_created(self) -> None:
        a = self.auth
        for key in (
            "benchmark_approved",
            "generalisation_approved",
            "pilot_approved",
            "production_approved",
            "phase_f_approved",
        ):
            self.assertFalse(a[key])
        self.assertFalse(self.result["manifest"]["model_qualified"])
        self.assertIn("permission for a second model run", self.analysis["not_concluded"])


if __name__ == "__main__":
    unittest.main()
