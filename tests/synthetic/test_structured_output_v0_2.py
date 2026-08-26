from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llm.local_model.structured_output_v0_2 import (
    OUTPUT_MODE_VERSION,
    build_response_format,
    build_structured_payload,
)
from llm.smoketest import parse_model_json
import scripts.zs_ki_b_smoketest_v0_2 as runner
from tests.synthetic.test_local_smoketest_harness import valid_model_response

ROOT = Path(__file__).resolve().parents[2]
TEST_GIT_COMMIT = "e4ef33bc0259d6ad1fb3e5f61871158478c2df1a"


class StructuredOutputV02Tests(unittest.TestCase):
    def test_01_response_format_is_strict_json_schema(self) -> None:
        response_format = build_response_format()
        self.assertEqual(response_format["type"], "json_schema")
        self.assertIs(response_format["json_schema"]["strict"], True)
        self.assertEqual(response_format["json_schema"]["name"], "zs_ki_b_semantic_response_v0_1")

    def test_02_transport_schema_preserves_frozen_contract(self) -> None:
        response_format = build_response_format()
        schema = response_format["json_schema"]["schema"]
        self.assertEqual(schema["properties"]["contract_version"]["const"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1")
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("proposal", schema["$defs"])
        self.assertIn("assignment_candidate", schema["$defs"])

    def test_03_transport_removes_annotations_not_constraints(self) -> None:
        schema = build_response_format()["json_schema"]["schema"]
        self.assertNotIn("$schema", schema)
        self.assertNotIn("$id", schema)
        self.assertNotIn("title", schema)
        self.assertNotIn("description", schema)
        self.assertIn("required", schema)
        self.assertIn("properties", schema)

    def test_04_payload_contains_response_format_and_no_tools(self) -> None:
        payload = build_structured_payload(
            model="synthetic-model",
            messages=[{"role": "user", "content": "synthetic"}],
        )
        self.assertIn("response_format", payload)
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["temperature"], 0.0)

    def test_05_strict_parser_remains_unchanged_and_rejects_fences(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_model_json('```json\n{"a":1}\n```')

    def test_06_output_mode_is_explicitly_versioned(self) -> None:
        self.assertEqual(OUTPUT_MODE_VERSION, "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.2")

    def test_07_dry_run_performs_no_model_contact(self) -> None:
        argv = ["zs_ki_b_smoketest_v0_2.py"]
        with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
            runner, "chat_completion_structured"
        ) as call, patch.object(sys, "argv", argv):
            exit_code = runner.main()
        self.assertEqual(exit_code, 0)
        call.assert_not_called()

    def test_08_execute_calls_model_exactly_once_and_persists_mode(self) -> None:
        content = json.dumps(valid_model_response(), ensure_ascii=False)
        envelope = {"id": "synthetic-envelope", "model": "synthetic-model", "created": 0, "usage": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.json"
            argv = [
                "zs_ki_b_smoketest_v0_2.py",
                "--execute",
                "--model",
                "synthetic-model",
                "--output",
                str(output),
            ]
            with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
                runner,
                "chat_completion_structured",
                return_value=(content, envelope),
            ) as call, patch.object(sys, "argv", argv):
                exit_code = runner.main()
            persisted = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        call.assert_called_once()
        self.assertEqual(persisted["mode"], "EXECUTED_ONCE_STRUCTURED_V0_2")
        self.assertEqual(persisted["manifest"]["retry_count"], 0)
        self.assertFalse(persisted["manifest"]["output_repair"])
        self.assertEqual(persisted["manifest"]["git_commit"], TEST_GIT_COMMIT)
        self.assertTrue(persisted["evaluation"]["passed"])

    def test_09_non_synthetic_case_fails_before_model_contact(self) -> None:
        argv = [
            "zs_ki_b_smoketest_v0_2.py",
            "--execute",
            "--model",
            "synthetic-model",
        ]
        with patch.object(runner, "load", return_value={"data_class": "REAL_DATA"}), patch.object(
            runner, "chat_completion_structured"
        ) as call, patch.object(sys, "argv", argv):
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_ONLY"):
                runner.main()
        call.assert_not_called()

    def test_10_connection_refused_persists_controlled_failure(self) -> None:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output = Path(tmpdir) / "result.json"
                argv = [
                    "zs_ki_b_smoketest_v0_2.py",
                    "--execute",
                    "--model",
                    "synthetic-model",
                    "--base-url",
                    f"http://127.0.0.1:{port}/v1",
                    "--output",
                    str(output),
                ]
                with patch.object(runner, "current_git_commit", return_value=TEST_GIT_COMMIT), patch.object(
                    sys, "argv", argv
                ):
                    exit_code = runner.main()
                persisted = json.loads(output.read_text(encoding="utf-8"))
        finally:
            probe.close()

        self.assertEqual(exit_code, 2)
        self.assertEqual(persisted["mode"], "EXECUTED_ONCE_FAILED_STRUCTURED_V0_2")
        self.assertFalse(persisted["manifest"]["executed"])
        self.assertTrue(persisted["manifest"]["execution_attempted"])
        self.assertFalse(persisted["evaluation"]["passed"])
        self.assertFalse(persisted["evaluation"]["criteria"]["endpoint_response_pass"])
        self.assertIn("LocalModelError", persisted["evaluation"]["endpoint_error"])

    def test_11_dirty_worktree_fails_before_model_contact(self) -> None:
        argv = [
            "zs_ki_b_smoketest_v0_2.py",
            "--execute",
            "--model",
            "synthetic-model",
        ]
        rev_parse = subprocess.CompletedProcess(
            args=["git", "rev-parse", "HEAD"],
            returncode=0,
            stdout=TEST_GIT_COMMIT + "\n",
            stderr="",
        )
        dirty_status = subprocess.CompletedProcess(
            args=["git", "status", "--porcelain", "--untracked-files=normal"],
            returncode=0,
            stdout=" M scripts/zs_ki_b_smoketest_v0_2.py\n",
            stderr="",
        )
        with patch.object(runner.subprocess, "run", side_effect=[rev_parse, dirty_status]), patch.object(
            runner, "chat_completion_structured"
        ) as call, patch.object(sys, "argv", argv):
            with self.assertRaisesRegex(RuntimeError, "working tree must be clean"):
                runner.main()
        call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
