from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_1.json"


class ReferenceQuestionMeaningsV01Tests(unittest.TestCase):
    def load(self) -> tuple[dict, dict]:
        self.assertTrue(MEANINGS.exists(), "reference question meaning layer must exist")
        return (
            json.loads(QUESTIONS.read_text(encoding="utf-8")),
            json.loads(MEANINGS.read_text(encoding="utf-8")),
        )

    def test_t8_r16_neighbor_meanings_are_explicit_without_new_ids_or_pfs(self) -> None:
        questions, meanings = self.load()
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        rows = {row["question_id"]: row for row in meanings["meanings"]}
        self.assertEqual(set(rows), {"2.1", "3.5", "4.1", "7.1", "11.2"})
        for question_id, row in rows.items():
            self.assertEqual(row["pf_id"], canonical[question_id])
            self.assertTrue(str(row.get("positive_scope", "")).strip())
            self.assertTrue(str(row.get("negative_scope", "")).strip())
        self.assertIn("unterlag", rows["4.1"]["positive_scope"].lower())
        self.assertIn("gegenstand", rows["4.1"]["negative_scope"].lower())
        self.assertIn("unbelegt", rows["11.2"]["positive_scope"].lower())
        self.assertTrue("nutzung" in rows["11.2"]["negative_scope"].lower() or "entscheid" in rows["11.2"]["negative_scope"].lower())

    def test_t9_meaning_layer_is_explicitly_limited_and_not_claimed_as_67_question_validation(self) -> None:
        questions, meanings = self.load()
        self.assertEqual(len(questions["questions"]), 67)
        self.assertLess(len(meanings["meanings"]), 67)
        scope = str(meanings.get("calibration_scope", "")).lower()
        self.assertIn("r16", scope)
        self.assertTrue("nicht" in scope or "keine" in scope)
        self.assertTrue("67" in scope or "alle" in scope)


if __name__ == "__main__":
    unittest.main()
