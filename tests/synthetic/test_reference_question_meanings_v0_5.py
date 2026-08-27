from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
V04 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_4.json"
V05 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_5.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche3_DRAFT_v0_1.json"

TRANCHE3_IDS = {"6.1", "6.2", "6.3", "6.4", "6.5", "8.1", "8.2", "8.3", "8.4", "8.5"}


class ReferenceQuestionMeaningsV05Tests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        self.assertTrue(path.exists(), f"missing {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(self, path: Path) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load(path)["meanings"]}

    def test_v05_has_44_unique_meanings(self) -> None:
        doc = self.load(V05)
        ids = [row["question_id"] for row in doc["meanings"]]
        self.assertEqual(doc["schema_version"], "v0.5")
        self.assertEqual(len(ids), 44)
        self.assertEqual(len(set(ids)), 44)

    def test_v04_is_preserved_exactly(self) -> None:
        v04 = self.rows(V04)
        v05 = self.rows(V05)
        self.assertEqual(len(v04), 34)
        for question_id, meaning in v04.items():
            self.assertIn(question_id, v05)
            self.assertEqual(v05[question_id], meaning)

    def test_tranche3_is_adopted_exactly_from_reviewed_draft(self) -> None:
        draft = self.rows(DRAFT)
        v05 = self.rows(V05)
        self.assertEqual(set(draft), TRANCHE3_IDS)
        for question_id in TRANCHE3_IDS:
            self.assertEqual(v05[question_id], draft[question_id])

    def test_union_is_exactly_v04_plus_tranche3(self) -> None:
        v04_ids = set(self.rows(V04))
        v05_ids = set(self.rows(V05))
        self.assertTrue(v04_ids.isdisjoint(TRANCHE3_IDS))
        self.assertEqual(v05_ids, v04_ids | TRANCHE3_IDS)

    def test_all_ids_bind_to_canonical_pf(self) -> None:
        questions = self.load(QUESTIONS)
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        self.assertEqual(len(canonical), 67)
        for row in self.load(V05)["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_84_explicitly_separates_pf9_consequences(self) -> None:
        notes = self.rows(V05)["8.4"]["disambiguation_notes"]
        for expected in ("9.1", "9.3", "9.5"):
            self.assertIn(expected, notes)
        self.assertIn("PF9", notes)

    def test_85_preserves_and_documents_pf8_specific_sighting_scope(self) -> None:
        row = self.rows(V05)["8.5"]
        self.assertIn("sichtung", row["positive_scope"].lower())
        notes = row["disambiguation_notes"].lower()
        self.assertIn("sichtungsbezug", notes)
        self.assertIn("12.4", notes)
        self.assertIn("11.5", notes)

    def test_cross_pf_spatial_boundaries_remain_explicit(self) -> None:
        rows = self.rows(V05)
        self.assertIn("2.4", rows["6.2"]["disambiguation_notes"])
        for expected in ("4.4", "4.5", "11.1", "11.3"):
            self.assertIn(expected, rows["6.4"]["disambiguation_notes"])
        self.assertIn("7.6", rows["6.5"]["disambiguation_notes"])
        self.assertIn("12.4", rows["6.5"]["disambiguation_notes"])

    def test_scope_states_44_of_67_and_remains_non_productive(self) -> None:
        scope = self.load(V05)["calibration_scope"].lower()
        self.assertIn("44 von 67", scope)
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)


if __name__ == "__main__":
    unittest.main()
