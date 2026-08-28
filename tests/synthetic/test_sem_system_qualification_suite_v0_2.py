from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.validation.semantic_qualification_oracle_harness_v0_1 import (
    build_qualification_oracle_bundle,
)

ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_suite_candidate_v0_2.json"
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SemanticSystemQualificationSuiteV02Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = load(SUITE_PATH)
        self.gold = load(GOLD_PATH)
        self.cases = self.suite["cases"]

    def test_s01_candidate_is_not_frozen_or_execution_authorized(self) -> None:
        self.assertEqual(self.suite["status"], "ARCHITECTURE_CANDIDATE")
        self.assertFalse(self.suite["execution_authorized"])
        self.assertFalse(self.suite["model_contact_authorized"])
        self.assertTrue(self.suite["freeze_hash_binding_required_before_execution"])
        self.assertTrue(self.suite["human_approval_required_before_freeze"])

    def test_s02_case_count_and_ids_are_consistent(self) -> None:
        self.assertEqual(self.suite["case_count"], len(self.cases))
        ids = [case["system_case_id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_s03_gold_remains_qualification_only_and_model_invisible(self) -> None:
        bundle = build_qualification_oracle_bundle(self.gold)
        self.assertTrue(bundle["qualification_only"])
        self.assertFalse(bundle["model_contact_authorized"])
        self.assertFalse(bundle["human_gold_runtime_dependency"])
        self.assertFalse(self.suite["human_gold_runtime_dependency"])
        self.assertFalse(self.suite["model_visible_gold"])

    def test_s04_pf2_pf9_pf12_all_have_complete_and_omit_all_cases(self) -> None:
        for pf_id in ("PF2", "PF9", "PF12"):
            families = {
                case["case_family"]
                for case in self.cases
                if case.get("pf_id") == pf_id
            }
            self.assertIn("COMPLETE_REQUIRED_SET", families)
            self.assertIn("OMIT_ALL_REQUIRED", families)

    def test_s05_each_required_assignment_has_symmetric_single_omission_case(self) -> None:
        bundle = build_qualification_oracle_bundle(self.gold)
        for pf_bundle in bundle["cases"]:
            pf_id = pf_bundle["pf_id"]
            expected = {tuple(pair) for pair in pf_bundle["required_assignments"]}
            observed = {
                tuple(case["omitted_assignment"])
                for case in self.cases
                if case.get("pf_id") == pf_id
                and case.get("case_family") == "OMIT_ONE_REQUIRED"
            }
            self.assertEqual(observed, expected)

    def test_s06_pf9_pf12_cover_multiple_required_omissions(self) -> None:
        for pf_id in ("PF9", "PF12"):
            matches = [
                case for case in self.cases
                if case.get("pf_id") == pf_id
                and case.get("case_family") == "OMIT_MULTIPLE_REQUIRED"
            ]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["expected_behavior"], "SEMANTIC_COMPLETENESS_STOP")

    def test_s07_optional_assignment_never_substitutes_for_pf2_required_assignment(self) -> None:
        matches = [
            case for case in self.cases
            if case.get("case_family") == "OPTIONAL_PRESENT_REQUIRED_MISSING"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["pf_id"], "PF2")
        self.assertEqual(matches[0]["preserved_optional_assignment"], ["2.4", "PF2"])
        self.assertEqual(matches[0]["expected_behavior"], "SEMANTIC_COMPLETENESS_STOP")

    def test_s08_same_source_multi_proposal_is_covered_for_all_target_pfs(self) -> None:
        covered = {
            case.get("pf_id") for case in self.cases
            if case.get("case_family") == "MULTI_PROPOSAL_SAME_SOURCE"
        }
        self.assertEqual(covered, {"PF2", "PF9", "PF12"})

    def test_s09_cross_source_false_completion_is_symmetric_for_all_target_pfs(self) -> None:
        matches = [
            case for case in self.cases
            if case.get("case_family") == "MULTI_SOURCE_PROVENANCE"
        ]
        self.assertEqual({case["pf_id"] for case in matches}, {"PF2", "PF9", "PF12"})
        self.assertEqual(len(matches), 3)
        for case in matches:
            self.assertNotEqual(case["target_source_location_id"], case["other_source_location_id"])
            self.assertEqual(case["expected_behavior"], "SEMANTIC_COMPLETENESS_STOP")

    def test_s10_malformed_nested_types_and_unknown_state_are_covered(self) -> None:
        malformed = [
            case for case in self.cases
            if case.get("case_family") == "MALFORMED_NESTED_TYPE"
        ]
        self.assertGreaterEqual(len(malformed), 3)
        self.assertTrue(all(case["expected_behavior"] == "FAIL_CLOSED_STOP" for case in malformed))
        self.assertTrue(any(case.get("case_family") == "UNKNOWN_STATE_STOP" for case in self.cases))

    def test_s11_stop_class_routing_contract_is_declared(self) -> None:
        self.assertEqual(
            set(self.suite["required_stop_classes"]),
            {"TECHNICAL_BOUNDARY_STOP", "SEMANTIC_COMPLETENESS_STOP", "UNKNOWN_STATE_STOP"},
        )

    def test_s12_inactive_trigger_cannot_grant_global_downstream_authority(self) -> None:
        matches = [
            case for case in self.cases
            if case.get("case_family") == "INACTIVE_TRIGGER_AUTHORITY"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["expected_behavior"], "NO_COMPLETENESS_ASSESSMENT")
        self.assertEqual(matches[0]["global_downstream_authority"], "NONE")

    def test_s13_suite_cannot_change_model_qualification_or_decision_authority(self) -> None:
        self.assertFalse(self.suite["model_qualification_changed"])
        self.assertEqual(self.suite["decision_authority"], "NONE")
        self.assertFalse(self.suite["automatic_semantic_repair"])
        self.assertFalse(self.suite["auto_assignment_performed"])

    def test_s14_no_broader_authorization_is_smuggled_into_candidate(self) -> None:
        for key in (
            "real_data_authorized",
            "pilot_authorized",
            "production_authorized",
            "benchmark_generalization_authorized",
            "phase_f_authorized",
        ):
            self.assertFalse(self.suite[key], key)


if __name__ == "__main__":
    unittest.main()
