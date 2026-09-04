import ast
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts/zs_ki_b_sem_ai_assisted_development_runner_candidate_v0_1.py"
MANIFEST_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_manifest_candidate_v0_1.json"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("dev_runner_candidate_v0_1", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSemAiAssistedDevelopmentRunnerCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner_module()
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_runner_is_prep_only(self):
        self.assertEqual(self.runner.MODE, "DEVELOPMENT_PREP_ONLY")
        self.assertEqual(self.runner.RUNNER_VERSION, "v0.1-prep-only")

    def test_manifest_validation_passes_on_bound_candidate(self):
        self.runner.validate_manifest_fail_closed(self.manifest)

    def test_bound_blob_validation_passes(self):
        self.runner.validate_bound_blobs(self.manifest)

    def test_prep_report_has_zero_model_requests_and_no_authorization(self):
        report = self.runner.build_prep_report(self.manifest)
        self.assertEqual(report["status"], "PREP_VALIDATED_NO_EXECUTION")
        self.assertEqual(report["model_request_count"], 0)
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["preflight_authorized"])
        self.assertFalse(report["qualification_claim_allowed"])

    def test_no_network_or_model_runtime_imports(self):
        tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
        forbidden_roots = {"requests", "httpx", "urllib", "socket", "openai", "subprocess", "os"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported.isdisjoint(forbidden_roots), f"forbidden runtime import(s): {sorted(imported & forbidden_roots)}")

    def test_no_execution_function_names_or_dynamic_calls(self):
        tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
        forbidden_names = {"run_model", "execute_model", "call_model", "preflight_model", "send_request"}
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(function_names.isdisjoint(forbidden_names), f"forbidden execution function(s): {sorted(function_names & forbidden_names)}")
        forbidden_calls = {"eval", "exec", "__import__", "system", "popen", "run", "call", "check_call", "check_output"}
        call_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    call_names.add(func.id)
                elif isinstance(func, ast.Attribute):
                    call_names.add(func.attr)
        self.assertTrue(call_names.isdisjoint(forbidden_calls), f"forbidden dynamic/shell call(s): {sorted(call_names & forbidden_calls)}")


if __name__ == "__main__":
    unittest.main()
