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
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_draft_v0_1.json"


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

    def test_q03_policy_is_draft_and_requires_precision_and_conflict_enforcement(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["status"], "DRAFT_NOT_HUMAN_APPROVED")
        pre = policy["preconditions_for_future_execution"]
        criteria = policy["pass_criteria"]
        self.assertTrue(pre["explicit_user_model_run_approval_required"])
        self.assertTrue(pre["qualification_evaluator_must_enforce_optional_and_spurious_assignments"])
        self.assertTrue(pre["qualification_evaluator_must_enforce_expected_conflict_candidate"])
        self.assertEqual(criteria["model_requests_expected"], 16)
        self.assertEqual(criteria["parse_success_required"], "16/16")
        self.assertEqual(criteria["contract_and_boundary_pass_required"], "16/16")
        self.assertEqual(criteria["challenge_cases_pass_required"], "4/4")
        self.assertEqual(criteria["spurious_assignments_outside_required_or_optional_allowed"], 0)
        self.assertEqual(criteria["expected_conflict_candidate_mismatches_allowed"], 0)
        self.assertTrue(criteria["optional_gold_assignments_allowed_but_not_required"])

    def test_q04_suite_contains_no_gold_expectation_keys(self) -> None:
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        for case in suite["cases"]:
            self.assertFalse(any(key.startswith("expected_") or key.startswith("optional_") or key.startswith("forbidden_") for key in case))

    def test_q05_bundle_validator_requires_pf_challenge_and_policy_controls(self) -> None:
        import scripts.zs_ki_b_sem_v07_qualification_pre_run_v0_1 as pre
        result = pre.validate_pre_run_bundle()
        self.assertEqual(result["case_count"], 16)
        self.assertEqual(result["challenge_case_count"], 4)
        self.assertEqual(result["optional_assignment_count"], 2)
        self.assertEqual(result["pf_coverage"], "12/12")
        self.assertEqual(result["human_gold_status"], "DRAFT_NOT_HUMAN_APPROVED")
        self.assertEqual(result["policy_status"], "DRAFT_NOT_HUMAN_APPROVED")

    def test_q06_all_gold_assignments_use_frozen_question_pf_binding_and_are_disjoint(self) -> None:
        questions = json.loads((ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json").read_text(encoding="utf-8"))["questions"]
        canonical = {row["question_id"]: row["pf_id"] for row in questions}
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        for case in gold["cases"]:
            sets = []
            for key in ("expected_assignments", "optional_assignments", "forbidden_assignments"):
                items = case.get(key, [])
                assignment_set = set()
                for assignment in items:
                    self.assertIn(assignment["question_id"], canonical)
                    self.assertEqual(canonical[assignment["question_id"]], assignment["pf_id"])
                    assignment_set.add((assignment["question_id"], assignment["pf_id"]))
                sets.append(assignment_set)
            required, optional, forbidden = sets
            self.assertFalse(required & optional)
            self.assertFalse(required & forbidden)
            self.assertFalse(optional & forbidden)

    def test_q07_independent_countercheck_corrections_are_encoded(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        indexed = {case["case_id"]: case for case in gold["cases"]}
        pf9 = indexed["ZS-KI-B-SEM-V07-Q-PF9-SYN-001"]
        self.assertIn({"question_id": "9.3", "pf_id": "PF9"}, pf9["expected_assignments"])
        possible_date = indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-POSSIBLE-DATE-SYN-001"]
        self.assertIn({"question_id": "3.2", "pf_id": "PF3"}, possible_date["forbidden_assignments"])
        time_case = indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001"]
        self.assertIn({"question_id": "4.5", "pf_id": "PF4"}, time_case["forbidden_assignments"])
        self.assertFalse(time_case["expected_conflict_candidate"])

    def test_q08_plausible_nonrequired_assignments_are_explicitly_optional(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        indexed = {case["case_id"]: case for case in gold["cases"]}
        self.assertEqual(indexed["ZS-KI-B-SEM-V07-Q-PF2-SYN-001"]["optional_assignments"], [{"question_id":"2.4","pf_id":"PF2"}])
        self.assertEqual(indexed["ZS-KI-B-SEM-V07-Q-PF6-SYN-001"]["optional_assignments"], [{"question_id":"4.4","pf_id":"PF4"}])

    def test_q09_dry_run_manifest_is_strictly_model_free(self) -> None:
        completed = subprocess.run([sys.executable, str(PRE_RUN)], cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_V0_7_QUALIFICATION_PRE_RUN")
        self.assertEqual(manifest["qualification_case_count"], 16)
        self.assertEqual(manifest["qualification_challenge_case_count"], 4)
        self.assertEqual(manifest["qualification_optional_assignment_count"], 2)
        self.assertEqual(manifest["qualification_pf_coverage"], "12/12")
        self.assertEqual(manifest["meaning_layer_schema_version"], "v0.7")
        self.assertEqual(manifest["meaning_layer_coverage"], "67/67")
        self.assertEqual(manifest["human_gold_status"], "DRAFT_NOT_HUMAN_APPROVED")
        self.assertFalse(manifest["human_gold_model_visible"])
        self.assertEqual(manifest["qualification_policy_status"], "DRAFT_NOT_HUMAN_APPROVED")
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
        self.assertTrue(manifest["qualification_policy_sha256"])

    def test_q10_execute_is_blocked_before_model_contact(self) -> None:
        completed = subprocess.run([sys.executable, str(PRE_RUN), "--execute"], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("model execution is disabled", completed.stderr)

    def test_q11_runtime_v07_remains_execution_blocked(self) -> None:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_7.py"), "--execute", "--model", "MUST_NOT_RUN"], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("model execution is disabled", completed.stderr)


if __name__ == "__main__":
    unittest.main()
