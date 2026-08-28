from __future__ import annotations

import json
from pathlib import Path
import unittest

from core.validation.semantic_qualification_oracle_harness_v0_1 import (
    build_qualification_oracle_bundle,
    generate_negative_variants,
    qualification_case_by_pf,
    required_pairs,
)

ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"


class SemanticQualificationOracleHarnessV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))

    def test_q01_uses_only_frozen_model_invisible_gold(self) -> None:
        self.assertEqual(self.gold["status"], "HUMAN_APPROVED_FROZEN")
        self.assertFalse(self.gold["model_visible"])
        for pf_id in ("PF2", "PF9", "PF12"):
            case = qualification_case_by_pf(self.gold, pf_id)
            self.assertIn(f"-Q-{pf_id}-SYN-001", case["case_id"])

    def test_q02_required_sets_match_frozen_gold(self) -> None:
        expected = {
            "PF2": (("2.1", "PF2"), ("2.2", "PF2")),
            "PF9": (("9.1", "PF9"), ("9.2", "PF9"), ("9.3", "PF9")),
            "PF12": (("12.1", "PF12"), ("12.2", "PF12"), ("12.3", "PF12")),
        }
        for pf_id, pairs in expected.items():
            with self.subTest(pf_id=pf_id):
                self.assertEqual(required_pairs(qualification_case_by_pf(self.gold, pf_id)), pairs)

    def test_q03_each_required_assignment_gets_omit_one_variant(self) -> None:
        for pf_id in ("PF2", "PF9", "PF12"):
            case = qualification_case_by_pf(self.gold, pf_id)
            required = set(required_pairs(case))
            variants = generate_negative_variants(case)
            omitted = {
                tuple(variant["missing_required_assignments"][0])
                for variant in variants
                if variant["variant_kind"] == "OMIT_ONE_REQUIRED"
            }
            self.assertEqual(omitted, required)

    def test_q04_complete_omission_variant_exists_for_all_selected_pfs(self) -> None:
        for pf_id in ("PF2", "PF9", "PF12"):
            case = qualification_case_by_pf(self.gold, pf_id)
            required = {tuple(pair) for pair in required_pairs(case)}
            variants = generate_negative_variants(case)
            omit_all = [v for v in variants if v["variant_kind"] == "OMIT_ALL_REQUIRED"]
            self.assertEqual(len(omit_all), 1)
            self.assertEqual({tuple(pair) for pair in omit_all[0]["missing_required_assignments"]}, required)

    def test_q05_pf2_optional_assignment_can_remain_while_required_is_missing(self) -> None:
        case = qualification_case_by_pf(self.gold, "PF2")
        variants = generate_negative_variants(case)
        omit_21 = next(
            v for v in variants
            if v["variant_kind"] == "OMIT_ONE_REQUIRED"
            and v["missing_required_assignments"] == [["2.1", "PF2"]]
        )
        self.assertIn(["2.4", "PF2"], omit_21["assignments"])
        self.assertIn(["2.2", "PF2"], omit_21["assignments"])
        self.assertNotIn(["2.1", "PF2"], omit_21["assignments"])

    def test_q06_multiple_required_omission_variant_exists(self) -> None:
        for pf_id in ("PF9", "PF12"):
            variants = generate_negative_variants(qualification_case_by_pf(self.gold, pf_id))
            multi = [v for v in variants if v["variant_kind"] == "OMIT_MULTIPLE_REQUIRED"]
            self.assertEqual(len(multi), 1)
            self.assertGreaterEqual(len(multi[0]["missing_required_assignments"]), 2)

    def test_q07_bundle_grants_no_runtime_or_model_authority(self) -> None:
        bundle = build_qualification_oracle_bundle(self.gold)
        self.assertTrue(bundle["qualification_only"])
        self.assertFalse(bundle["model_contact_authorized"])
        self.assertEqual(bundle["decision_authority"], "NONE")
        self.assertFalse(bundle["human_gold_runtime_dependency"])
        self.assertFalse(bundle["runtime_profiles_created"])
        self.assertFalse(bundle["runtime_trigger_policies_created"])
        self.assertFalse(bundle["model_qualification_changed"])
        self.assertFalse(bundle["automatic_semantic_repair"])
        self.assertFalse(bundle["auto_assignment_performed"])

    def test_q08_bundle_contains_only_selected_pf_qualification_cases(self) -> None:
        bundle = build_qualification_oracle_bundle(self.gold)
        self.assertEqual([case["pf_id"] for case in bundle["cases"]], ["PF2", "PF9", "PF12"])
        self.assertEqual(len(bundle["cases"]), 3)

    def test_q09_nonfrozen_or_model_visible_gold_is_rejected(self) -> None:
        not_frozen = dict(self.gold)
        not_frozen["status"] = "DRAFT"
        with self.assertRaises(ValueError):
            qualification_case_by_pf(not_frozen, "PF2")
        model_visible = dict(self.gold)
        model_visible["model_visible"] = True
        with self.assertRaises(ValueError):
            qualification_case_by_pf(model_visible, "PF2")


if __name__ == "__main__":
    unittest.main()
