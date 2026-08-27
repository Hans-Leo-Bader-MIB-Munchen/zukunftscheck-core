from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche4_DRAFT_v0_1.json"

EXPECTED_IDS = {"5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "9.1", "9.2", "9.3", "9.4", "9.5"}


class MeaningTranche4DraftTests(unittest.TestCase):
    def load_draft(self) -> dict:
        self.assertTrue(DRAFT.exists())
        return json.loads(DRAFT.read_text(encoding="utf-8"))

    def rows(self) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load_draft()["meanings"]}

    def test_d01_draft_is_explicitly_non_leading(self) -> None:
        doc = self.load_draft()
        self.assertEqual(doc["status"], "HUMAN_REVIEW_DRAFT_ONLY")
        self.assertIn("v0_5", doc["guardrail"].lower())
        self.assertIn("nicht", doc["guardrail"].lower())

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
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_d04_pf5_role_functions_are_not_collapsed(self) -> None:
        rows = self.rows()
        self.assertIn("5.3", rows["5.2"]["disambiguation_notes"])
        self.assertIn("5.2", rows["5.3"]["disambiguation_notes"])
        self.assertIn("5.4", rows["5.3"]["disambiguation_notes"])
        self.assertIn("1.5", rows["5.4"]["disambiguation_notes"])

    def test_d05_55_is_existing_external_specialist_involvement_not_future_connector(self) -> None:
        row = self.rows()["5.5"]
        self.assertIn("8.1", row["disambiguation_notes"])
        self.assertIn("12.4", row["disambiguation_notes"])
        self.assertIn("bereits", row["positive_scope"].lower())

    def test_d06_56_separates_role_conflict_from_information_conflict_and_pf9(self) -> None:
        notes = self.rows()["5.6"]["disambiguation_notes"]
        for expected in ("4.5", "11.1", "9.1", "9.2"):
            self.assertIn(expected, notes)

    def test_d07_57_is_actor_interest_dependency_not_pf9_process_dependency(self) -> None:
        row = self.rows()["5.7"]
        self.assertIn("PF9", row["disambiguation_notes"])
        self.assertIn("akteurs", row["disambiguation_notes"].lower())
        self.assertIn("spekul", row["negative_scope"].lower())

    def test_d08_91_92_93_have_distinct_dependency_semantics(self) -> None:
        rows = self.rows()
        self.assertIn("9.2", rows["9.1"]["disambiguation_notes"])
        self.assertIn("9.3", rows["9.1"]["disambiguation_notes"])
        self.assertIn("9.1", rows["9.2"]["disambiguation_notes"])
        self.assertIn("vor", rows["9.3"]["positive_scope"].lower())

    def test_d09_93_is_connector_sequence_not_specialist_work(self) -> None:
        row = self.rows()["9.3"]
        self.assertIn("8.5", row["disambiguation_notes"])
        self.assertIn("12.4", row["disambiguation_notes"])
        negative = row["negative_scope"].lower()
        self.assertTrue("durchführung" in negative or "vorwegnahme" in negative)

    def test_d10_94_is_parallelization_not_override_of_dependencies(self) -> None:
        row = self.rows()["9.4"]
        self.assertIn("12.1", row["disambiguation_notes"])
        self.assertIn("parallel", row["positive_scope"].lower())
        self.assertIn("nicht", row["negative_scope"].lower())

    def test_d11_95_is_specific_stufe2_indication_not_aggregate_release(self) -> None:
        row = self.rows()["9.5"]
        self.assertIn("8.4", row["disambiguation_notes"])
        self.assertIn("12.5", row["disambiguation_notes"])
        self.assertIn("nicht", row["negative_scope"].lower())
        self.assertIn("stufe 2", row["negative_scope"].lower())

    def test_d12_all_rows_have_three_required_semantic_fields(self) -> None:
        for row in self.load_draft()["meanings"]:
            for field in ("positive_scope", "negative_scope", "disambiguation_notes"):
                self.assertIsInstance(row[field], str)
                self.assertTrue(row[field].strip())


if __name__ == "__main__":
    unittest.main()
