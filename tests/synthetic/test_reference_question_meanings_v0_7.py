from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
V06 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_6.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche5_DRAFT_v0_1.json"
V07 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"


class MeaningV07Tests(unittest.TestCase):
    def load(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(self, path: Path):
        return {r["question_id"]: r for r in self.load(path)["meanings"]}

    def test_v01_schema_and_complete_count(self):
        doc = self.load(V07)
        ids = [r["question_id"] for r in doc["meanings"]]
        self.assertEqual(doc["schema_version"], "v0.7")
        self.assertEqual(len(ids), 67)
        self.assertEqual(len(set(ids)), 67)

    def test_v02_matches_all_canonical_question_ids(self):
        canonical = {r["question_id"] for r in self.load(QUESTIONS)["questions"]}
        actual = {r["question_id"] for r in self.load(V07)["meanings"]}
        self.assertEqual(actual, canonical)

    def test_v03_preserves_all_56_v06_rows_exactly(self):
        old = self.rows(V06)
        new = self.rows(V07)
        self.assertEqual(len(old), 56)
        for qid, row in old.items():
            self.assertEqual(new[qid], row)

    def test_v04_adopts_all_11_reviewed_tranche5_rows_exactly(self):
        draft = self.rows(DRAFT)
        new = self.rows(V07)
        self.assertEqual(len(draft), 11)
        for qid, row in draft.items():
            self.assertEqual(new[qid], row)

    def test_v05_all_pf_bindings_match_canonical_schema(self):
        canonical = {r["question_id"]: r["pf_id"] for r in self.load(QUESTIONS)["questions"]}
        for row in self.load(V07)["meanings"]:
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_v06_pf1_cross_pf_boundaries_are_retained(self):
        rows = self.rows(V07)
        self.assertIn("12.1", rows["1.4"]["disambiguation_notes"])
        self.assertIn("5.4", rows["1.5"]["disambiguation_notes"])
        self.assertIn("10.4", rows["1.5"]["disambiguation_notes"])
        self.assertIn("12.6", rows["1.6"]["disambiguation_notes"])

    def test_v07_pf10_fail_closed_governance_boundaries_are_retained(self):
        rows = self.rows(V07)
        self.assertIn("eigenständige klassifizierung", rows["10.1"]["negative_scope"].lower())
        self.assertIn("rechtsgrundlage", rows["10.2"]["negative_scope"].lower())
        self.assertIn("extern dokumentierte", rows["10.5"]["negative_scope"].lower())
        self.assertIn("aussetzungsregel", rows["10.5"]["negative_scope"].lower())

    def test_v08_complete_coverage_is_not_model_or_product_approval(self):
        scope = self.load(V07)["calibration_scope"].lower()
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)
        self.assertIn("67 von 67", scope)

    def test_v09_all_rows_have_required_semantic_fields(self):
        for row in self.load(V07)["meanings"]:
            for field in ("positive_scope", "negative_scope", "disambiguation_notes"):
                self.assertIsInstance(row[field], str)
                self.assertTrue(row[field].strip())


if __name__ == "__main__":
    unittest.main()
