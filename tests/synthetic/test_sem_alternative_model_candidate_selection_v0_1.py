from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_alternative_model_candidate_selection_v0_1.json"


class TestSemAlternativeModelCandidateSelectionV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))

    def test_s01_selected_candidate_is_ministral_14b(self) -> None:
        self.assertEqual(
            self.selection["selected_candidate"],
            "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        )

    def test_s02_context_exceeds_project_minimum(self) -> None:
        self.assertGreaterEqual(
            self.selection["documented_context_length"],
            self.selection["required_project_context_length"],
        )

    def test_s03_candidate_is_local_structured_and_multilingual(self) -> None:
        self.assertTrue(self.selection["gguf_available"])
        self.assertTrue(self.selection["lm_studio_compatible_distribution_available"])
        self.assertTrue(self.selection["multilingual_german_documented"])
        self.assertTrue(self.selection["structured_json_output_documented"])

    def test_s04_no_execution_or_model_contact_is_authorized(self) -> None:
        self.assertFalse(self.selection["download_authorized"])
        self.assertFalse(self.selection["model_load_authorized"])
        self.assertFalse(self.selection["model_contact_authorized"])
        self.assertFalse(self.selection["execution_authorized"])
        self.assertFalse(self.selection["qualification_run_authorized"])

    def test_s05_model_remains_not_qualified(self) -> None:
        self.assertFalse(self.selection["model_qualified"])
        self.assertFalse(self.selection["frozen_assets_changed"])

    def test_s06_phi4_is_excluded_for_context(self) -> None:
        excluded = {row["model"]: row["reason"] for row in self.selection["excluded_candidates"]}
        self.assertIn("microsoft/phi-4", excluded)
        self.assertIn("16k", excluded["microsoft/phi-4"])
        self.assertIn("32768", excluded["microsoft/phi-4"])

    def test_s07_next_gate_is_model_free_readiness_plan(self) -> None:
        self.assertEqual(
            self.selection["next_gate"],
            "MODEL_FREE_CANDIDATE_READINESS_PREFLIGHT_PLAN",
        )


if __name__ == "__main__":
    unittest.main()
