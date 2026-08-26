from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v0_1 as base
import scripts.zs_ki_b_sem_qualifikation_runner_v0_2 as runner


class SemQualificationRunnerV02Tests(unittest.TestCase):
    def test_01_prompt_v0_2_hash_matches(self) -> None:
        text = runner.PROMPT_PATH.read_text(encoding="utf-8")
        self.assertEqual(base.sha256_text(text), runner.PROMPT_SHA256)
        self.assertEqual(runner.PROMPT_VERSION, "zs_ki_b_sem_qualifikation_system_v0_2")

    def test_02_runner_v0_2_binds_only_execution_metadata(self) -> None:
        original = {
            "PROMPT_VERSION": base.PROMPT_VERSION,
            "PROMPT_SHA256": base.PROMPT_SHA256,
            "PROMPT_PATH": base.PROMPT_PATH,
            "RUN_TYPE": base.RUN_TYPE,
            "RUNNER_VERSION": base.RUNNER_VERSION,
            "DEFAULT_OUTPUT": base.DEFAULT_OUTPUT,
        }
        try:
            runner.configure_base()
            self.assertEqual(base.PROMPT_VERSION, runner.PROMPT_VERSION)
            self.assertEqual(base.PROMPT_SHA256, runner.PROMPT_SHA256)
            self.assertEqual(base.PROMPT_PATH, runner.PROMPT_PATH)
            self.assertEqual(base.RUN_TYPE, runner.RUN_TYPE)
            self.assertEqual(base.RUNNER_VERSION, "v0.2")
            self.assertEqual(base.DEFAULT_OUTPUT, "zs_ki_b_sem_qualifikation_result_v0_2.json")
            self.assertEqual(base.EXPECTED_RUN_COUNT, 1)
            self.assertEqual(base.EXPECTED_MODEL_REQUEST_COUNT, 4)
            self.assertEqual(base.CONTRACT_VERSION, "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1")
        finally:
            for name, value in original.items():
                setattr(base, name, value)


if __name__ == "__main__":
    unittest.main()
