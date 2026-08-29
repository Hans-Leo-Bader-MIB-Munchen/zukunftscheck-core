from __future__ import annotations

import ast
import unittest
from pathlib import Path

from llm.local_model import structured_output_v0_7_candidate as bounded
import scripts.zs_ki_b_sem_qualifikation_runner_v1_8_prep as prep


class V18LmStudioTokenCapCompatPrepTests(unittest.TestCase):
    def test_d01_manifest_is_closed_and_model_free(self) -> None:
        payload = prep.build_dry_run_manifest()
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_8_LMSTUDIO_TOKEN_CAP_PREP")
        manifest = payload["manifest"]
        self.assertEqual(manifest["runner_version"], "v1.8-prep")
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertFalse(manifest["model_qualified"])
        self.assertIsNone(manifest["authorization_path"])

    def test_d02_payload_uses_lmstudio_documented_max_tokens(self) -> None:
        request = prep.build_candidate_request_preview()
        self.assertEqual(request["max_tokens"], 1024)
        self.assertNotIn("max_completion_tokens", request)
        self.assertFalse(request["stream"])

    def test_d03_manifest_records_exact_token_parameter(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        self.assertEqual(manifest["output_token_parameter"], "max_tokens")
        self.assertEqual(manifest["max_tokens"], 1024)
        self.assertIsNone(manifest["max_completion_tokens"])
        self.assertTrue(manifest["lmstudio_documented_chat_completion_parameter_binding_prepared"])

    def test_d04_candidate_schema_and_prompt_are_preserved(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        self.assertEqual(manifest["contract_version"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate")
        self.assertEqual(manifest["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_7_candidate")
        self.assertEqual(manifest["full_reference_question_count"], 67)
        self.assertEqual(manifest["full_meaning_count"], 67)
        self.assertFalse(manifest["context_reduction_performed"])
        self.assertFalse(manifest["pf_prefiltering_performed"])

    def test_d05_output_mode_is_new_candidate_version(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        self.assertEqual(manifest["candidate_output_mode_version"], "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.7-candidate")
        self.assertEqual(manifest["response_format_sha256"], manifest["candidate_response_format_sha256"])

    def test_d06_builder_rejects_invalid_caps(self) -> None:
        messages = prep.build_candidate_messages()
        with self.assertRaises(ValueError):
            bounded.build_structured_payload(model=prep.RUNTIME_MODEL_ID, messages=messages, max_tokens=0)
        with self.assertRaises(ValueError):
            bounded.build_structured_payload(model=prep.RUNTIME_MODEL_ID, messages=messages, max_tokens=1025)
        with self.assertRaises(ValueError):
            bounded.build_structured_payload(model=prep.RUNTIME_MODEL_ID, messages=messages, max_tokens=True)

    def test_d07_no_network_or_execution_imports(self) -> None:
        for module in (bounded, prep):
            source = Path(module.__file__).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            forbidden = ("urllib", "requests", "httpx", "socket", "subprocess")
            for name in imported:
                self.assertFalse(name.startswith(forbidden), f"{module.__name__}: {name}")

    def test_d08_execution_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()


if __name__ == "__main__":
    unittest.main()
