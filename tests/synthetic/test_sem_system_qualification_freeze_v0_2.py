from __future__ import annotations

import json
import string
import unittest
from pathlib import Path

from scripts.zs_ki_b_sem_system_qualification_freeze_v0_2 import (
    load_manifest,
    materialize_hashes,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_policy_candidate_v0_2.json"
SUITE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_suite_candidate_v0_2.json"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_freeze_manifest_candidate_v0_2.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SemanticSystemQualificationFreezeV02Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load(POLICY_PATH)
        self.suite = load(SUITE_PATH)
        self.manifest = load_manifest(MANIFEST_PATH)

    def test_f01_policy_is_only_freeze_candidate(self) -> None:
        self.assertEqual(self.policy["status"], "FREEZE_CANDIDATE")
        self.assertTrue(self.policy["human_approval_required_before_final_freeze"])
        self.assertFalse(self.policy["execution_authorized"])
        self.assertFalse(self.policy["model_contact_authorized"])

    def test_f02_suite_remains_unfrozen_candidate_until_explicit_approval(self) -> None:
        self.assertEqual(self.suite["status"], "ARCHITECTURE_CANDIDATE")
        self.assertEqual(self.suite["case_count"], 29)
        self.assertFalse(self.suite["execution_authorized"])
        self.assertFalse(self.suite["model_contact_authorized"])

    def test_f03_policy_preserves_authority_and_model_separation(self) -> None:
        self.assertEqual(self.policy["decision_authority"], "NONE")
        self.assertFalse(self.policy["model_qualification_changed"])
        self.assertFalse(self.policy["human_gold_runtime_dependency"])
        self.assertFalse(self.policy["model_visible_gold"])
        self.assertFalse(self.policy["automatic_semantic_repair"])
        self.assertFalse(self.policy["auto_assignment_performed"])
        self.assertTrue(self.policy["status_axes"]["must_remain_separate"])

    def test_f04_no_stop_is_not_global_release(self) -> None:
        rule = self.policy["no_completeness_stop_rule"]
        self.assertEqual(rule["global_downstream_authority"], "NONE")
        self.assertTrue(rule["must_not_be_interpreted_as_model_pass"])
        self.assertTrue(rule["must_not_be_interpreted_as_global_runtime_release"])

    def test_f05_manifest_binds_required_artifact_roles(self) -> None:
        roles = {entry["role"] for entry in self.manifest["artifacts"]}
        self.assertEqual(
            roles,
            {
                "policy",
                "suite",
                "generic_completeness_engine",
                "qualification_oracle_harness",
                "semantic_boundary",
                "semantic_runtime_guard",
                "source_human_gold",
                "suite_contract_tests",
            },
        )
        self.assertEqual(self.manifest["hash_algorithm"], "SHA-256")
        self.assertFalse(self.manifest["hashes_materialized"])

    def test_f06_materialization_produces_real_sha256_for_every_artifact(self) -> None:
        materialized = materialize_hashes(self.manifest, root=ROOT)
        self.assertEqual(materialized["status"], "HASH_BOUND_FREEZE_CANDIDATE")
        self.assertTrue(materialized["hashes_materialized"])
        hexdigits = set(string.hexdigits.lower())
        for artifact in materialized["artifacts"]:
            digest = artifact["sha256"]
            self.assertIsInstance(digest, str)
            self.assertEqual(len(digest), 64)
            self.assertTrue(set(digest) <= hexdigits)

    def test_f07_materialization_grants_no_execution_or_model_contact(self) -> None:
        materialized = materialize_hashes(self.manifest, root=ROOT)
        self.assertFalse(materialized["execution_authorized"])
        self.assertFalse(materialized["model_contact_authorized"])
        self.assertEqual(materialized["decision_authority"], "NONE")
        self.assertTrue(materialized["final_freeze_requires_explicit_human_approval"])

    def test_f08_broader_authorizations_remain_false(self) -> None:
        for obj in (self.policy, self.manifest):
            for key in (
                "real_data_authorized",
                "pilot_authorized",
                "production_authorized",
                "benchmark_generalization_authorized",
                "phase_f_authorized",
            ):
                self.assertFalse(obj[key], key)

    def test_f09_model_qualification_status_is_preserved(self) -> None:
        self.assertEqual(self.manifest["model_qualification_status_preserved"], "NOT_QUALIFIED")
        self.assertEqual(self.manifest["guarded_system_qualification_status"], "NOT_YET_EXECUTED")


if __name__ == "__main__":
    unittest.main()
