from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche5_DRAFT_v0_1.json"
EXPECTED_IDS = {"1.1","1.2","1.3","1.4","1.5","1.6","10.1","10.2","10.3","10.4","10.5"}

class MeaningTranche5DraftTests(unittest.TestCase):
    def load_draft(self):
        return json.loads(DRAFT.read_text(encoding="utf-8"))

    def rows(self):
        return {r["question_id"]: r for r in self.load_draft()["meanings"]}

    def test_d01_draft_is_explicitly_non_leading(self):
        doc = self.load_draft()
        self.assertEqual(doc["status"], "HUMAN_REVIEW_DRAFT_ONLY")
        self.assertIn("v0_6", doc["guardrail"].lower())
        self.assertIn("nicht", doc["guardrail"].lower())

    def test_d02_contains_exactly_11_unique_target_ids(self):
        ids = [r["question_id"] for r in self.load_draft()["meanings"]]
        self.assertEqual(len(ids), 11)
        self.assertEqual(set(ids), EXPECTED_IDS)
        self.assertEqual(len(set(ids)), 11)

    def test_d03_all_ids_bind_to_canonical_pf(self):
        q = json.loads(QUESTIONS.read_text(encoding="utf-8"))
        canonical = {r["question_id"]: r["pf_id"] for r in q["questions"]}
        for r in self.load_draft()["meanings"]:
            self.assertEqual(r["pf_id"], canonical[r["question_id"]])

    def test_d04_11_12_separate_org_from_contact_and_pf5_roles(self):
        rows = self.rows()
        self.assertIn("1.2", rows["1.1"]["disambiguation_notes"])
        self.assertIn("5.1", rows["1.1"]["disambiguation_notes"])
        self.assertIn("5.2", rows["1.2"]["disambiguation_notes"])
        self.assertIn("5.3", rows["1.2"]["disambiguation_notes"])

    def test_d05_13_question_not_object_or_specialist_answer(self):
        row = self.rows()["1.3"]
        self.assertIn("2.1", row["disambiguation_notes"])
        self.assertIn("11.5", row["disambiguation_notes"])
        self.assertIn("12.4", row["disambiguation_notes"])

    def test_d06_14_expected_result_not_next_step(self):
        row = self.rows()["1.4"]
        self.assertIn("12.1", row["disambiguation_notes"])
        self.assertIn("eingangs", row["disambiguation_notes"].lower())
        self.assertIn("ausgangs", row["disambiguation_notes"].lower())

    def test_d07_15_addressing_separate_from_release_and_data_forwarding(self):
        row = self.rows()["1.5"]
        self.assertIn("5.4", row["disambiguation_notes"])
        self.assertIn("10.4", row["disambiguation_notes"])

    def test_d08_16_is_input_boundary_mirrored_to_126(self):
        row = self.rows()["1.6"]
        self.assertIn("12.6", row["disambiguation_notes"])
        self.assertIn("eingangs", row["disambiguation_notes"].lower())
        self.assertIn("ausgangs", row["disambiguation_notes"].lower())

    def test_d09_pf10_classification_need_action_are_distinct(self):
        rows = self.rows()
        self.assertIn("10.2", rows["10.1"]["disambiguation_notes"])
        self.assertIn("10.5", rows["10.1"]["disambiguation_notes"])
        self.assertIn("10.3", rows["10.2"]["disambiguation_notes"])
        self.assertIn("10.1", rows["10.3"]["disambiguation_notes"])

    def test_d10_104_separate_from_15_and_54(self):
        row = self.rows()["10.4"]
        self.assertIn("1.5", row["disambiguation_notes"])
        self.assertIn("5.4", row["disambiguation_notes"])
        self.assertIn("nicht automatisch", row["disambiguation_notes"].lower())

    def test_d11_105_is_fail_closed_stop_question(self):
        row = self.rows()["10.5"]
        text = (row["positive_scope"] + " " + row["disambiguation_notes"]).lower()
        self.assertTrue("stop" in text or "aussetz" in text)
        self.assertIn("10.1", row["disambiguation_notes"])
        self.assertIn("10.4", row["disambiguation_notes"])

    def test_d12_all_rows_have_three_required_semantic_fields(self):
        for r in self.load_draft()["meanings"]:
            for field in ("positive_scope","negative_scope","disambiguation_notes"):
                self.assertIsInstance(r[field], str)
                self.assertTrue(r[field].strip())

    def test_d13_101_does_not_invent_classification(self):
        negative = self.rows()["10.1"]["negative_scope"].lower()
        self.assertIn("eigenständige klassifizierung", negative)
        self.assertIn("dokumentierte grundlage", negative)

    def test_d14_102_does_not_create_processing_legal_basis(self):
        row = self.rows()["10.2"]
        self.assertNotIn("verarbeitet werden müssen", row["positive_scope"].lower())
        negative = row["negative_scope"].lower()
        self.assertTrue("verarbeitungsbefugnis" in negative or "rechtsgrundlage" in negative)

    def test_d15_105_binds_red_data_and_stop_to_documented_external_rule(self):
        negative = self.rows()["10.5"]["negative_scope"].lower()
        self.assertIn("extern dokumentierte", negative)
        self.assertIn("aussetzungsregel", negative)
        self.assertIn("nicht die eigenständige festlegung", negative)

if __name__ == "__main__":
    unittest.main()
