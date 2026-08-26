from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
V03 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_3.json"
V04 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_4.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche2_DRAFT_v0_1.json"

TRANCHE2_IDS = {"2.2", "2.3", "2.4", "2.5", "12.1", "12.2", "12.3", "12.4", "12.5", "12.6"}


class ReferenceQuestionMeaningsV04Tests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        self.assertTrue(path.exists(), f"missing {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(self, path: Path) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load(path)["meanings"]}

    def test_v04_has_34_unique_meanings(self) -> None:
        doc = self.load(V04)
        ids = [row["question_id"] for row in doc["meanings"]]
        self.assertEqual(doc["schema_version"], "v0.4")
        self.assertEqual(len(ids), 34)
        self.assertEqual(len(set(ids)), 34)

    def test_v03_is_preserved_exactly(self) -> None:
        v03 = self.rows(V03)
        v04 = self.rows(V04)
        self.assertEqual(len(v03), 24)
        for question_id, meaning in v03.items():
            self.assertIn(question_id, v04)
            self.assertEqual(v04[question_id], meaning)

    def test_tranche2_is_adopted_exactly_from_reviewed_draft(self) -> None:
        draft = self.rows(DRAFT)
        v04 = self.rows(V04)
        self.assertEqual(set(draft), TRANCHE2_IDS)
        for question_id in TRANCHE2_IDS:
            self.assertEqual(v04[question_id], draft[question_id])

    def test_all_ids_bind_to_canonical_pf(self) -> None:
        questions = self.load(QUESTIONS)
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        self.assertEqual(len(canonical), 67)
        for row in self.load(V04)["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_25_has_no_rejected_extra_threshold(self) -> None:
        row = self.rows(V04)["2.5"]
        positive = row["positive_scope"].lower()
        self.assertNotIn("verkürzen", positive)
        self.assertNotIn("verzerren", positive)
        self.assertIn("12.5", row["disambiguation_notes"])

    def test_24_explicitly_separates_pf6_neighbors(self) -> None:
        notes = self.rows(V04)["2.4"]["disambiguation_notes"]
        self.assertIn("6.2", notes)
        self.assertIn("6.4", notes)

    def test_125_explicitly_separates_95(self) -> None:
        notes = self.rows(V04)["12.5"]["disambiguation_notes"]
        self.assertIn("9.5", notes)
        self.assertIn("2.5", notes)

    def test_126_explicitly_separates_16_and_124(self) -> None:
        row = self.rows(V04)["12.6"]
        notes = row["disambiguation_notes"]
        self.assertIn("1.6", notes)
        self.assertIn("12.4", notes)
        self.assertIn("stufe 1", row["positive_scope"].lower())

    def test_scope_remains_model_free_and_non_productive(self) -> None:
        scope = self.load(V04)["calibration_scope"].lower()
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)


if __name__ == "__main__":
    unittest.main()
