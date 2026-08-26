from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v0_1 as base
import scripts.zs_ki_b_sem_qualifikation_runner_v0_3 as runner
from llm.local_model.structured_output_v0_3 import chat_completion_structured


class SemQualifikationRunnerV03Tests(unittest.TestCase):
    def test_01_runner_freezes_prompt_v0_2_and_new_run_identity(self) -> None:
        self.assertEqual(runner.PROMPT_VERSION, "zs_ki_b_sem_qualifikation_system_v0_2")
        self.assertEqual(runner.PROMPT_SHA256, "9280e064c2504677f1e7e9e408990532046aaed087caf41a241a718a89d85b40")
        self.assertEqual(runner.RUN_TYPE, "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-ONE-RUN-2026-003")
        self.assertEqual(runner.RUNNER_VERSION, "v0.3")

    def test_02_runner_binds_only_new_transport(self) -> None:
        runner.configure_base()
        self.assertIs(base.chat_completion_structured, chat_completion_structured)
        self.assertEqual(base.PROMPT_VERSION, runner.PROMPT_VERSION)
        self.assertEqual(base.PROMPT_SHA256, runner.PROMPT_SHA256)
        self.assertEqual(base.RUN_TYPE, runner.RUN_TYPE)
        self.assertEqual(base.RUNNER_VERSION, runner.RUNNER_VERSION)


if __name__ == "__main__":
    unittest.main()
