from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_execution_evidence_2026_001_v0_1.json"


class SemSystemQualificationExecutionEvidenceV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_e01_records_exact_source_merge_and_scope(self) -> None:
        self.assertEqual(self.evidence["source_merge_commit"], "c11d2554ddeae5c802e4f98bdfae7bf5ed7b83b2")
        self.assertEqual(self.evidence["source_pr"], 49)
        self.assertEqual(self.evidence["system_case_count"], 19)
        self.assertEqual(self.evidence["expected_pass_through_case_count"], 16)
        self.assertEqual(self.evidence["expected_fail_closed_stop_case_count"], 3)

    def test_e02_records_green_without_inventing_test_totals(self) -> None:
        self.assertEqual(self.evidence["status"], "POST_MERGE_LOCAL_VALIDATION_REPORTED_GREEN")
        self.assertIn("Exact unittest totals were not captured", self.evidence["reported_result_scope"])
        self.assertEqual(len(self.evidence["validation_commands_reported_green"]), 2)

    def test_e03_preserves_model_system_separation_and_no_authorization(self) -> None:
        self.assertFalse(self.evidence["model_qualified"])
        self.assertFalse(self.evidence["model_qualification_changed"])
        self.assertFalse(self.evidence["model_contact_attempted"])
        self.assertEqual(self.evidence["model_request_count"], 0)
        self.assertFalse(self.evidence["execution_authorized"])
        self.assertFalse(self.evidence["model_run_authorized"])

    def test_e04_grants_no_deployment_or_generalisation_scope(self) -> None:
        for key in (
            "real_data",
            "pilot_approved",
            "production_approved",
            "benchmark_approved",
            "generalisation_approved",
            "phase_f_approved",
        ):
            self.assertFalse(self.evidence[key], key)


if __name__ == "__main__":
    unittest.main()
