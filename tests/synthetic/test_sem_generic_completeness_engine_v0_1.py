from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_completeness_profile_engine_v0_1 import evaluate_completeness_profile
from core.validation.semantic_completeness_profile_loader_v0_1 import (
    runtime_enabled_profiles,
    validate_profile_set,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_runtime_completeness_profiles_candidate_v0_1.json"


def response_with(*groups: tuple[tuple[str, str], ...]) -> dict:
    proposals = []
    for index, assignments in enumerate(groups or (tuple(),), start=1):
        proposals.append(
            {
                "proposal_id": f"P-{index}",
                "source_location_id": "SL-001",
                "normalized_statement": "synthetic",
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {
                        "question_id": question_id,
                        "pf_id": pf_id,
                        "assignment_confidence": "UNCERTAIN",
                        "human_review_required": True,
                    }
                    for question_id, pf_id in assignments
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": True,
            }
        )
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": "SL-001",
        "proposals": proposals,
    }


def profile(pf_id: str, required: list[str]) -> dict:
    return {
        "profile_id": f"{pf_id}_TEST_PROFILE",
        "pf_id": pf_id,
        "required_assignments": [
            {"question_id": question_id, "pf_id": pf_id} for question_id in required
        ],
        "trigger_policy": {"type": "SYNTHETIC_TEST_TRIGGER"},
        "stop_code": "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED",
        "decision_authority": "NONE",
    }


class SemanticGenericCompletenessEngineV01Tests(unittest.TestCase):
    def test_g01_candidate_profile_set_has_no_runtime_enabled_profiles(self) -> None:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        validated = validate_profile_set(payload)
        self.assertEqual(runtime_enabled_profiles(validated), [])
        self.assertFalse(validated["human_gold_runtime_dependency"])

    def test_g02_pf9_missing_required_assignment_fail_closes(self) -> None:
        result = evaluate_completeness_profile(
            profile=profile("PF9", ["9.1", "9.2", "9.3"]),
            trigger_active=True,
            model_response=response_with((("9.1", "PF9"), ("9.3", "PF9"))),
        )
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_downstream_use_allowed"])
        self.assertEqual(result["missing_required_assignments"], [["9.2", "PF9"]])
        self.assertEqual(result["stop_class"], "SEMANTIC_COMPLETENESS_STOP")
        self.assertEqual(result["review_metadata"]["review_class"], "SEMANTIC_COMPLETENESS_STOP")

    def test_g03_pf12_complete_required_set_does_not_stop(self) -> None:
        result = evaluate_completeness_profile(
            profile=profile("PF12", ["12.1", "12.2", "12.3"]),
            trigger_active=True,
            model_response=response_with(
                (("12.1", "PF12"), ("12.2", "PF12"), ("12.3", "PF12"))
            ),
        )
        self.assertFalse(result["human_review_required"])
        self.assertTrue(result["automatic_downstream_use_allowed"])
        self.assertEqual(result["missing_required_assignments"], [])
        self.assertIsNone(result["stop_class"])

    def test_g04_inactive_trigger_makes_no_completeness_stop(self) -> None:
        result = evaluate_completeness_profile(
            profile=profile("PF9", ["9.1", "9.2", "9.3"]),
            trigger_active=False,
            model_response=response_with((("9.1", "PF9"),)),
        )
        self.assertFalse(result["human_review_required"])
        self.assertTrue(result["automatic_downstream_use_allowed"])
        self.assertEqual(result["missing_required_assignments"], [])

    def test_g05_assignments_across_multiple_proposals_are_aggregated(self) -> None:
        result = evaluate_completeness_profile(
            profile=profile("PF12", ["12.1", "12.2", "12.3"]),
            trigger_active=True,
            model_response=response_with(
                (("12.1", "PF12"),),
                (("12.2", "PF12"), ("12.3", "PF12")),
            ),
        )
        self.assertFalse(result["human_review_required"])
        self.assertEqual(result["missing_required_assignments"], [])

    def test_g06_engine_never_mutates_or_repairs_model_output(self) -> None:
        response = response_with((("9.1", "PF9"),))
        before = copy.deepcopy(response)
        result = evaluate_completeness_profile(
            profile=profile("PF9", ["9.1", "9.2", "9.3"]),
            trigger_active=True,
            model_response=response,
        )
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertFalse(result["auto_assignment_performed"])
        self.assertFalse(result["semantic_repair_performed"])
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertFalse(result["model_qualification_changed"])

    def test_g07_loader_rejects_human_gold_runtime_dependency(self) -> None:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        payload["human_gold_runtime_dependency"] = True
        with self.assertRaises(ValueError):
            validate_profile_set(payload)

    def test_g08_loader_rejects_forbidden_gold_reference(self) -> None:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        payload["profiles"][0]["gold_case_id"] = "FORBIDDEN"
        with self.assertRaises(ValueError):
            validate_profile_set(payload)

    def test_g09_runtime_enabled_profile_requires_trigger_policy(self) -> None:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        payload["profiles"][1]["runtime_enabled"] = True
        self.assertIsNone(payload["profiles"][1]["trigger_policy"])
        with self.assertRaises(ValueError):
            validate_profile_set(payload)


if __name__ == "__main__":
    unittest.main()
