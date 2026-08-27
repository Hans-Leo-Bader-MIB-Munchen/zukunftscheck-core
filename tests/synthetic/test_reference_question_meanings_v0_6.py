from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
V05 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_5.json"
V06 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_6.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche4_DRAFT_v0_1.json"

TRANCHE4_IDS = {"5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "9.1", "9.2", "9.3", "9.4", "9.5"}


class ReferenceQuestionMeaningsV06Tests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        self.assertTrue(path.exists(), f"missing {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(self, path: Path) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load(path)["meanings"]}

    def test_v06_has_56_unique_meanings(self) -> None:
        doc = self.load(V06)
        ids = [row["question_id"] for row in doc["meanings"]]
        self.assertEqual(doc["schema_version"], "v0.6")
        self.assertEqual(len(ids), 56)
        self.assertEqual(len(set(ids)), 56)

    def test_v05_is_preserved_exactly(self) -> None:
        v05 = self.rows(V05)
        v06 = self.rows(V06)
        self.assertEqual(len(v05), 44)
        for question_id, meaning in v05.items():
            self.assertIn(question_id, v06)
            self.assertEqual(v06[question_id], meaning)

    def test_tranche4_is_adopted_exactly_from_reviewed_draft(self) -> None:
        draft = self.rows(DRAFT)
        v06 = self.rows(V06)
        self.assertEqual(set(draft), TRANCHE4_IDS)
        for question_id in TRANCHE4_IDS:
            self.assertEqual(v06[question_id], draft[question_id])

    def test_all_ids_bind_to_canonical_pf(self) -> None:
        questions = self.load(QUESTIONS)
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        self.assertEqual(len(canonical), 67)
        for row in self.load(V06)["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_54_explicitly_separates_addressing_from_internal_release(self) -> None:
        notes = self.rows(V06)["5.4"]["disambiguation_notes"]
        self.assertIn("1.5", notes)
        self.assertIn("adress", notes.lower())
        self.assertIn("freigab", notes.lower())

    def test_91_explicitly_separates_actor_dependency_from_process_dependency(self) -> None:
        notes = self.rows(V06)["9.1"]["disambiguation_notes"]
        self.assertIn("5.7", notes)
        self.assertIn("akteurs", notes.lower())
        self.assertIn("sachlich", notes.lower())

    def test_94_does_not_authorize_independent_schedule_planning(self) -> None:
        negative = self.rows(V06)["9.4"]["negative_scope"].lower()
        self.assertIn("ablaufplanung", negative)
        self.assertIn("sequenzierung", negative)

    def test_95_remains_specific_indication_not_aggregate_release(self) -> None:
        row = self.rows(V06)["9.5"]
        self.assertIn("8.4", row["disambiguation_notes"])
        self.assertIn("12.5", row["disambiguation_notes"])
        self.assertIn("stufe 2", row["negative_scope"].lower())

    def test_scope_remains_model_free_and_non_productive(self) -> None:
        scope = self.load(V06)["calibration_scope"].lower()
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)


if __name__ == "__main__":
    unittest.main()
