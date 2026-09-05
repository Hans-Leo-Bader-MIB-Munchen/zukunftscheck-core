import ast
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts/zs_ki_b_sem_ai_assisted_development_live_runner_candidate_v0_1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("dev_live_runner_v0_1", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSemAiAssistedDevelopmentLiveRunnerCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()

    def test_static_package_and_exact_24_case_order_are_bound(self):
        runtime = self.runner.validate_static_package()
        ids = self.runner.ordered_case_ids()
        self.assertEqual(len(ids), 24)
        self.assertEqual(len(set(ids)), 24)
        self.assertEqual(runtime["runtime_parameters"]["model_id"], "ministral-3-14b-instruct-2512")

    def test_request_contains_full_67_67_semantic_context(self):
        request = self.runner.build_candidate_request(self.runner.ordered_case_ids()[0])
        payload = json.loads(request["messages"][1]["content"])
        self.assertEqual(len(payload["reference_questions"]), 67)
        self.assertEqual(len(payload["reference_question_meanings"]["meanings"]), 67)
        self.assertIn("finding_type_meanings", payload)
        self.assertEqual(len(payload["source_locations"]), 1)

    def test_request_runtime_and_structured_output_are_exact(self):
        request = self.runner.build_candidate_request(self.runner.ordered_case_ids()[0])
        self.assertEqual(request["model"], "ministral-3-14b-instruct-2512")
        self.assertEqual(request["max_tokens"], 2048)
        self.assertEqual(request["temperature"], 0.0)
        self.assertIs(request["stream"], False)
        self.assertNotIn("max_completion_tokens", request)
        self.assertEqual(request["response_format"]["type"], "json_schema")
        self.assertIs(request["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(
            request["response_format"]["json_schema"]["schema"]["$id"],
            "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate",
        )

    def test_candidate_is_deliberately_not_executable(self):
        with self.assertRaises(PermissionError):
            self.runner.validate_execution_authorization({})
        with self.assertRaises(PermissionError):
            self.runner.execute_once()

    def test_module_has_no_network_or_shell_imports(self):
        tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
        forbidden_roots = {"requests", "httpx", "urllib", "socket", "openai", "subprocess", "os"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported.isdisjoint(forbidden_roots), imported & forbidden_roots)

    def test_static_report_remains_fail_closed(self):
        report = self.runner.build_static_architecture_report()
        self.assertEqual(
            report["status"],
            "PASS_STATIC_REQUEST_ARCHITECTURE_AWAITING_CONSUMPTION_AND_PREFLIGHT_GATE",
        )
        self.assertEqual(report["expected_model_request_count"], 24)
        self.assertEqual(report["reference_question_count"], 67)
        self.assertEqual(report["meaning_count"], 67)
        for key in (
            "execution_authorized",
            "model_contact_authorized",
            "preflight_authorized",
            "automatic_retry_authorized",
            "automatic_rerun_authorized",
            "output_repair_authorized",
            "ready_for_user_approval",
            "qualification_claim_allowed",
        ):
            self.assertIs(report[key], False, key)


if __name__ == "__main__":
    unittest.main()
