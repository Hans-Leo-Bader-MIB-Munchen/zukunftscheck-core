from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_freeze_manifest_v0_1.json"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"
VALIDATOR = ROOT / "scripts/zs_ki_b_sem_v07_qualification_freeze_v0_1.py"


class SemV07QualificationFreezeTests(unittest.TestCase):
    def test_f01_frozen_artifacts_are_human_approved(self) -> None:
        for path in (SUITE, GOLD, POLICY):
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc["status"], "HUMAN_APPROVED_FROZEN")
            self.assertEqual(doc["approved_on"], "2026-08-27")

    def test_f02_drafts_are_preserved_separately(self) -> None:
        self.assertTrue((ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_draft_v0_1.json").exists())
        self.assertTrue((ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_draft_v0_1.json").exists())
        self.assertTrue((ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_draft_v0_1.json").exists())

    def test_f03_freeze_manifest_binds_exact_artifact_hashes(self) -> None:
        import scripts.zs_ki_b_sem_v07_qualification_freeze_v0_1 as freeze
        result = freeze.validate_freeze_bundle()
        self.assertEqual(result["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(result["case_count"], 16)
        self.assertEqual(result["pf_coverage"], "12/12")
        self.assertEqual(result["challenge_case_count"], 4)
        self.assertFalse(result["model_execution_authorized"])

    def test_f04_gold_remains_model_invisible_and_contains_countercheck_corrections(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        self.assertFalse(gold["model_visible"])
        indexed = {row["case_id"]: row for row in gold["cases"]}
        pf9 = indexed["ZS-KI-B-SEM-V07-Q-PF9-SYN-001"]
        self.assertIn({"question_id": "9.3", "pf_id": "PF9"}, pf9["expected_assignments"])
        possible = indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-POSSIBLE-DATE-SYN-001"]
        self.assertIn({"question_id": "3.2", "pf_id": "PF3"}, possible["forbidden_assignments"])
        timed = indexed["ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001"]
        self.assertFalse(timed["expected_conflict_candidate"])
        self.assertIn({"question_id": "4.5", "pf_id": "PF4"}, timed["forbidden_assignments"])

    def test_f05_policy_requires_precision_and_conflict_enforcement(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        pre = policy["preconditions_for_future_execution"]
        criteria = policy["pass_criteria"]
        self.assertTrue(pre["qualification_evaluator_must_enforce_optional_and_spurious_assignments"])
        self.assertTrue(pre["qualification_evaluator_must_enforce_expected_conflict_candidate"])
        self.assertEqual(criteria["spurious_assignments_outside_required_or_optional_allowed"], 0)
        self.assertEqual(criteria["expected_conflict_candidate_mismatches_allowed"], 0)
        self.assertTrue(pre["explicit_user_model_run_approval_required"])

    def test_f06_freeze_validator_is_model_free_and_execute_blocked(self) -> None:
        completed = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "VALIDATED_SEM_V0_7_QUALIFICATION_FREEZE_MODEL_FREE")
        self.assertEqual(manifest["expected_model_request_count"], 0)
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertFalse(manifest["execution_attempted"])
        self.assertFalse(manifest["model_qualified"])
        blocked = subprocess.run([sys.executable, str(VALIDATOR), "--execute"], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("model execution is disabled", blocked.stderr)


if __name__ == "__main__":
    unittest.main()
