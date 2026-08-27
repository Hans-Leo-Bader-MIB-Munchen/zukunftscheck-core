from __future__ import annotations

import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_8.py"


class SemQualificationRunnerV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = importlib.import_module("scripts.zs_ki_b_sem_qualifikation_runner_v0_8")

    def _response(self, assignments: list[tuple[str, str]], conflicts: list[str] | None = None) -> dict:
        return {
            "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
            "source_location_id": "SL-X",
            "proposals": [{
                "proposal_id": "P1",
                "source_location_id": "SL-X",
                "normalized_statement": "synthetic",
                "finding_type_candidate": "DT",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {"question_id": q, "pf_id": pf, "assignment_confidence": "CLEAR", "human_review_required": True}
                    for q, pf in assignments
                ],
                "conflict_candidate_refs": conflicts or [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": True,
            }],
        }

    def test_r01_frozen_package_validates(self) -> None:
        package = self.mod.validate_frozen_package()
        self.assertEqual(len(package["suite"]["cases"]), 16)
        self.assertEqual(package["gold"]["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(package["policy"]["status"], "HUMAN_APPROVED_FROZEN")

    def test_r02_dry_run_is_model_free_and_16_case_bound(self) -> None:
        completed = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V0_8")
        self.assertEqual(manifest["expected_model_request_count"], 16)
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertFalse(manifest["execution_attempted"])
        self.assertFalse(manifest["remote_cloud"])
        self.assertFalse(manifest["real_data"])

    def test_r03_execute_is_blocked_without_explicit_authorization_artifact(self) -> None:
        self.assertFalse(self.mod.AUTH_PATH.exists())
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--execute", "--model", "MUST_NOT_RUN"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("explicit model-run authorization artifact is absent", completed.stderr)

    def test_r04_required_assignment_must_be_present(self) -> None:
        gold = {"expected_assignments": [{"question_id": "3.3", "pf_id": "PF3"}]}
        result = self.mod.evaluate_gold(gold, self._response([]))
        self.assertFalse(result["passed"])
        self.assertEqual(result["missing_required"], [["3.3", "PF3"]] if isinstance(result["missing_required"][0], list) else [("3.3", "PF3")])

    def test_r05_optional_assignment_is_allowed(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "2.1", "pf_id": "PF2"}],
            "optional_assignments": [{"question_id": "2.4", "pf_id": "PF2"}],
        }
        result = self.mod.evaluate_gold(gold, self._response([("2.1", "PF2"), ("2.4", "PF2")]))
        self.assertTrue(result["passed"])
        self.assertEqual(result["spurious_assignments"], [])

    def test_r06_spurious_assignment_causes_fail(self) -> None:
        gold = {"expected_assignments": [{"question_id": "2.1", "pf_id": "PF2"}]}
        result = self.mod.evaluate_gold(gold, self._response([("2.1", "PF2"), ("4.1", "PF4")]))
        self.assertFalse(result["passed"])
        self.assertTrue(result["spurious_assignments"])

    def test_r07_forbidden_assignment_causes_fail(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "11.2", "pf_id": "PF11"}],
            "forbidden_assignments": [{"question_id": "7.1", "pf_id": "PF7"}],
        }
        result = self.mod.evaluate_gold(gold, self._response([("11.2", "PF11"), ("7.1", "PF7")]))
        self.assertFalse(result["passed"])
        self.assertTrue(result["forbidden_present"])

    def test_r08_expected_nonconflict_is_enforced(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "4.2", "pf_id": "PF4"}],
            "expected_conflict_candidate": False,
        }
        ok = self.mod.evaluate_gold(gold, self._response([("4.2", "PF4")], []))
        bad = self.mod.evaluate_gold(gold, self._response([("4.2", "PF4")], ["SL-OTHER"]))
        self.assertTrue(ok["passed"])
        self.assertFalse(bad["passed"])
        self.assertFalse(bad["conflict_candidate_match"])

    def test_r09_gold_is_not_in_model_payload(self) -> None:
        package = self.mod.validate_frozen_package()
        case = package["suite"]["cases"][0]
        messages = self.mod.build_messages(case, self.mod.PROMPT_PATH.read_text(encoding="utf-8"))
        payload = json.loads(messages[1]["content"])
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("expected_assignments", rendered)
        self.assertNotIn("optional_assignments", rendered)
        self.assertNotIn("forbidden_assignments", rendered)
        self.assertNotIn("HUMAN_APPROVED_FROZEN", rendered)

    def test_r10_cloud_endpoint_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            self.mod.build_dry_run_manifest(model="x", base_url="https://api.anthropic.com/v1")


if __name__ == "__main__":
    unittest.main()
