from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_pf2_robustness_matrix_v0_1.json"
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"
CROSS_MODEL_REVIEW_PATH = ROOT / "docs/requirements/ZS-DEV-KI-B-SEM-PF2-CROSS-MODEL-GEGENCHECK-2026-001_v0.1.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemPF2RobustnessMatrixV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = load(MATRIX_PATH)
        cls.cases = {row["case_id"]: row for row in cls.matrix["cases"]}
        cls.prompt = PROMPT_PATH.read_text(encoding="utf-8")
        cls.review = CROSS_MODEL_REVIEW_PATH.read_text(encoding="utf-8")

    def test_r01_matrix_is_model_free_and_does_not_change_frozen_assets(self) -> None:
        self.assertEqual(self.matrix["status"], "MODEL_FREE_TESTDESIGN")
        self.assertFalse(self.matrix["frozen_assets_changed"])
        self.assertFalse(self.matrix["model_execution_authorized"])
        self.assertEqual(len(self.matrix["cases"]), 6)

    def test_r02_object_only_requires_21_and_forbids_22(self) -> None:
        case = self.cases["PF2-RM-01-OBJECT-ONLY"]
        self.assertIn(["2.1", "PF2"], case["required_assignments"])
        self.assertIn(["2.2", "PF2"], case["forbidden_assignments"])

    def test_r03_explicit_inclusion_and_exclusion_require_22(self) -> None:
        for case_id in ("PF2-RM-02-EXPLICIT-INCLUSION", "PF2-RM-03-EXPLICIT-EXCLUSION"):
            case = self.cases[case_id]
            self.assertIn(["2.2", "PF2"], case["required_assignments"])

    def test_r04_frozen_phrase_requires_21_and_22_with_24_optional(self) -> None:
        case = self.cases["PF2-RM-04-EXCLUSIVE-PLUS-INCLUSION"]
        self.assertIn(["2.1", "PF2"], case["required_assignments"])
        self.assertIn(["2.2", "PF2"], case["required_assignments"])
        self.assertIn(["2.4", "PF2"], case["optional_assignments"])

    def test_r05_spatial_boundary_discriminates_24_from_22(self) -> None:
        case = self.cases["PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION"]
        self.assertIn(["2.4", "PF2"], case["required_assignments"])
        self.assertIn(["2.2", "PF2"], case["forbidden_assignments"])

    def test_r06_nonspatial_inclusion_discriminates_22_from_24(self) -> None:
        case = self.cases["PF2-RM-06-INCLUSION-NONSPATIAL"]
        self.assertIn(["2.2", "PF2"], case["required_assignments"])
        self.assertIn(["2.4", "PF2"], case["forbidden_assignments"])

    def test_r07_prompt_and_prior_review_already_cover_scope_markers(self) -> None:
        self.assertIn("ausschließlich", self.prompt)
        self.assertIn("einschließlich", self.prompt)
        self.assertIn("GOLD_CONFIRMED", self.review)
        self.assertIn("keinen konkreten Beleg dafür, dass ein weiterer Prompt-Hinweis erforderlich wäre", self.review)


if __name__ == "__main__":
    unittest.main()
