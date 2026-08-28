from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as v13

ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def valid_response(case: dict, *, assignments: list[dict] | None = None) -> dict:
    target = case["target_source_location_id"]
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target,
        "proposals": [
            {
                "proposal_id": f"P-{target}-1",
                "source_location_id": target,
                "normalized_statement": "synthetic qualification response",
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "derivation_note": None,
                "assignment_candidates": assignments or [],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": False,
            }
        ],
    }


class TestSemQualificationRunnerV13Alignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load(SUITE_PATH)
        cls.cases = {row["case_id"]: row for row in cls.suite["cases"]}

    def test_r01_dry_run_is_not_authorized_and_performs_no_model_contact(self) -> None:
        # Unit-test the manifest contract independently from unrelated untracked
        # developer files. Production dry-runs keep the inherited clean-tree gate.
        with patch.object(v13.v11.v10.v09.base, "current_git_commit", return_value="0" * 40):
            payload = v13.build_dry_run_manifest(model="qwen3-14b")
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_QUALIFICATION_V1_3")
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertEqual(manifest["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])

    def test_r02_execution_authorization_fails_closed_while_not_approved(self) -> None:
        with self.assertRaises(PermissionError):
            v13.validate_execution_authorization("qwen3-14b")

    def test_r03_pf2_uses_generic_composition_and_stops_when_required_assignments_missing(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF2-SYN-001"]
        result = v13.evaluate_runtime_guard(case, valid_response(case))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF2")
        self.assertEqual(result["behavior"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertFalse(result["passed"])
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertEqual(result["global_downstream_authority"], "NONE")

    def test_r04_pf9_uses_generic_composition(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF9-SYN-001"]
        result = v13.evaluate_runtime_guard(case, valid_response(case))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF9")
        self.assertEqual(result["behavior"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertFalse(result["passed"])

    def test_r05_pf12_uses_generic_composition(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF12-SYN-001"]
        result = v13.evaluate_runtime_guard(case, valid_response(case))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF12")
        self.assertEqual(result["behavior"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertFalse(result["passed"])

    def test_r06_unqualified_pf_is_boundary_only(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF1-SYN-001"]
        result = v13.evaluate_runtime_guard(case, valid_response(case))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["passed"])
        self.assertFalse(result["completeness_profile_applied"])
        self.assertIsNone(result["composition_version"])
        self.assertEqual(result["runtime_guard_version"], "semantic-boundary-v0.2")

    def test_r07_challenge_case_is_boundary_only(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001"]
        result = v13.evaluate_runtime_guard(case, valid_response(case))
        self.assertTrue(result["formal_boundary_passed"])
        self.assertTrue(result["passed"])
        self.assertFalse(result["completeness_profile_applied"])
        self.assertEqual(result["runtime_guard_version"], "semantic-boundary-v0.2")


if __name__ == "__main__":
    unittest.main()
