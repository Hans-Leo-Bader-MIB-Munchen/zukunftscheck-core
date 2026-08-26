from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v0_1 as runner

TEST_GIT_COMMIT = "dab7b8926a7cc7e035c65936704da22c829d99b7"


def valid_response(source_location_id: str) -> str:
    return json.dumps(
        {
            "contract_version": runner.CONTRACT_VERSION,
            "source_location_id": source_location_id,
            "proposals": [
                {
                    "proposal_id": f"P-{source_location_id}",
                    "normalized_statement": "Synthetischer Testvorschlag ohne Goldbewertung.",
                    "finding_type_candidate": "DT",
                    "evidence_relation_type_candidate": "DIRECT",
                    "assignment_candidates": [],
                    "conflict_candidate_refs": [],
                    "gap_notes": [],
                    "uncertainty_notes": [],
                    "human_review_required": False,
                }
            ],
        },
        ensure_ascii=False,
    )


class SemQualificationRunnerTests(unittest.TestCase):
    def test_01_frozen_prompt_hash_matches(self) -> None:
        text = runner.PROMPT_PATH.read_text(encoding="utf-8")
        self.assertEqual(runner.sha256_text(text), runner.PROMPT_SHA256)

    def test_02_frozen_case_set_and_hashes_match(self) -> None:
        cases = [runner.load(path) for path in runner.CASE_PATHS]
        runner.validate_frozen_cases(cases)
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(case["data_class"] == "SYNTHETIC_ONLY" for case in cases))

    def test_03_dry_run_has_no_model_contact_and_full_manifest(self) -> None:
        argv = ["zs_ki_b_sem_qualifikation_runner_v0_1.py"]
        with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
            runner, "chat_completion_structured"
        ) as call, patch.object(sys, "argv", argv):
            exit_code = runner.main()
        self.assertEqual(exit_code, 0)
        call.assert_not_called()

    def test_04_execute_calls_exactly_four_times_and_persists_raw_outputs(self) -> None:
        cases = [runner.load(path) for path in runner.CASE_PATHS]
        side_effect = [
            (valid_response(case["target_source_location_id"]), {"id": f"env-{idx}", "model": "synthetic-model", "created": 0, "usage": {}})
            for idx, case in enumerate(cases, start=1)
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.json"
            argv = [
                "zs_ki_b_sem_qualifikation_runner_v0_1.py",
                "--execute",
                "--model",
                "synthetic-model",
                "--output",
                str(output),
            ]
            with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
                runner, "chat_completion_structured", side_effect=side_effect
            ) as call, patch.object(sys, "argv", argv):
                exit_code = runner.main()
            persisted = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(call.call_count, 4)
        self.assertEqual(persisted["manifest"]["expected_run_count"], 1)
        self.assertEqual(persisted["manifest"]["observed_run_count"], 1)
        self.assertEqual(persisted["manifest"]["retry_count"], 0)
        self.assertFalse(persisted["manifest"]["output_repair"])
        self.assertEqual(persisted["manifest"]["observed_model_request_count"], 4)
        self.assertTrue(persisted["technical_boundary_pass"])
        self.assertEqual(persisted["human_gold_evaluation"], "PENDING_HUMAN_REVIEW")
        self.assertTrue(all(item["model_response_raw"] for item in persisted["cases"]))

    def test_05_boundary_failure_aborts_remaining_requests(self) -> None:
        cases = [runner.load(path) for path in runner.CASE_PATHS]
        invalid = json.dumps(
            {
                "contract_version": runner.CONTRACT_VERSION,
                "source_location_id": cases[0]["target_source_location_id"],
                "proposals": [],
                "governance_approval": True,
            }
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.json"
            argv = [
                "zs_ki_b_sem_qualifikation_runner_v0_1.py",
                "--execute",
                "--model",
                "synthetic-model",
                "--output",
                str(output),
            ]
            with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
                runner,
                "chat_completion_structured",
                return_value=(invalid, {"id": "env-1", "model": "synthetic-model", "created": 0, "usage": {}}),
            ) as call, patch.object(sys, "argv", argv):
                exit_code = runner.main()
            persisted = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(persisted["manifest"]["observed_model_request_count"], 1)
        self.assertFalse(persisted["cases"][0]["boundary_evaluation"]["passed"])


if __name__ == "__main__":
    unittest.main()
