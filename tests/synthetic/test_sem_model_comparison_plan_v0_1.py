from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "tests/fixtures/zs_ki_b_sem_model_comparison_plan_v0_1.json"
INCIDENT = ROOT / "tests/fixtures/zs_ki_b_sem_v11_execution_failure_gold_pf2_reproduced_v0_1.json"
PROMPT_V06 = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"


class SemModelComparisonPlanV01Tests(unittest.TestCase):
    def load(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_c01_pf2_reproduction_is_recorded(self):
        incident = self.load(INCIDENT)
        self.assertTrue(incident["same_pf2_missing_assignment_reproduced"])
        self.assertEqual(incident["missing_required"], [["2.2", "PF2"]])
        self.assertFalse(incident["model_qualified"])
        self.assertFalse(incident["rerun_authorized"])

    def test_c02_comparison_is_model_free_and_not_authorized(self):
        plan = self.load(PLAN)
        self.assertEqual(plan["status"], "MODEL_FREE_PREPARATION")
        self.assertFalse(plan["execution_authorized"])
        self.assertTrue(plan["per_model_explicit_authorization_required"])
        self.assertFalse(plan["qwen3_14b_rerun_authorized"])

    def test_c03_candidate_models_are_explicit_and_reference_model_is_excluded(self):
        plan = self.load(PLAN)
        self.assertEqual(plan["reference_model"], "qwen3-14b")
        self.assertEqual(plan["candidate_models"], ["gemma-3-12b-it-qat", "qwen/qwen3-8b"])
        self.assertNotIn(plan["reference_model"], plan["candidate_models"])

    def test_c04_prompt_gold_and_case_changes_are_locked_before_comparison(self):
        plan = self.load(PLAN)
        self.assertFalse(plan["prompt_change_allowed_before_comparison"])
        self.assertFalse(plan["gold_change_allowed_before_comparison"])
        self.assertFalse(plan["case_change_allowed_before_comparison"])
        self.assertEqual(plan["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")

    def test_c05_frozen_assets_exist_and_plan_names_them(self):
        plan = self.load(PLAN)
        self.assertTrue(PROMPT_V06.exists())
        self.assertTrue(SUITE.exists())
        self.assertTrue(GOLD.exists())
        self.assertTrue(POLICY.exists())
        self.assertEqual(plan["qualification_suite"], "ZS-KI-B-SEM-V0-7-QUALIFIKATION-SUITE-FROZEN-v0.1")
        self.assertEqual(plan["human_gold"], "ZS-KI-B-SEM-V0-7-HUMAN-GOLD-FROZEN-v0.1")
        self.assertEqual(plan["qualification_policy"], "ZS-KI-B-SEM-V0-7-QUALIFIKATION-POLICY-FROZEN-v0.1")


if __name__ == "__main__":
    unittest.main()
