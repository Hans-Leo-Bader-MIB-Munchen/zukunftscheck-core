from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "tests/fixtures/zs_ki_b_sem_pf2_cross_model_countercheck_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
MEANINGS = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
PROMPT = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"


class Pf2CrossModelCountercheckTests(unittest.TestCase):
    def test_review_is_model_free_and_gold_confirmed(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(review["decision"], "GOLD_CONFIRMED")
        self.assertFalse(review["further_model_run_authorized"])
        self.assertFalse(any(review["delta_required"].values()))

    def test_frozen_pf2_case_text_is_the_reviewed_text(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        case = next(row for row in suite["cases"] if row["case_id"] == review["case_id"])
        self.assertEqual(case["source_locations"][0]["original_text"], review["case_text"])

    def test_frozen_gold_requires_21_and_22_with_24_optional(self) -> None:
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        case = next(row for row in gold["cases"] if row["case_id"] == "ZS-KI-B-SEM-V07-Q-PF2-SYN-001")
        required = {(row["question_id"], row["pf_id"]) for row in case["expected_assignments"]}
        optional = {(row["question_id"], row["pf_id"]) for row in case["optional_assignments"]}
        self.assertEqual(required, {("2.1", "PF2"), ("2.2", "PF2")})
        self.assertEqual(optional, {("2.4", "PF2")})

    def test_meaning_layer_distinguishes_explicit_scope_from_spatial_special_question(self) -> None:
        meanings = json.loads(MEANINGS.read_text(encoding="utf-8"))["meanings"]
        m22 = next(row for row in meanings if row["question_id"] == "2.2")
        m24 = next(row for row in meanings if row["question_id"] == "2.4")
        self.assertIn("Ein- und Ausschlüsse", m22["positive_scope"])
        self.assertIn("räumliche", m24["positive_scope"])

    def test_prompt_already_names_scope_markers(self) -> None:
        prompt = PROMPT.read_text(encoding="utf-8")
        self.assertIn("ausschließlich", prompt)
        self.assertIn("einschließlich", prompt)
        self.assertIn("Mehrfachprüfung", prompt)


if __name__ == "__main__":
    unittest.main()
