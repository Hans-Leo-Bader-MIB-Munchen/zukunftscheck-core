from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche1_DRAFT_v0_1.json"

EXPECTED_IDS = {
    "3.1", "4.3", "4.4", "4.5", "4.6",
    "7.4", "7.5", "7.6",
    "11.1", "11.3", "11.4", "11.5",
}


class MeaningTranche1DraftTests(unittest.TestCase):
    def load_draft(self) -> dict:
        self.assertTrue(DRAFT.exists())
        return json.loads(DRAFT.read_text(encoding="utf-8"))

    def rows(self) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load_draft()["meanings"]}

    def test_d01_draft_is_explicitly_non_leading(self) -> None:
        doc = self.load_draft()
        self.assertEqual(doc["status"], "HUMAN_REVIEW_DRAFT_ONLY")
        self.assertIn("nicht", doc["guardrail"].lower())
        self.assertIn("führend", doc["guardrail"].lower())

    def test_d02_contains_exactly_12_unique_target_ids(self) -> None:
        rows = self.load_draft()["meanings"]
        ids = [row["question_id"] for row in rows]
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(set(ids), EXPECTED_IDS)

    def test_d03_all_ids_bind_to_canonical_pf(self) -> None:
        questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        for row in self.load_draft()["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_d04_pf4_vs_pf11_missing_information_is_explicitly_separated(self) -> None:
        rows = self.rows()
        self.assertIn("11.3", rows["4.4"]["disambiguation_notes"])
        self.assertIn("4.4", rows["11.3"]["disambiguation_notes"])
        self.assertIn("entscheidungserheb", rows["11.3"]["positive_scope"].lower())

    def test_d05_pf4_vs_pf11_contradiction_is_explicitly_separated(self) -> None:
        rows = self.rows()
        self.assertIn("11.1", rows["4.5"]["disambiguation_notes"])
        self.assertIn("4.5", rows["11.1"]["disambiguation_notes"])
        self.assertIn("entscheidungserheb", rows["11.1"]["positive_scope"].lower())

    def test_d06_pf4_vs_pf11_request_is_explicitly_separated(self) -> None:
        rows = self.rows()
        self.assertIn("11.4", rows["4.6"]["disambiguation_notes"])
        self.assertIn("4.6", rows["11.4"]["disambiguation_notes"])
        self.assertIn("prüflücke", rows["11.4"]["positive_scope"].lower())

    def test_d07_pf7_chain_separates_plan_actual_basis_and_followup(self) -> None:
        rows = self.rows()
        self.assertIn("plan-ist", rows["7.4"]["disambiguation_notes"].lower())
        self.assertIn("7.6", rows["7.5"]["disambiguation_notes"])
        self.assertIn("nicht", rows["7.6"]["negative_scope"].lower())
        self.assertTrue(
            "durchführung" in rows["7.6"]["negative_scope"].lower()
            or "vorwegnahme" in rows["7.6"]["negative_scope"].lower()
        )

    def test_d08_115_marks_stage1_boundary_without_answering_specialist_question(self) -> None:
        row = self.rows()["11.5"]
        self.assertIn("fachlich offen", row["positive_scope"].lower())
        self.assertIn("nicht", row["negative_scope"].lower())
        self.assertIn("nicht selbst fachlich entscheiden", row["disambiguation_notes"].lower())


if __name__ == "__main__":
    unittest.main()
