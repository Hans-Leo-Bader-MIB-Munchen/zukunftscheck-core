from __future__ import annotations

import json
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as v13

ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestSemQualificationRunnerV13Alignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load(SUITE_PATH)
        cls.cases = {row["case_id"]: row for row in cls.suite["cases"]}

    def test_r01_dry_run_is_not_authorized_and_performs_no_model_contact(self) -> None:
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
        response = {
            "semantic_proposals": [{"proposal_id": "P1", "text": "Rathaus und Vorplatz"}],
            "assignment_candidates": [],
        }
        result = v13.evaluate_runtime_guard(case, response)
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF2")
        self.assertEqual(result["behavior"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertFalse(result["passed"])
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertEqual(result["global_downstream_authority"], "NONE")

    def test_r04_pf9_uses_generic_composition(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF9-SYN-001"]
        response = {
            "semantic_proposals": [{"proposal_id": "P1", "text": "Bestandsvermessung vor Freigabe"}],
            "assignment_candidates": [],
        }
        result = v13.evaluate_runtime_guard(case, response)
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF9")
        self.assertFalse(result["passed"])

    def test_r05_pf12_uses_generic_composition(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF12-SYN-001"]
        response = {
            "semantic_proposals": [{"proposal_id": "P1", "text": "Vermessung anfordern"}],
            "assignment_candidates": [],
        }
        result = v13.evaluate_runtime_guard(case, response)
        self.assertTrue(result["completeness_profile_applied"])
        self.assertEqual(result["pf_id"], "PF12")
        self.assertFalse(result["passed"])

    def test_r06_unqualified_pf_is_boundary_only(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-PF1-SYN-001"]
        response = {
            "semantic_proposals": [{"proposal_id": "P1", "text": "Gemeinde Beispielstadt"}],
            "assignment_candidates": [],
        }
        result = v13.evaluate_runtime_guard(case, response)
        self.assertFalse(result["completeness_profile_applied"])
        self.assertIsNone(result["composition_version"])
        self.assertEqual(result["runtime_guard_version"], "semantic-boundary-v0.2")

    def test_r07_challenge_case_is_boundary_only(self) -> None:
        case = self.cases["ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001"]
        response = {
            "semantic_proposals": [{"proposal_id": "P1", "text": "30 Fahrradstellplätze"}],
            "assignment_candidates": [],
        }
        result = v13.evaluate_runtime_guard(case, response)
        self.assertFalse(result["completeness_profile_applied"])
        self.assertEqual(result["runtime_guard_version"], "semantic-boundary-v0.2")


if __name__ == "__main__":
    unittest.main()
