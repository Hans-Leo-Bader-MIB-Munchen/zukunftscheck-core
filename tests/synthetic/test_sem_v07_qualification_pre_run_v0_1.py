from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE_RUN = ROOT / "scripts/zs_ki_b_sem_v07_qualification_pre_run_v0_1.py"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_draft_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_draft_v0_1.json"


class SemV07QualificationPreRunTests(unittest.TestCase):
    def test_q01_suite_is_synthetic_and_contains_16_unique_cases(self) -> None:
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        self.assertEqual(suite["data_class"], "SYNTHETIC_ONLY")
        self.assertEqual(len(suite["cases"]), 16)
        self.assertEqual(len({case["case_id"] for case in suite["cases"]}), 16)
        self.assertEqual(sum("CHALLENGE" in case["case_id"] for case in suite["cases"]), 4)

    def test_q02_gold_is_separate_unapproved_and_not_model_visible(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        self.assertEqual(gold["status"], "DRAFT_NOT_HUMAN_APPROVED")
        self.assertFalse(gold["model_visible"])
        self.assertEqual(len(gold["cases"]), 16)

    def test_q03_suite_contains_no_gold_expectation_keys(self) -> None:
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        for case in suite["cases"]:
            self.assertFalse(any(key.startswith("expected_") or key.startswith("forbidden_") for key in case))

    def test_q04_bundle_validator_requires_pf_and_challenge_coverage(self) -> None:
        import scripts.zs_ki_b_sem_v07_qualification_pre_run_v0_1 as pre
        result = pre.validate_pre_run_bundle()
        self.assertEqual(result["case_count"], 16)
        self.assertEqual(result["challenge_case_count"], 4)
        self.assertEqual(result["pf_coverage"], "12/12")
        self.assertEqual(result["human_gold_status"], "DRAFT_NOT_HUMAN_APPROVED")

    def test_q05_all_gold_assignments_use_frozen_question_pf_binding(self) -> None:
        questions = json.loads((ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json").read_text(encoding="utf-8"))["questions"]
        canonical = {row["question_id"]: row["pf_id"] for row in questions}
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        for case in gold["cases"]:
            for key in ("expected_assignments", "forbidden_assignments"):
                for assignment in case.get(key, []):
                    self.assertIn(assignment["question_id"], canonical)
                    self.assertEqual(canonical[assignment["question_id"]], assignment["pf_id"])

    def test_q06_challenge_gold_contains_negative_and_nonconflict_expectations(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        indexed = {case["case_id"]: case for case in gold["cases"]}
        self.assertTrue(indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-DOC-SYN-001"]["forbidden_assignments"])
        self.assertTrue(indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-UNSUPPORTED-SYN-001"]["forbidden_assignments"])
        self.assertFalse(indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001"]["expected_conflict_candidate"])

    def test_q07_dry_run_manifest_is_strictly_model_free(self) -> None:
        completed = subprocess.run([sys.executable, str(PRE_RUN)], cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_V0_7_QUALIFICATION_PRE_RUN")
        self.assertEqual(manifest["qualification_case_count"], 16)
        self.assertEqual(manifest["qualification_challenge_case_count"], 4)
        self.assertEqual(manifest["qualification_pf_coverage"], "12/12")
        self.assertEqual(manifest["meaning_layer_schema_version"], "v0.7")
        self.assertEqual(manifest["meaning_layer_coverage"], "67/67")
        self.assertEqual(manifest["human_gold_status"], "DRAFT_NOT_HUMAN_APPROVED")
        self.assertFalse(manifest["human_gold_model_visible"])
        self.assertEqual(manifest["expected_run_count"], 0)
        self.assertEqual(manifest["expected_model_request_count"], 0)
        self.assertEqual(manifest["observed_run_count"], 0)
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertFalse(manifest["execution_attempted"])
        self.assertFalse(manifest["model_execution_enabled"])
        self.assertFalse(manifest["real_data"])
        self.assertFalse(manifest["model_qualified"])
        self.assertTrue(manifest["qualification_suite_sha256"])
        self.assertTrue(manifest["human_gold_sha256"])

    def test_q08_execute_is_blocked_before_model_contact(self) -> None:
        completed = subprocess.run([sys.executable, str(PRE_RUN), "--execute"], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("model execution is disabled", completed.stderr)

    def test_q09_runtime_v07_remains_execution_blocked(self) -> None:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_7.py"), "--execute", "--model", "MUST_NOT_RUN"], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("model execution is disabled", completed.stderr)


if __name__ == "__main__":
    unittest.main()
