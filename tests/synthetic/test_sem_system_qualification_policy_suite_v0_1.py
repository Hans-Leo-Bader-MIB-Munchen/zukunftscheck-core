from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_runtime_guard_v0_1 import evaluate_semantic_runtime_guard

ROOT = Path(__file__).resolve().parents[2]
MODEL_SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_policy_v0_1.json"
SYSTEM_SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_suite_v0_1.json"
FREEZE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_gold_complete_response(case: dict, gold_case: dict) -> dict:
    target = case["target_source_location_id"]
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target,
        "proposals": [
            {
                "proposal_id": f"P-{target}-SYSQUAL",
                "source_location_id": target,
                "normalized_statement": case["source_locations"][-1]["original_text"],
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {
                        "question_id": row["question_id"],
                        "pf_id": row["pf_id"],
                        "assignment_confidence": "CLEAR",
                        "human_review_required": False,
                    }
                    for row in gold_case.get("expected_assignments", [])
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": False,
            }
        ],
    }


class SemSystemQualificationPolicySuiteV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model_suite = load(MODEL_SUITE)
        cls.gold = load(GOLD)
        cls.policy = load(POLICY)
        cls.system_suite = load(SYSTEM_SUITE)
        cls.freeze = load(FREEZE)
        cls.case_by_id = {row["case_id"]: row for row in cls.model_suite["cases"]}
        cls.gold_by_id = {row["case_id"]: row for row in cls.gold["cases"]}

    def _evaluate(self, case: dict, response: dict) -> dict:
        target = case["target_source_location_id"]
        source_by_id = {row["source_location_id"]: row for row in case["source_locations"]}
        return evaluate_semantic_runtime_guard(
            source_text=source_by_id[target]["original_text"],
            model_response=response,
            allowed_source_location_ids=set(source_by_id),
            target_source_location_id=target,
        )

    def test_q01_policy_separates_model_and_guarded_system_status(self) -> None:
        axes = self.policy["status_axes"]
        self.assertEqual(axes["model"], "MODEL_QUALIFIED")
        self.assertEqual(axes["guarded_system"], "GUARDED_SYSTEM_QUALIFIED")
        self.assertTrue(axes["must_remain_separate"])
        self.assertIn("MUST NOT set MODEL_QUALIFIED=true", self.policy["model_status_rule"])

    def test_q02_candidate_authorizes_no_execution(self) -> None:
        self.assertEqual(self.policy["status"], "FREEZE_CANDIDATE")
        self.assertEqual(self.system_suite["status"], "FREEZE_CANDIDATE")
        self.assertEqual(self.freeze["status"], "FREEZE_CANDIDATE")
        self.assertFalse(self.policy["execution_authorized"])
        self.assertFalse(self.policy["model_run_authorized"])
        self.assertFalse(self.system_suite["execution_authorized"])
        self.assertFalse(self.freeze["model_run_authorized"])

    def test_q03_suite_has_prefrozen_behavior_for_every_case(self) -> None:
        cases = self.system_suite["cases"]
        self.assertEqual(len(cases), 19)
        self.assertEqual(sum(row["expected_behavior"] == "PASS_THROUGH" for row in cases), 16)
        self.assertEqual(sum(row["expected_behavior"] == "FAIL_CLOSED_STOP" for row in cases), 3)
        self.assertTrue(all(row["expected_behavior"] in {"PASS_THROUGH", "FAIL_CLOSED_STOP"} for row in cases))

    def test_q04_all_16_canonical_gold_complete_variants_pass_through(self) -> None:
        for system_case in self.system_suite["cases"]:
            if system_case["expected_behavior"] != "PASS_THROUGH":
                continue
            case = self.case_by_id[system_case["base_case_id"]]
            response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
            result = self._evaluate(case, response)
            self.assertTrue(result["boundary_passed"], system_case["system_case_id"])
            self.assertFalse(result["human_review_required"], system_case["system_case_id"])
            self.assertTrue(result["automatic_downstream_use_allowed"], system_case["system_case_id"])
            self.assertFalse(result["model_output_mutated"], system_case["system_case_id"])

    def test_q05_pf2_underassignment_matches_defined_fail_closed_stop(self) -> None:
        spec = next(row for row in self.system_suite["cases"] if row["system_case_id"] == "SYS-STOP-PF2-UNDERASSIGN")
        case = self.case_by_id[spec["base_case_id"]]
        response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
        response["proposals"][0]["assignment_candidates"] = [
            row for row in response["proposals"][0]["assignment_candidates"]
            if not (row["question_id"] == "2.2" and row["pf_id"] == "PF2")
        ]
        before = copy.deepcopy(response)
        result = self._evaluate(case, response)
        self.assertTrue(result["boundary_passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertTrue(result["completeness_audit"]["possible_multi_assignment_omission"])
        self.assertEqual(spec["expected_stop_code"], "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED")
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])

    def test_q06_target_mismatch_is_formally_fail_closed(self) -> None:
        spec = next(row for row in self.system_suite["cases"] if row["system_case_id"] == "SYS-STOP-TARGET-MISMATCH")
        case = self.case_by_id[spec["base_case_id"]]
        response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
        response["source_location_id"] = "SL-WRONG-999"
        result = self._evaluate(case, response)
        codes = {row["code"] for row in result["boundary_issues"]}
        self.assertFalse(result["boundary_passed"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertIn(spec["expected_boundary_code"], codes)

    def test_q07_unknown_state_is_prefrozen_fail_closed_requirement_not_implemented_as_repair(self) -> None:
        spec = next(row for row in self.system_suite["cases"] if row["system_case_id"] == "SYS-STOP-UNKNOWN-STATE")
        self.assertEqual(spec["expected_behavior"], "FAIL_CLOSED_STOP")
        self.assertEqual(spec["expected_stop_code"], "UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED")
        self.assertEqual(self.policy["unknown_state_policy"], "FAIL_CLOSED_STOP")
        self.assertTrue(self.policy["unknown_state_requires_human_review"])
        self.assertFalse(self.policy["system_components_required"]["automatic_semantic_repair_allowed"])
        self.assertEqual(self.freeze["guarded_system_qualification_status"], "NOT_YET_EXECUTED")


if __name__ == "__main__":
    unittest.main()
