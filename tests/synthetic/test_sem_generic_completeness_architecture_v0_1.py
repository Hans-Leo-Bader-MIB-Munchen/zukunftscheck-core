from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH_PATH = ROOT / "docs/architecture/ZS-DEV-KI-B-SEM-GENERIC-COMPLETENESS-ARCHITEKTUR-2026-001_v0.1.md"
PROFILE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_runtime_completeness_profiles_candidate_v0_1.json"
GOLD_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"


class SemGenericCompletenessArchitectureV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.arch = ARCH_PATH.read_text(encoding="utf-8")
        cls.profiles = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        cls.gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))

    def test_a01_architecture_separates_qualification_oracle_and_runtime_profiles(self) -> None:
        self.assertIn("Qualification Required Sets", self.arch)
        self.assertIn("Runtime Required Profiles", self.arch)
        self.assertIn("Runtime-Profil darf **nicht** auf einen Human-Gold-Dateipfad", self.arch)

    def test_a02_candidate_profiles_have_no_runtime_gold_dependency(self) -> None:
        self.assertFalse(self.profiles["human_gold_runtime_dependency"])
        serialized = json.dumps(self.profiles, ensure_ascii=False).lower()
        self.assertNotIn("human_gold_frozen", serialized)
        self.assertNotIn("gold_case_id", serialized)

    def test_a03_pf2_required_set_matches_frozen_gold_without_importing_gold_at_runtime(self) -> None:
        pf2_gold = next(row for row in self.gold["cases"] if row["case_id"] == "ZS-KI-B-SEM-V07-Q-PF2-SYN-001")
        pf2_profile = next(row for row in self.profiles["profiles"] if row["pf_id"] == "PF2")
        self.assertEqual(pf2_profile["required_assignments"], pf2_gold["expected_assignments"])
        self.assertFalse(pf2_profile["runtime_enabled"])
        self.assertTrue(pf2_profile["requalification_required"])

    def test_a04_pf9_and_pf12_are_qualification_targets_not_runtime_claims(self) -> None:
        for pf_id, case_id in (
            ("PF9", "ZS-KI-B-SEM-V07-Q-PF9-SYN-001"),
            ("PF12", "ZS-KI-B-SEM-V07-Q-PF12-SYN-001"),
        ):
            gold = next(row for row in self.gold["cases"] if row["case_id"] == case_id)
            profile = next(row for row in self.profiles["profiles"] if row["pf_id"] == pf_id)
            self.assertEqual(profile["required_assignments"], gold["expected_assignments"])
            self.assertEqual(profile["status"], "QUALIFICATION_TARGET_ONLY")
            self.assertIsNone(profile["trigger_policy"])
            self.assertFalse(profile["runtime_enabled"])

    def test_a05_no_profile_can_grant_decision_authority_or_repair(self) -> None:
        self.assertEqual(self.profiles["decision_authority"], "NONE")
        self.assertFalse(self.profiles["automatic_semantic_repair"])
        self.assertFalse(self.profiles["auto_assignment_performed"])

    def test_a06_natural_language_precision_is_explicit_open_risk(self) -> None:
        risks = {row["risk_id"]: row for row in self.profiles["open_risks"]}
        self.assertIn("OPEN_RISK_NATURAL_LANGUAGE_TRIGGER_PRECISION", risks)
        self.assertIn("nur", risks["OPEN_RISK_NATURAL_LANGUAGE_TRIGGER_PRECISION"]["description"])
        self.assertIn("OPEN_RISK_NATURAL_LANGUAGE_TRIGGER_PRECISION", self.arch)

    def test_a07_no_execution_or_downstream_authorization_is_created(self) -> None:
        for key in (
            "execution_authorized",
            "model_run_authorized",
            "real_data_authorized",
            "pilot_authorized",
            "production_authorized",
            "benchmark_generalisation_authorized",
            "phase_f_authorized",
        ):
            self.assertFalse(self.profiles[key], key)


if __name__ == "__main__":
    unittest.main()
