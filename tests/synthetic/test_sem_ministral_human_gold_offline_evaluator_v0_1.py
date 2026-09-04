from __future__ import annotations

import ast
import inspect
import unittest

import scripts.zs_ki_b_sem_ministral_human_gold_offline_evaluator_v0_1 as evaluator


class MinistralHumanGoldOfflineEvaluatorV01Tests(unittest.TestCase):
    def _response(self, assignments: list[tuple[str, str]], *, conflict: bool = False) -> dict:
        return {
            "proposals": [
                {
                    "assignment_candidates": [
                        {"question_id": question_id, "pf_id": pf_id}
                        for question_id, pf_id in assignments
                    ],
                    "conflict_candidate_refs": ["SRC-2"] if conflict else [],
                }
            ]
        }

    def test_required_assignment_is_required(self) -> None:
        gold = {"expected_assignments": [{"question_id": "5.5", "pf_id": "PF5"}]}
        result = evaluator.evaluate_gold(gold, self._response([]))
        self.assertFalse(result["passed"])
        self.assertEqual(result["missing_required"], [["5.5", "PF5"]])

    def test_optional_assignment_is_allowed_not_required(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "2.1", "pf_id": "PF2"}],
            "optional_assignments": [{"question_id": "2.4", "pf_id": "PF2"}],
        }
        self.assertTrue(evaluator.evaluate_gold(gold, self._response([("2.1", "PF2")]))["passed"])
        self.assertTrue(evaluator.evaluate_gold(gold, self._response([("2.1", "PF2"), ("2.4", "PF2")]))["passed"])

    def test_forbidden_assignment_fails(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "4.2", "pf_id": "PF4"}],
            "forbidden_assignments": [{"question_id": "4.5", "pf_id": "PF4"}],
        }
        result = evaluator.evaluate_gold(gold, self._response([("4.2", "PF4"), ("4.5", "PF4")]))
        self.assertFalse(result["passed"])
        self.assertEqual(result["forbidden_present"], [["4.5", "PF4"]])

    def test_unlisted_assignment_is_spurious_and_fails(self) -> None:
        gold = {"expected_assignments": [{"question_id": "5.5", "pf_id": "PF5"}]}
        result = evaluator.evaluate_gold(gold, self._response([("5.5", "PF5"), ("5.4", "PF5")]))
        self.assertFalse(result["passed"])
        self.assertEqual(result["spurious_assignments"], [["5.4", "PF5"]])

    def test_expected_conflict_candidate_false_is_enforced(self) -> None:
        gold = {
            "expected_assignments": [{"question_id": "4.2", "pf_id": "PF4"}],
            "expected_conflict_candidate": False,
        }
        result = evaluator.evaluate_gold(gold, self._response([("4.2", "PF4")], conflict=True))
        self.assertFalse(result["passed"])
        self.assertFalse(result["conflict_candidate_match"])

    def test_frozen_gold_and_policy_blobs_are_bound(self) -> None:
        _suite, gold, policy = evaluator.validate_frozen_inputs()
        self.assertEqual(gold["status"], "HUMAN_APPROVED_FROZEN")
        self.assertFalse(gold["model_visible"])
        self.assertEqual(policy["status"], "HUMAN_APPROVED_FROZEN")

    def test_module_imports_no_network_or_model_runtime_library(self) -> None:
        tree = ast.parse(inspect.getsource(evaluator))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue({"urllib", "socket", "requests", "httpx", "openai"}.isdisjoint(imported))

    def test_evaluation_loop_is_non_short_circuiting(self) -> None:
        source = inspect.getsource(evaluator.evaluate_result)
        self.assertIn("deliberately never stops at first case FAIL", source)
        self.assertNotIn("break", source)


if __name__ == "__main__":
    unittest.main()
