from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "tests/fixtures/zs_ki_b_sem_multi_assignment_robustness_pf2_architecture_v0_1.json"
BOUNDARY = ROOT / "core/validation/semantic_boundary_v0_2.py"
PROMPT = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"


class SemMultiAssignmentRobustnessPF2ArchitectureTests(unittest.TestCase):
    def test_a01_architecture_decision_is_model_free_and_non_authorizing(self) -> None:
        data = json.loads(ARCH.read_text(encoding="utf-8"))
        self.assertEqual(data["diagnosis"], "SEMANTIC_COMPLETENESS_AUDIT_REQUIRED")
        self.assertFalse(data["frozen_assets_changed"])
        self.assertFalse(data["model_run_authorized"])
        self.assertFalse(data["real_data_authorized"])
        self.assertFalse(data["pilot_authorized"])
        self.assertFalse(data["production_authorized"])
        self.assertFalse(data["phase_f_authorized"])

    def test_a02_audit_may_flag_but_must_not_auto_assign(self) -> None:
        data = json.loads(ARCH.read_text(encoding="utf-8"))
        self.assertIn("flag_possible_multi_assignment_omission", data["audit_effects_allowed"])
        self.assertIn("require_human_review", data["audit_effects_allowed"])
        self.assertIn("auto_add_assignment", data["audit_effects_forbidden"])
        self.assertIn("reconstruct_human_gold", data["audit_effects_forbidden"])
        self.assertIn("change_model_output_silently", data["audit_effects_forbidden"])

    def test_a03_prompt_already_contains_pf2_scope_markers(self) -> None:
        text = PROMPT.read_text(encoding="utf-8")
        self.assertIn("ausschließlich", text)
        self.assertIn("einschließlich", text)
        self.assertIn("ausgenommen", text)
        self.assertIn("alle Referenzfragen", text)

    def test_a04_existing_boundary_is_formal_not_completeness_inference(self) -> None:
        text = BOUNDARY.read_text(encoding="utf-8")
        self.assertIn("formal invariants without semantic inference", text)
        self.assertNotIn("possible_multi_assignment_omission", text)

    def test_a05_prototype_scope_remains_narrow(self) -> None:
        data = json.loads(ARCH.read_text(encoding="utf-8"))
        self.assertEqual(data["prototype_scope"], "PF2 explicit inclusion/exclusion markers only")
        self.assertEqual(data["prototype_markers"], ["ausschließlich", "einschließlich", "ausgenommen"])


if __name__ == "__main__":
    unittest.main()
