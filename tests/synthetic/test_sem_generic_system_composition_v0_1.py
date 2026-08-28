from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.validation.semantic_qualification_oracle_harness_v0_1 import build_qualification_oracle_bundle
from core.validation.semantic_system_composition_v0_1 import (
    NO_COMPLETENESS_ASSESSMENT,
    NO_COMPLETENESS_STOP,
    SEMANTIC_COMPLETENESS_STOP,
    TECHNICAL_BOUNDARY_STOP,
    UNKNOWN_STATE_STOP,
    evaluate_semantic_system_composition,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_generic_system_composition_profiles_v0_1.json"
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"


def profiles() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def response_with(
    *groups: tuple[tuple[str, str], ...],
    target: str = "SL-001",
    proposal_sources: tuple[str, ...] | None = None,
) -> dict:
    proposals = []
    effective_groups = groups or (tuple(),)
    sources = proposal_sources or tuple(target for _ in effective_groups)
    for index, (assignments, source_id) in enumerate(zip(effective_groups, sources), start=1):
        proposals.append(
            {
                "proposal_id": f"P-{index}",
                "source_location_id": source_id,
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
        "source_location_id": target,
        "proposals": proposals,
    }


def compose(*, response: dict, pf_id: str, trigger_state: str, allowed: set[str] | None = None, target: str = "SL-001") -> dict:
    return evaluate_semantic_system_composition(
        model_response=response,
        allowed_source_location_ids=allowed or {target},
        target_source_location_id=target,
        pf_id=pf_id,
        trigger_state=trigger_state,
        profile_set=profiles(),
    )


class SemanticGenericSystemCompositionV01Tests(unittest.TestCase):
    def test_c01_profiles_match_frozen_human_gold_oracle_required_assignments(self) -> None:
        gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
        bundle = build_qualification_oracle_bundle(gold)
        expected = {
            row["pf_id"]: sorted(tuple(pair) for pair in row["required_assignments"])
            for row in bundle["cases"]
        }
        actual = {
            profile["pf_id"]: sorted(
                (item["question_id"], item["pf_id"])
                for item in profile["required_assignments"]
            )
            for profile in profiles()["profiles"]
        }
        self.assertEqual(actual, expected)
        self.assertFalse(profiles()["human_gold_runtime_dependency"])

    def test_c02_pf2_complete_active_has_no_completeness_stop_and_no_authority(self) -> None:
        result = compose(
            response=response_with((("2.1", "PF2"), ("2.2", "PF2"))),
            pf_id="PF2",
            trigger_state="ACTIVE",
        )
        self.assertEqual(result["behavior"], NO_COMPLETENESS_STOP)
        self.assertTrue(result["completeness_assessed"])
        self.assertEqual(result["global_downstream_authority"], "NONE")
        self.assertEqual(result["decision_authority"], "NONE")
        self.assertFalse(result["model_qualification_changed"])

    def test_c03_pf9_missing_required_active_stops(self) -> None:
        result = compose(
            response=response_with((("9.1", "PF9"), ("9.3", "PF9"))),
            pf_id="PF9",
            trigger_state="ACTIVE",
        )
        self.assertEqual(result["behavior"], SEMANTIC_COMPLETENESS_STOP)
        self.assertEqual(result["stop_class"], SEMANTIC_COMPLETENESS_STOP)
        self.assertEqual(
            result["completeness_result"]["missing_required_assignments"],
            [["9.2", "PF9"]],
        )

    def test_c04_pf12_same_source_multi_proposal_aggregates(self) -> None:
        result = compose(
            response=response_with(
                (("12.1", "PF12"),),
                (("12.2", "PF12"), ("12.3", "PF12")),
            ),
            pf_id="PF12",
            trigger_state="ACTIVE",
        )
        self.assertEqual(result["behavior"], NO_COMPLETENESS_STOP)

    def test_c05_cross_source_assignments_cannot_false_complete_target(self) -> None:
        response = response_with(
            (("9.1", "PF9"),),
            (("9.2", "PF9"), ("9.3", "PF9")),
            target="SL-A",
            proposal_sources=("SL-A", "SL-B"),
        )
        result = compose(
            response=response,
            pf_id="PF9",
            trigger_state="ACTIVE",
            allowed={"SL-A", "SL-B"},
            target="SL-A",
        )
        self.assertEqual(result["behavior"], SEMANTIC_COMPLETENESS_STOP)
        self.assertEqual(
            result["completeness_result"]["observed_assignments"],
            [["9.1", "PF9"]],
        )
        self.assertEqual(
            result["completeness_result"]["missing_required_assignments"],
            [["9.2", "PF9"], ["9.3", "PF9"]],
        )

    def test_c06_inactive_trigger_skips_completeness_without_global_release(self) -> None:
        result = compose(
            response=response_with((("9.1", "PF9"),)),
            pf_id="PF9",
            trigger_state="INACTIVE",
        )
        self.assertEqual(result["behavior"], NO_COMPLETENESS_ASSESSMENT)
        self.assertFalse(result["completeness_assessed"])
        self.assertIsNone(result["completeness_result"])
        self.assertEqual(result["global_downstream_authority"], "NONE")
        self.assertNotIn("automatic_downstream_use_allowed", result)

    def test_c07_unknown_trigger_fail_closes(self) -> None:
        result = compose(
            response=response_with((("9.1", "PF9"),)),
            pf_id="PF9",
            trigger_state="UNKNOWN",
        )
        self.assertEqual(result["behavior"], UNKNOWN_STATE_STOP)
        self.assertEqual(result["stop_code"], "UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED")
        self.assertTrue(result["human_review_required"])

    def test_c08_invalid_trigger_value_fail_closes_as_unknown_state(self) -> None:
        result = compose(
            response=response_with((("9.1", "PF9"),)),
            pf_id="PF9",
            trigger_state="MAYBE",
        )
        self.assertEqual(result["behavior"], UNKNOWN_STATE_STOP)

    def test_c09_unknown_pf_fail_closes(self) -> None:
        result = compose(
            response=response_with(tuple()),
            pf_id="PF99",
            trigger_state="ACTIVE",
        )
        self.assertEqual(result["behavior"], UNKNOWN_STATE_STOP)

    def test_c10_boundary_target_mismatch_stops_before_completeness(self) -> None:
        response = response_with((("9.1", "PF9"), ("9.2", "PF9"), ("9.3", "PF9")), target="SL-B")
        result = compose(
            response=response,
            pf_id="PF9",
            trigger_state="ACTIVE",
            allowed={"SL-A", "SL-B"},
            target="SL-A",
        )
        self.assertEqual(result["behavior"], TECHNICAL_BOUNDARY_STOP)
        self.assertEqual(result["stop_class"], TECHNICAL_BOUNDARY_STOP)
        self.assertEqual(result["stop_code"], "TARGET_SOURCE_LOCATION_MISMATCH")
        self.assertFalse(result["completeness_assessed"])

    def test_c11_malformed_nested_assignments_fail_closed_before_completeness(self) -> None:
        response = response_with((("9.1", "PF9"),))
        response["proposals"][0]["assignment_candidates"] = "malformed"
        result = compose(response=response, pf_id="PF9", trigger_state="ACTIVE")
        self.assertEqual(result["behavior"], TECHNICAL_BOUNDARY_STOP)
        self.assertFalse(result["completeness_assessed"])

    def test_c12_model_output_is_never_mutated_or_repaired(self) -> None:
        response = response_with((("9.1", "PF9"),))
        before = copy.deepcopy(response)
        result = compose(response=response, pf_id="PF9", trigger_state="ACTIVE")
        self.assertEqual(response, before)
        self.assertFalse(result["model_output_mutated"])
        self.assertFalse(result["automatic_semantic_repair"])
        self.assertFalse(result["auto_assignment_performed"])
        self.assertFalse(result["model_qualification_changed"])

    def test_c13_profile_set_with_human_gold_runtime_dependency_fail_closes(self) -> None:
        profile_set = profiles()
        profile_set["human_gold_runtime_dependency"] = True
        result = evaluate_semantic_system_composition(
            model_response=response_with((("9.1", "PF9"),)),
            allowed_source_location_ids={"SL-001"},
            target_source_location_id="SL-001",
            pf_id="PF9",
            trigger_state="ACTIVE",
            profile_set=profile_set,
        )
        self.assertEqual(result["behavior"], UNKNOWN_STATE_STOP)
        self.assertIn("INVALID_PROFILE_SET", result["reason"])


if __name__ == "__main__":
    unittest.main()
