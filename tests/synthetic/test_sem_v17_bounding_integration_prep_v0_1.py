from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v1_7_prep as prep


class V17BoundingIntegrationPrepTests(unittest.TestCase):
    def test_c01_manifest_is_closed_and_model_free(self) -> None:
        payload = prep.build_dry_run_manifest()
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_7_BOUNDING_PREP")
        manifest = payload["manifest"]
        self.assertEqual(manifest["runner_version"], "v1.7-prep")
        self.assertTrue(manifest["bounded_request_integration_prepared"])
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertFalse(manifest["model_qualified"])
        self.assertIsNone(manifest["authorization_path"])

    def test_c02_candidate_binding_is_exact(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        expected_contract = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate"
        self.assertEqual(manifest["contract_version"], expected_contract)
        self.assertEqual(manifest["candidate_contract_version"], expected_contract)
        self.assertEqual(
            manifest["candidate_output_mode_version"],
            "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.6-candidate",
        )
        self.assertEqual(manifest["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_7_candidate")
        prompt_text = prep.PROMPT_PATH.read_text(encoding="utf-8")
        expected_prompt_sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        self.assertEqual(manifest["prompt_sha256"], expected_prompt_sha)
        self.assertEqual(len(manifest["prompt_sha256"]), 64)
        self.assertEqual(manifest["max_completion_tokens"], 1024)
        self.assertEqual(manifest["request_timeout_seconds"], 1800.0)
        self.assertEqual(manifest["response_format_sha256"], manifest["candidate_response_format_sha256"])
        self.assertEqual(len(manifest["candidate_response_format_sha256"]), 64)

    def test_c03_preview_is_bounded_but_not_transmitted(self) -> None:
        request = prep.build_candidate_request_preview()
        self.assertEqual(request["model"], prep.RUNTIME_MODEL_ID)
        self.assertEqual(request["max_completion_tokens"], 1024)
        self.assertFalse(request["stream"])
        response_format = request["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertTrue(response_format["json_schema"]["strict"])
        schema = response_format["json_schema"]["schema"]
        self.assertEqual(schema["properties"]["proposals"]["maxItems"], 8)

    def test_c04_full_semantic_context_is_preserved(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        self.assertEqual(manifest["full_reference_question_count"], 67)
        self.assertEqual(manifest["full_meaning_count"], 67)
        self.assertFalse(manifest["context_reduction_performed"])
        self.assertFalse(manifest["pf_prefiltering_performed"])

    def test_c05_active_contract_remains_distinct_and_unchanged(self) -> None:
        manifest = prep.build_dry_run_manifest()["manifest"]
        self.assertEqual(
            manifest["active_contract_version_unchanged"],
            "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        )
        self.assertNotEqual(manifest["active_contract_version_unchanged"], manifest["contract_version"])
        self.assertNotEqual(manifest["active_contract_version_unchanged"], manifest["candidate_contract_version"])

    def test_c06_candidate_prompt_binds_candidate_contract(self) -> None:
        messages = prep.build_candidate_messages()
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate", messages[0]["content"])
        user_payload = json.loads(messages[1]["content"])
        self.assertEqual(len(user_payload["reference_questions"]), 67)
        self.assertEqual(len(user_payload["reference_question_meanings"]["meanings"]), 67)

    def test_c07_no_network_or_execution_imports(self) -> None:
        source = Path(prep.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden_prefixes = (
            "urllib",
            "requests",
            "httpx",
            "socket",
            "subprocess",
            "llm.local_model.openai_compatible",
        )
        for name in imported:
            self.assertFalse(name.startswith(forbidden_prefixes), name)

    def test_c08_execution_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()


if __name__ == "__main__":
    unittest.main()
