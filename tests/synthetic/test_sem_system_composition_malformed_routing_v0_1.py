from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.validation.semantic_system_composition_v0_1 import (
    FAIL_CLOSED_STOP,
    NO_COMPLETENESS_STOP,
    TECHNICAL_BOUNDARY_STOP,
    evaluate_semantic_system_composition,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_generic_system_composition_profiles_v0_1.json"


def profile_set() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def valid_pf9_response() -> dict:
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": "SL-001",
        "proposals": [
            {
                "proposal_id": "P-1",
                "source_location_id": "SL-001",
                "normalized_statement": "synthetic",
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {"question_id": "9.1", "pf_id": "PF9", "assignment_confidence": "UNCERTAIN", "human_review_required": True},
                    {"question_id": "9.2", "pf_id": "PF9", "assignment_confidence": "UNCERTAIN", "human_review_required": True},
                    {"question_id": "9.3", "pf_id": "PF9", "assignment_confidence": "UNCERTAIN", "human_review_required": True},
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": True,
            }
        ],
    }


def compose(response: dict, *, target: str = "SL-001", allowed: set[str] | None = None) -> dict:
    return evaluate_semantic_system_composition(
        model_response=response,
        allowed_source_location_ids=allowed or {target},
        target_source_location_id=target,
        pf_id="PF9",
        trigger_state="ACTIVE",
        profile_set=profile_set(),
    )


class SemanticSystemCompositionMalformedRoutingV01Tests(unittest.TestCase):
    def test_r01_proposals_wrong_type_is_fail_closed(self) -> None:
        response = valid_pf9_response()
        response["proposals"] = "malformed"
        result = compose(response)
        self.assertEqual(result["behavior"], FAIL_CLOSED_STOP)
        self.assertEqual(result["stop_code"], "MISSING_SEMANTIC_PROPOSALS")
        self.assertTrue(result["human_review_required"])

    def test_r02_assignment_candidates_wrong_type_is_fail_closed(self) -> None:
        response = valid_pf9_response()
        response["proposals"][0]["assignment_candidates"] = "malformed"
        result = compose(response)
        self.assertEqual(result["behavior"], FAIL_CLOSED_STOP)
        self.assertEqual(result["stop_code"], "INVALID_ASSIGNMENT_CANDIDATES")

    def test_r03_assignment_item_wrong_type_is_fail_closed(self) -> None:
        response = valid_pf9_response()
        response["proposals"][0]["assignment_candidates"] = ["malformed"]
        result = compose(response)
        self.assertEqual(result["behavior"], FAIL_CLOSED_STOP)
        self.assertEqual(result["stop_code"], "INVALID_ASSIGNMENT_CANDIDATE")

    def test_r04_target_mismatch_remains_technical_boundary_stop(self) -> None:
        response = valid_pf9_response()
        response["source_location_id"] = "SL-B"
        response["proposals"][0]["source_location_id"] = "SL-B"
        result = compose(response, target="SL-A", allowed={"SL-A", "SL-B"})
        self.assertEqual(result["behavior"], TECHNICAL_BOUNDARY_STOP)
        self.assertEqual(result["stop_code"], "TARGET_SOURCE_LOCATION_MISMATCH")

    def test_r05_valid_complete_case_is_unchanged(self) -> None:
        result = compose(valid_pf9_response())
        self.assertEqual(result["behavior"], NO_COMPLETENESS_STOP)
        self.assertEqual(result["global_downstream_authority"], "NONE")
        self.assertFalse(result["model_output_mutated"])
        self.assertFalse(result["auto_assignment_performed"])
        self.assertFalse(result["model_qualification_changed"])


if __name__ == "__main__":
    unittest.main()
