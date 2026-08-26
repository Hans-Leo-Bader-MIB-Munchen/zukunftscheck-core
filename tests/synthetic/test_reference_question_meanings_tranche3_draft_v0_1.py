from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche3_DRAFT_v0_1.json"

EXPECTED_IDS = {"6.1", "6.2", "6.3", "6.4", "6.5", "8.1", "8.2", "8.3", "8.4", "8.5"}


class MeaningTranche3DraftTests(unittest.TestCase):
    def load_draft(self) -> dict:
        self.assertTrue(DRAFT.exists())
        return json.loads(DRAFT.read_text(encoding="utf-8"))

    def rows(self) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load_draft()["meanings"]}

    def test_d01_draft_is_explicitly_non_leading(self) -> None:
        doc = self.load_draft()
        self.assertEqual(doc["status"], "HUMAN_REVIEW_DRAFT_ONLY")
        self.assertIn("v0_4", doc["guardrail"].lower())
        self.assertIn("nicht", doc["guardrail"].lower())

    def test_d02_contains_exactly_10_unique_target_ids(self) -> None:
        rows = self.load_draft()["meanings"]
        ids = [row["question_id"] for row in rows]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertEqual(set(ids), EXPECTED_IDS)

    def test_d03_all_ids_bind_to_canonical_pf(self) -> None:
        questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        for row in self.load_draft()["meanings"]:
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_d04_62_is_explicitly_separated_from_24(self) -> None:
        row = self.rows()["6.2"]
        self.assertIn("2.4", row["disambiguation_notes"])
        self.assertIn("unterlagen", row["positive_scope"].lower())

    def test_d05_64_is_spatially_specialized_against_general_gaps_and_conflicts(self) -> None:
        row = self.rows()["6.4"]
        notes = row["disambiguation_notes"]
        for expected in ("4.4", "4.5", "11.1", "11.3"):
            self.assertIn(expected, notes)
        self.assertIn("räum", row["positive_scope"].lower())

    def test_d06_65_is_connector_not_specialist_work(self) -> None:
        row = self.rows()["6.5"]
        self.assertIn("7.6", row["disambiguation_notes"])
        self.assertIn("12.4", row["disambiguation_notes"])
        negative = row["negative_scope"].lower()
        self.assertTrue("durchführung" in negative or "vorwegnahme" in negative)

    def test_d07_81_and_82_are_separated_from_general_document_questions(self) -> None:
        rows = self.rows()
        self.assertIn("4.1", rows["8.1"]["disambiguation_notes"])
        self.assertIn("4.2", rows["8.2"]["disambiguation_notes"])
        self.assertIn("8.2", rows["8.1"]["disambiguation_notes"])
        self.assertIn("8.3", rows["8.2"]["disambiguation_notes"])

    def test_d08_83_marks_scope_of_existing_specialist_work_not_new_answer(self) -> None:
        row = self.rows()["8.3"]
        self.assertIn("11.5", row["disambiguation_notes"])
        self.assertIn("nicht", row["negative_scope"].lower())
        self.assertIn("beantwort", row["negative_scope"].lower())

    def test_d09_84_is_specialist_contribution_interface_not_general_conflict(self) -> None:
        row = self.rows()["8.4"]
        notes = row["disambiguation_notes"]
        self.assertIn("4.5", notes)
        self.assertIn("11.1", notes)
        self.assertIn("PF9", notes)
        self.assertIn("fachbeitr", row["positive_scope"].lower())

    def test_d10_85_is_separated_from_115_and_124(self) -> None:
        row = self.rows()["8.5"]
        self.assertIn("11.5", row["disambiguation_notes"])
        self.assertIn("12.4", row["disambiguation_notes"])
        negative = row["negative_scope"].lower()
        self.assertIn("nicht", negative)
        self.assertTrue("beantwort" in negative or "beauftragung" in negative)

    def test_d11_all_rows_have_three_required_semantic_fields(self) -> None:
        for row in self.load_draft()["meanings"]:
            for field in ("positive_scope", "negative_scope", "disambiguation_notes"):
                self.assertIsInstance(row[field], str)
                self.assertTrue(row[field].strip())


if __name__ == "__main__":
    unittest.main()
