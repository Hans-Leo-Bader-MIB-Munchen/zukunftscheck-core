from __future__ import annotations

import ast
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v1_9_readiness_prep as prep


class V19ExecutionReadinessPrepTests(unittest.TestCase):
    def test_e01_readiness_report_passes_model_free(self) -> None:
        report = prep.build_readiness_report()
        self.assertEqual(report["mode"], "MODEL_FREE_EXECUTION_READINESS_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["technical_binding_ready_for_future_authorization_design"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertTrue(report["new_explicit_single_use_model_contact_authorization_required"])
        self.assertFalse(report["model_qualified"])

    def test_e02_all_readiness_checks_are_true(self) -> None:
        report = prep.build_readiness_report()
        self.assertTrue(report["checks"])
        self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_e03_exact_runtime_and_artifact_binding(self) -> None:
        checks = prep.build_readiness_report()["checks"]
        self.assertTrue(checks["runtime_model_id_exact"])
        self.assertTrue(checks["model_repository_exact"])
        self.assertTrue(checks["prompt_exact"])
        self.assertTrue(checks["contract_exact"])
        self.assertTrue(checks["output_mode_exact"])

    def test_e04_full_context_is_preserved(self) -> None:
        checks = prep.build_readiness_report()["checks"]
        self.assertTrue(checks["full_reference_questions"])
        self.assertTrue(checks["full_meaning_layer"])
        self.assertTrue(checks["no_context_reduction"])
        self.assertTrue(checks["no_pf_prefiltering"])

    def test_e05_request_bounds_are_exact(self) -> None:
        checks = prep.build_readiness_report()["checks"]
        self.assertTrue(checks["max_tokens_exact"])
        self.assertTrue(checks["no_max_completion_tokens"])
        self.assertTrue(checks["stream_false"])
        self.assertTrue(checks["strict_json_schema"])
        self.assertTrue(checks["timeout_design_exact"])

    def test_e06_execution_policy_is_closed(self) -> None:
        checks = prep.build_readiness_report()["checks"]
        self.assertTrue(checks["retry_zero"])
        self.assertTrue(checks["output_repair_false"])
        self.assertTrue(checks["remote_cloud_false"])
        self.assertTrue(checks["real_data_false"])
        self.assertTrue(checks["loopback_base_url_exact"])
        self.assertTrue(checks["execution_not_authorized"])
        self.assertTrue(checks["model_run_not_authorized"])
        self.assertTrue(checks["model_contact_not_authorized"])
        self.assertTrue(checks["model_contact_not_performed"])
        self.assertTrue(checks["authorization_path_absent"])
        self.assertTrue(checks["model_not_qualified"])

    def test_e07_no_network_or_execution_imports(self) -> None:
        source = Path(prep.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden = ("urllib", "requests", "httpx", "socket", "subprocess")
        for name in imported:
            self.assertFalse(name.startswith(forbidden), name)

    def test_e08_execution_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()


if __name__ == "__main__":
    unittest.main()
