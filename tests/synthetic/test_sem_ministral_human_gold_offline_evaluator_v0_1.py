from __future__ import annotations

import ast
import inspect
import subprocess
import sys
import unittest
from pathlib import Path

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

    def _candidate_response(self, *, contract_version: str | None = None, proposal_review: bool = False) -> dict:
        return {
            "contract_version": contract_version or evaluator.EXPECTED_CANDIDATE_CONTRACT,
            "source_location_id": "SRC-1",
            "proposals": [
                {
                    "proposal_id": "P1",
                    "source_location_id": "SRC-1",
                    "normalized_statement": "Testaussage",
                    "finding_type_candidate": "DT",
                    "evidence_relation_type_candidate": "DIRECT",
                    "derivation_note": None,
                    "assignment_candidates": [
                        {
                            "question_id": "1.1",
                            "pf_id": "PF1",
                            "assignment_confidence": "CLEAR",
                            "human_review_required": False,
                        }
                    ],
                    "conflict_candidate_refs": [],
                    "gap_notes": [],
                    "uncertainty_notes": [],
                    "human_review_required": proposal_review,
                }
            ],
        }

    def _case(self) -> dict:
        return {
            "target_source_location_id": "SRC-1",
            "source_locations": [{"source_location_id": "SRC-1"}],
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

    def test_frozen_gold_policy_and_candidate_schema_are_bound(self) -> None:
        _suite, gold, policy = evaluator.validate_frozen_inputs()
        self.assertEqual(gold["status"], "HUMAN_APPROVED_FROZEN")
        self.assertFalse(gold["model_visible"])
        self.assertEqual(policy["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(evaluator.EXPECTED_CANDIDATE_SCHEMA_BLOB, "bc3dd4832db51677bdaf6f16028ade1b02214673")

    def test_candidate_contract_is_normalized_only_for_v02_boundary_reuse(self) -> None:
        result = evaluator.evaluate_boundary(self._case(), self._candidate_response())
        codes = [row["code"] for row in result["issues"]]
        self.assertNotIn("SEMANTIC_CONTRACT_VERSION_MISMATCH", codes)
        self.assertNotIn("SEMANTIC_CANDIDATE_CONTRACT_VERSION_MISMATCH", codes)
        self.assertTrue(result["passed"])

    def test_wrong_candidate_contract_fails_closed(self) -> None:
        result = evaluator.evaluate_boundary(
            self._case(),
            self._candidate_response(contract_version="ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"),
        )
        self.assertFalse(result["passed"])
        self.assertIn("SEMANTIC_CANDIDATE_CONTRACT_VERSION_MISMATCH", [row["code"] for row in result["issues"]])

    def test_candidate_normalization_preserves_real_review_flag_boundary_failure(self) -> None:
        response = self._candidate_response()
        response["proposals"][0]["uncertainty_notes"] = ["Unsicherheit"]
        response["proposals"][0]["human_review_required"] = False
        result = evaluator.evaluate_boundary(self._case(), response)
        self.assertFalse(result["passed"])
        self.assertIn("MISSING_PROPOSAL_REVIEW_FLAG", [row["code"] for row in result["issues"]])
        self.assertNotIn("SEMANTIC_CONTRACT_VERSION_MISMATCH", [row["code"] for row in result["issues"]])

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

    def test_direct_script_invocation_can_resolve_repo_imports(self) -> None:
        script = Path(evaluator.__file__).resolve()
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=script.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Offline-only evaluator", completed.stdout)


if __name__ == "__main__":
    unittest.main()
