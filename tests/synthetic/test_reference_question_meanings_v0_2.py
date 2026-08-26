from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS_V01 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_1.json"
MEANINGS_V02 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_2.json"
PROMPT_V04 = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_4.txt"
RUNNER_V06 = ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_6.py"

EXPECTED_IDS = {"2.1", "3.2", "3.3", "3.4", "3.5", "4.1", "4.2", "7.1", "7.2", "7.3", "11.2", "11.6"}


class ReferenceQuestionMeaningsV02Tests(unittest.TestCase):
    def load_questions(self) -> dict:
        return json.loads(QUESTIONS.read_text(encoding="utf-8"))

    def load_v02(self) -> dict:
        self.assertTrue(MEANINGS_V02.exists(), "reference_question_meanings_v0_2.json must exist")
        return json.loads(MEANINGS_V02.read_text(encoding="utf-8"))

    def test_t15_v01_meaning_layer_remains_r16_limited(self) -> None:
        v01 = json.loads(MEANINGS_V01.read_text(encoding="utf-8"))
        self.assertEqual(v01["schema_version"], "v0.1")
        self.assertEqual({row["question_id"] for row in v01["meanings"]}, {"2.1", "3.5", "4.1", "7.1", "11.2"})
        self.assertIn("r16", str(v01.get("calibration_scope", "")).lower())

    def test_t16_v02_contains_exactly_12_unique_question_ids(self) -> None:
        v02 = self.load_v02()
        rows = v02["meanings"]
        ids = [row["question_id"] for row in rows]
        self.assertEqual(v02["schema_version"], "v0.2")
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(set(ids), EXPECTED_IDS)

    def test_t17_all_ids_exist_in_67_snapshot_with_exact_pf_binding(self) -> None:
        questions = self.load_questions()
        self.assertEqual(len(questions["questions"]), 67)
        canonical = {row["question_id"]: row["pf_id"] for row in questions["questions"]}
        for row in self.load_v02()["meanings"]:
            self.assertIn(row["question_id"], canonical)
            self.assertEqual(row["pf_id"], canonical[row["question_id"]])

    def test_t18_pf7_neighbors_are_explicitly_disambiguated(self) -> None:
        rows = {row["question_id"]: row for row in self.load_v02()["meanings"]}
        self.assertIn("nutzung", rows["7.1"]["positive_scope"].lower())
        self.assertTrue("nutzungszeit" in rows["7.2"]["positive_scope"].lower() or "betriebszeit" in rows["7.2"]["positive_scope"].lower())
        self.assertTrue("zugang" in rows["7.3"]["positive_scope"].lower() or "barriere" in rows["7.3"]["positive_scope"].lower())
        self.assertIn("7.1", rows["7.2"]["disambiguation_notes"])
        self.assertIn("4.1", rows["7.3"]["disambiguation_notes"])

    def test_t19_pf3_neighbors_are_explicitly_disambiguated(self) -> None:
        rows = {row["question_id"]: row for row in self.load_v02()["meanings"]}
        self.assertIn("vorlieg", rows["3.2"]["positive_scope"].lower())
        self.assertTrue("aussteh" in rows["3.3"]["positive_scope"].lower() or "nicht getroffen" in rows["3.3"]["positive_scope"].lower())
        self.assertTrue("frist" in rows["3.4"]["positive_scope"].lower() or "termin" in rows["3.4"]["positive_scope"].lower())
        self.assertTrue("vorläufig" in rows["3.5"]["positive_scope"].lower() or "überholt" in rows["3.5"]["positive_scope"].lower())

    def test_t20_112_and_116_separate_evidence_gap_from_visible_uncertainty(self) -> None:
        rows = {row["question_id"]: row for row in self.load_v02()["meanings"]}
        self.assertIn("unbelegt", rows["11.2"]["positive_scope"].lower())
        self.assertIn("unsicherheit", rows["11.6"]["positive_scope"].lower())
        self.assertIn("11.2", rows["11.6"]["disambiguation_notes"])

    def test_t21_41_and_42_separate_document_existence_from_version_status(self) -> None:
        rows = {row["question_id"]: row for row in self.load_v02()["meanings"]}
        self.assertIn("unterlag", rows["4.1"]["positive_scope"].lower())
        self.assertTrue("version" in rows["4.2"]["positive_scope"].lower() or "status" in rows["4.2"]["positive_scope"].lower())
        self.assertIn("entscheidung", rows["4.2"]["negative_scope"].lower())

    def test_t22_prompt_and_runner_explicitly_version_v02_meaning_layer(self) -> None:
        self.assertTrue(PROMPT_V04.exists(), "new prompt version must be additive")
        self.assertTrue(RUNNER_V06.exists(), "new runner version must be additive")
        prompt = PROMPT_V04.read_text(encoding="utf-8")
        runner = RUNNER_V06.read_text(encoding="utf-8")
        self.assertIn("reference_question_meanings_v0_2.json", prompt)
        self.assertIn("reference_question_meanings_v0_2.json", runner)
        self.assertIn("zs_ki_b_sem_qualifikation_system_v0_4", runner)

    def test_t24_standalone_dry_run_reports_v02_meaning_layer(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER_V06), "--model", "qwen3-14b"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["manifest"]["observed_model_request_count"], 0)
        self.assertFalse(payload["manifest"]["execution_attempted"])
        self.assertEqual(
            payload["manifest"]["meaning_layer"],
            "reference_question_meanings_v0_2.json/R16-R18-R21-R22-neighbor-limited",
        )


if __name__ == "__main__":
    unittest.main()
