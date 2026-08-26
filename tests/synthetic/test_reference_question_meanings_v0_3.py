from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
V02 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_2.json"
V03 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_3.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche1_DRAFT_v0_1.json"

TRANCHE_IDS = {
    "3.1", "4.3", "4.4", "4.5", "4.6",
    "7.4", "7.5", "7.6",
    "11.1", "11.3", "11.4", "11.5",
}


class ReferenceQuestionMeaningsV03Tests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        self.assertTrue(path.exists(), f"missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(self, path: Path) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load(path)["meanings"]}

    def test_v03_01_contains_exactly_24_unique_ids(self) -> None:
        doc = self.load(V03)
        ids = [row["question_id"] for row in doc["meanings"]]
        self.assertEqual(doc["schema_version"], "v0.3")
        self.assertEqual(len(ids), 24)
        self.assertEqual(len(set(ids)), 24)

    def test_v03_02_all_v02_rows_are_byte_semantically_unchanged(self) -> None:
        old = self.rows(V02)
        new = self.rows(V03)
        for question_id, old_row in old.items():
            self.assertIn(question_id, new)
            self.assertEqual(new[question_id], old_row)

    def test_v03_03_tranche_rows_match_reviewed_draft(self) -> None:
        draft = self.rows(DRAFT)
        new = self.rows(V03)
        self.assertEqual(set(draft), TRANCHE_IDS)
        for question_id in TRANCHE_IDS:
            self.assertIn(question_id, new)
            self.assertEqual(new[question_id], draft[question_id])

    def test_v03_04_union_is_exactly_v02_plus_tranche1(self) -> None:
        old_ids = set(self.rows(V02))
        new_ids = set(self.rows(V03))
        self.assertEqual(new_ids, old_ids | TRANCHE_IDS)
        self.assertTrue(old_ids.isdisjoint(TRANCHE_IDS))

    def test_v03_05_all_ids_bind_to_canonical_pf(self) -> None:
        questions = self.load(QUESTIONS)
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        self.assertEqual(len(canonical), 67)
        for row in self.load(V03)["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_v03_06_scope_is_explicitly_partial_and_non_productive(self) -> None:
        scope = self.load(V03)["calibration_scope"].lower()
        self.assertIn("24 von 67", scope)
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)

    def test_v03_07_cross_pf_44_113_123_is_explicit(self) -> None:
        rows = self.rows(V03)
        self.assertIn("11.3", rows["4.4"]["disambiguation_notes"])
        self.assertIn("12.3", rows["4.4"]["disambiguation_notes"])
        self.assertIn("4.4", rows["11.3"]["disambiguation_notes"])
        self.assertIn("12.3", rows["11.3"]["disambiguation_notes"])

    def test_v03_08_113_and_115_are_explicitly_separated(self) -> None:
        rows = self.rows(V03)
        self.assertIn("11.5", rows["11.3"]["disambiguation_notes"])
        self.assertIn("11.3", rows["11.5"]["disambiguation_notes"])
        self.assertIn("schließbare", rows["11.3"]["disambiguation_notes"].lower())
        self.assertIn("fachliche offenheit", rows["11.5"]["disambiguation_notes"].lower())

    def test_v03_09_stage1_boundary_remains_explicit(self) -> None:
        rows = self.rows(V03)
        self.assertIn("nicht selbst ersetzen", rows["7.6"]["disambiguation_notes"].lower())
        self.assertIn("nicht selbst fachlich entscheiden", rows["11.5"]["disambiguation_notes"].lower())


if __name__ == "__main__":
    unittest.main()
