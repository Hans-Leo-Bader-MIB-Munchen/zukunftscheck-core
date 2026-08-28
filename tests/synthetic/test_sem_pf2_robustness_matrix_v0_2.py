from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX_V01 = ROOT / "tests/fixtures/zs_ki_b_sem_pf2_robustness_matrix_v0_1.json"
MATRIX_V02 = ROOT / "tests/fixtures/zs_ki_b_sem_pf2_robustness_matrix_v0_2.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemPF2RobustnessMatrixV02(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v01 = load(MATRIX_V01)
        cls.v02 = load(MATRIX_V02)
        cls.cases01 = {row["case_id"]: row for row in cls.v01["cases"]}
        cls.cases02 = {row["case_id"]: row for row in cls.v02["cases"]}

    def test_r01_v02_is_model_free_and_changes_no_frozen_assets(self) -> None:
        self.assertEqual(self.v02["status"], "MODEL_FREE_TESTDESIGN_REVIEWED")
        self.assertFalse(self.v02["frozen_assets_changed"])
        self.assertFalse(self.v02["model_execution_authorized"])
        self.assertEqual(len(self.v02["cases"]), 6)

    def test_r02_only_rm05_classification_changes_from_v01(self) -> None:
        for case_id in self.cases01:
            if case_id == "PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION":
                continue
            self.assertEqual(self.cases01[case_id], self.cases02[case_id])

    def test_r03_rm05_requires_21_and_24(self) -> None:
        case = self.cases02["PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION"]
        self.assertIn(["2.1", "PF2"], case["required_assignments"])
        self.assertIn(["2.4", "PF2"], case["required_assignments"])

    def test_r04_rm05_forbids_22(self) -> None:
        case = self.cases02["PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION"]
        self.assertIn(["2.2", "PF2"], case["forbidden_assignments"])

    def test_r05_rm05_has_no_optional_assignments(self) -> None:
        case = self.cases02["PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION"]
        self.assertEqual(case["optional_assignments"], [])

    def test_r06_frozen_phrase_classification_remains_unchanged(self) -> None:
        case = self.cases02["PF2-RM-04-EXCLUSIVE-PLUS-INCLUSION"]
        self.assertIn(["2.1", "PF2"], case["required_assignments"])
        self.assertIn(["2.2", "PF2"], case["required_assignments"])
        self.assertIn(["2.4", "PF2"], case["optional_assignments"])

    def test_r07_no_model_run_or_frozen_change_is_authorized(self) -> None:
        self.assertFalse(self.v02["model_execution_authorized"])
        self.assertFalse(self.v02["frozen_assets_changed"])


if __name__ == "__main__":
    unittest.main()
