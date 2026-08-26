from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
DRAFT = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_tranche2_DRAFT_v0_1.json"

EXPECTED_IDS = {"2.2", "2.3", "2.4", "2.5", "12.1", "12.2", "12.3", "12.4", "12.5", "12.6"}


class MeaningTranche2DraftTests(unittest.TestCase):
    def load_draft(self) -> dict:
        self.assertTrue(DRAFT.exists())
        return json.loads(DRAFT.read_text(encoding="utf-8"))

    def rows(self) -> dict[str, dict]:
        return {row["question_id"]: row for row in self.load_draft()["meanings"]}

    def test_d01_draft_is_explicitly_non_leading(self) -> None:
        doc = self.load_draft()
        self.assertEqual(doc["status"], "HUMAN_REVIEW_DRAFT_ONLY")
        self.assertIn("v0_3", doc["guardrail"].lower())
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

    def test_d04_pf2_chain_separates_scope_boundability_space_and_dependencies(self) -> None:
        rows = self.rows()
        self.assertIn("2.3", rows["2.2"]["disambiguation_notes"])
        self.assertIn("2.4", rows["2.3"]["disambiguation_notes"])
        self.assertIn("räum", rows["2.4"]["positive_scope"].lower())
        self.assertIn("teilgegen", rows["2.5"]["positive_scope"].lower())

    def test_d05_25_vs_125_is_explicitly_separated_without_extra_threshold(self) -> None:
        rows = self.rows()
        self.assertIn("12.5", rows["2.5"]["disambiguation_notes"])
        self.assertIn("2.5", rows["12.5"]["disambiguation_notes"])
        self.assertIn("nahelegen", rows["2.5"]["positive_scope"].lower())
        self.assertNotIn("verkürzen", rows["2.5"]["positive_scope"].lower())
        self.assertNotIn("verzerren", rows["2.5"]["positive_scope"].lower())
        self.assertIn("nicht", rows["12.5"]["negative_scope"].lower())
        self.assertIn("beauftragung", rows["12.5"]["negative_scope"].lower())

    def test_d06_123_is_separated_from_missing_information_findings(self) -> None:
        row = self.rows()["12.3"]
        self.assertIn("4.4", row["disambiguation_notes"])
        self.assertIn("11.3", row["disambiguation_notes"])
        self.assertIn("11.4", row["disambiguation_notes"])

    def test_d07_124_is_a_connector_not_specialist_decision(self) -> None:
        row = self.rows()["12.4"]
        self.assertIn("fachlichen anschluss", row["positive_scope"].lower())
        self.assertTrue(
            "durchführung" in row["negative_scope"].lower()
            or "vorwegnahme" in row["negative_scope"].lower()
        )
        self.assertIn("11.5", row["disambiguation_notes"])

    def test_d08_121_122_123_form_step_owner_input_chain(self) -> None:
        rows = self.rows()
        self.assertIn("nächsten", rows["12.1"]["positive_scope"].lower())
        self.assertIn("zuständ", rows["12.2"]["positive_scope"].lower())
        self.assertTrue(
            "unterlage" in rows["12.3"]["positive_scope"].lower()
            or "bestätigung" in rows["12.3"]["positive_scope"].lower()
        )

    def test_d09_126_explicitly_preserves_stage1_non_replacement_boundary(self) -> None:
        row = self.rows()["12.6"]
        positive = row["positive_scope"].lower()
        self.assertIn("stufe 1", positive)
        self.assertTrue("fachentscheid" in positive or "qualitätsbestät" in positive or "freigab" in positive)
        self.assertIn("nicht", row["negative_scope"].lower())

    def test_d10_24_explicitly_separates_pf6_spatial_evidence_checks(self) -> None:
        notes = self.rows()["2.4"]["disambiguation_notes"]
        self.assertIn("6.2", notes)
        self.assertIn("6.4", notes)

    def test_d11_125_explicitly_separates_pf9_stage2_indication(self) -> None:
        notes = self.rows()["12.5"]["disambiguation_notes"]
        self.assertIn("9.5", notes)
        self.assertIn("aggregierende", notes.lower())

    def test_d12_126_separates_input_guardrail_and_concrete_connector(self) -> None:
        notes = self.rows()["12.6"]["disambiguation_notes"]
        self.assertIn("1.6", notes)
        self.assertIn("12.4", notes)
        self.assertIn("eingangsseitig", notes.lower())
        self.assertIn("ausgangsseitig", notes.lower())


if __name__ == "__main__":
    unittest.main()
