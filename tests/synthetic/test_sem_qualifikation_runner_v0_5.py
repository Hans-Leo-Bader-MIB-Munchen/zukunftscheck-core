from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_5.py"


def load_runner():
    if not RUNNER.exists():
        raise AssertionError(f"missing implementation artifact: {RUNNER.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("sem_runner_v0_5", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SemQualificationRunnerV05Tests(unittest.TestCase):
    def test_t5_runner_binds_v02_contract_v03_prompt_and_v01_meaning_layer(self) -> None:
        runner = load_runner()
        self.assertEqual(runner.CONTRACT_VERSION, "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")
        self.assertEqual(runner.PROMPT_VERSION, "zs_ki_b_sem_qualifikation_system_v0_3")
        self.assertEqual(runner.RUNNER_VERSION, "v0.5")
        self.assertTrue(str(runner.MEANINGS_PATH).endswith("reference_question_meanings_v0_1.json"))

    def test_t5_runner_keeps_top_level_target_match(self) -> None:
        runner = load_runner()
        self.assertTrue(hasattr(runner, "evaluate_boundary"), "runner v0.5 should expose deterministic boundary evaluation")
        case = {
            "target_source_location_id": "SL-TARGET",
            "source_locations": [{"source_location_id": "SL-TARGET"}, {"source_location_id": "SL-OTHER"}],
        }
        response = {
            "contract_version": runner.CONTRACT_VERSION,
            "source_location_id": "SL-OTHER",
            "proposals": [],
        }
        evaluation = runner.evaluate_boundary(case, response)
        self.assertFalse(evaluation["target_source_match"])
        self.assertFalse(evaluation["passed"])

    def test_t10_dry_run_makes_no_model_contact(self) -> None:
        runner = load_runner()
        with patch.object(runner, "current_git_commit", return_value="a" * 40), patch.object(
            runner, "chat_completion_structured"
        ) as call:
            result = runner.build_dry_run_manifest(model="")
        call.assert_not_called()
        self.assertEqual(result["mode"], "DRY_RUN_SEM_QUALIFICATION_V0_2")
        self.assertFalse(result["manifest"]["execution_attempted"])

    def test_t13_runner_v05_is_additive_and_does_not_replace_old_runners(self) -> None:
        for version in ("v0_1", "v0_2", "v0_3", "v0_4"):
            self.assertTrue((ROOT / f"scripts/zs_ki_b_sem_qualifikation_runner_{version}.py").exists())
        self.assertTrue(RUNNER.exists())


if __name__ == "__main__":
    unittest.main()
