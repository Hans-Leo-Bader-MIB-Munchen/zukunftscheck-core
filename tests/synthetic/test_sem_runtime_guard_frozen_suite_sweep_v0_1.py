from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_runtime_guard_v0_1 import evaluate_semantic_runtime_guard

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
EXPECTATIONS = ROOT / "tests/fixtures/zs_ki_b_sem_runtime_guard_frozen_suite_sweep_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_gold_complete_response(case: dict, gold_case: dict) -> dict:
    target = case["target_source_location_id"]
    assignments = []
    for row in gold_case.get("expected_assignments", []):
        assignments.append(
            {
                "question_id": row["question_id"],
                "pf_id": row["pf_id"],
                "assignment_confidence": "CLEAR",
                "human_review_required": False,
            }
        )
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target,
        "proposals": [
            {
                "proposal_id": f"P-{target}-SWEEP",
                "source_location_id": target,
                "normalized_statement": case["source_locations"][-1]["original_text"],
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": assignments,
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": False,
            }
        ],
    }


class SemRuntimeGuardFrozenSuiteSweepV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load(SUITE)
        cls.gold = load(GOLD)
        cls.expectations = load(EXPECTATIONS)
        cls.gold_by_id = {row["case_id"]: row for row in cls.gold["cases"]}

    def _evaluate(self, case: dict, response: dict) -> dict:
        target = case["target_source_location_id"]
        source_by_id = {row["source_location_id"]: row for row in case["source_locations"]}
        source_text = source_by_id[target]["original_text"]
        allowed = set(source_by_id)
        return evaluate_semantic_runtime_guard(
            source_text=source_text,
            model_response=response,
            allowed_source_location_ids=allowed,
            target_source_location_id=target,
        )

    def test_s01_fixture_is_model_free_and_16_case_bound(self) -> None:
        self.assertEqual(len(self.suite["cases"]), 16)
        self.assertEqual(self.expectations["complete_gold_case_count"], 16)
        self.assertFalse(self.expectations["model_run_authorized"])
        self.assertFalse(self.expectations["real_data_authorized"])
        self.assertFalse(self.expectations["pilot_authorized"])
        self.assertFalse(self.expectations["production_authorized"])
        self.assertFalse(self.expectations["phase_f_authorized"])

    def test_s02_all_gold_complete_cases_pass_boundary(self) -> None:
        for case in self.suite["cases"]:
            response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
            result = self._evaluate(case, response)
            self.assertTrue(result["boundary_passed"], case["case_id"])

    def test_s03_complete_gold_cases_produce_no_false_positive_stop(self) -> None:
        hits = []
        for case in self.suite["cases"]:
            response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
            result = self._evaluate(case, response)
            if result["human_review_required"] or not result["automatic_downstream_use_allowed"]:
                hits.append(case["case_id"])
        self.assertEqual(hits, self.expectations["expected_false_positive_case_ids"])

    def test_s04_pf2_reproduced_underassignment_is_detected(self) -> None:
        case = next(row for row in self.suite["cases"] if row["case_id"] == "ZS-KI-B-SEM-V07-Q-PF2-SYN-001")
        response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
        before = copy.deepcopy(response)
        remove = self.expectations["pf2_underassignment_removed_assignment"]
        response["proposals"][0]["assignment_candidates"] = [
            row
            for row in response["proposals"][0]["assignment_candidates"]
            if not (row["question_id"] == remove["question_id"] and row["pf_id"] == remove["pf_id"])
        ]
        underassigned = copy.deepcopy(response)
        result = self._evaluate(case, response)
        self.assertTrue(result["boundary_passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertTrue(result["completeness_audit"]["possible_multi_assignment_omission"])
        self.assertEqual(response, underassigned)
        self.assertNotEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertEqual(result["decision_authority"], "NONE")

    def test_s05_non_pf2_cases_do_not_activate_pf2_completeness_stop(self) -> None:
        for case in self.suite["cases"]:
            if case["case_id"] == "ZS-KI-B-SEM-V07-Q-PF2-SYN-001":
                continue
            response = build_gold_complete_response(case, self.gold_by_id[case["case_id"]])
            result = self._evaluate(case, response)
            audit = result["completeness_audit"]
            self.assertIsNotNone(audit, case["case_id"])
            self.assertFalse(audit["possible_multi_assignment_omission"], case["case_id"])


if __name__ == "__main__":
    unittest.main()
