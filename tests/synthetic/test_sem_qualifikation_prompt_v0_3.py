from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_3.txt"


class SemQualificationPromptV03Tests(unittest.TestCase):
    def prompt_text(self) -> str:
        self.assertTrue(PROMPT.exists(), "v0.3 SEM prompt must exist")
        return PROMPT.read_text(encoding="utf-8")

    def test_t6_temporal_progression_is_not_automatic_conflict(self) -> None:
        text = self.prompt_text().lower()
        self.assertIn("source_location_id", text)
        self.assertIn("zeit", text)
        self.assertIn("fortschreibung", text)
        self.assertTrue(
            "nicht allein" in text and "konflikt" in text,
            "prompt must state that differing temporal values alone do not create a conflict candidate",
        )

    def test_t7_simultaneous_incompatible_states_can_remain_conflict_candidates(self) -> None:
        text = self.prompt_text().lower()
        self.assertIn("konflikt", text)
        self.assertTrue("inkompatibel" in text or "unvereinbar" in text)
        self.assertTrue("gleicher" in text and ("zeitraum" in text or "bezugszeitraum" in text))
        self.assertIn("human_review_required", text)

    def test_t12_partial_overlap_routes_to_uncertainty_and_human_review(self) -> None:
        text = self.prompt_text().lower()
        self.assertTrue("überlapp" in text or "ueberlapp" in text)
        self.assertTrue("unklar" in text or "unsicher" in text)
        self.assertIn("human_review_required", text)
        self.assertFalse(
            "teilweise überlapp" in text and "bestätigter konflikt" in text,
            "partial overlap must not be promoted to a confirmed conflict",
        )


if __name__ == "__main__":
    unittest.main()
