from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.validation.semantic_system_qualification_execution_harness_v0_1 import (
    EXPECTED_CASE_COUNT,
    execute_frozen_system_qualification_once,
    materialize_frozen_system_cases,
)

ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_suite_frozen_v0_2.json"
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
PROFILE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_generic_system_composition_profiles_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SemanticSystemQualificationExecutionHarnessV01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = load(SUITE_PATH)
        self.gold = load(GOLD_PATH)
        self.profiles = load(PROFILE_PATH)

    def materialized(self) -> list[dict]:
        return materialize_frozen_system_cases(suite=self.suite, gold=self.gold)

    def test_h01_materializes_exactly_29_unique_frozen_case_ids(self) -> None:
        rows = self.materialized()
        ids = [row["system_case_id"] for row in rows]
        self.assertEqual(len(rows), EXPECTED_CASE_COUNT)
        self.assertEqual(len(set(ids)), EXPECTED_CASE_COUNT)
        self.assertEqual(ids, [case["system_case_id"] for case in self.suite["cases"]])

    def test_h02_materialized_inputs_are_synthetic_and_model_contact_forbidden(self) -> None:
        rows = self.materialized()
        self.assertTrue(all(row["data_class"] == "SYNTHETIC_ONLY" for row in rows))
        self.assertTrue(all(row["model_contact_authorized"] is False for row in rows))
        self.assertFalse(self.suite["model_contact_authorized"])

    def test_h03_cross_source_cases_keep_target_and_other_source_separate(self) -> None:
        rows = [
            row for row in self.materialized()
            if row["case_spec"]["case_family"] == "MULTI_SOURCE_PROVENANCE"
        ]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["target_source_location_id"], "SL-A")
            self.assertEqual(row["allowed_source_location_ids"], {"SL-A", "SL-B"})
            sources = [proposal["source_location_id"] for proposal in row["model_response"]["proposals"]]
            self.assertEqual(sources, ["SL-A", "SL-B"])

    def test_h04_malformed_cases_modify_only_the_declared_nested_shape(self) -> None:
        rows = {
            row["case_spec"]["malformed_path"]: row
            for row in self.materialized()
            if row["case_spec"]["case_family"] == "MALFORMED_NESTED_TYPE"
        }
        self.assertEqual(set(rows), {
            "proposals",
            "proposals[].assignment_candidates",
            "proposals[].assignment_candidates[]",
        })
        self.assertEqual(rows["proposals"]["model_response"]["proposals"], "malformed")
        self.assertEqual(
            rows["proposals[].assignment_candidates"]["model_response"]["proposals"][0]["assignment_candidates"],
            "malformed",
        )
        self.assertEqual(
            rows["proposals[].assignment_candidates[]"]["model_response"]["proposals"][0]["assignment_candidates"],
            ["malformed"],
        )

    def test_h05_inactive_trigger_is_external_and_does_not_materialize_as_active(self) -> None:
        matches = [
            row for row in self.materialized()
            if row["case_spec"]["case_family"] == "INACTIVE_TRIGGER_AUTHORITY"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["trigger_state"], "INACTIVE")
        self.assertEqual(matches[0]["pf_id"], "PF9")

    def test_h06_execution_requires_explicit_external_authorization(self) -> None:
        with self.assertRaises(PermissionError):
            execute_frozen_system_qualification_once(
                suite=self.suite,
                gold=self.gold,
                profile_set=self.profiles,
                evaluated_commit="8e8509d9b534edcd2b82adfb0ec54ad7b0db5620",
                execution_authorized=False,
            )

    def test_h07_suite_mutation_or_nonfrozen_status_is_rejected_before_execution(self) -> None:
        changed = dict(self.suite)
        changed["status"] = "ARCHITECTURE_CANDIDATE"
        with self.assertRaises(ValueError):
            materialize_frozen_system_cases(suite=changed, gold=self.gold)


if __name__ == "__main__":
    unittest.main()
