#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_candidate_v0_1.json"
LIVE_AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_v0_1.json"


class MinistralPreflightAuthorizationCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        cls.live = json.loads(LIVE_AUTH_PATH.read_text(encoding="utf-8"))

    def test_r01_candidate_is_not_approved(self) -> None:
        self.assertEqual(self.candidate["status"], "PREPARED_NOT_APPROVED")
        for key in (
            "download_authorized",
            "model_load_authorized",
            "localhost_preflight_authorized",
            "model_contact_authorized",
            "generation_authorized",
            "qualification_execution_authorized",
        ):
            self.assertIs(self.candidate[key], False)

    def test_r02_live_gate_remains_closed(self) -> None:
        self.assertEqual(self.live["status"], "NOT_APPROVED")
        self.assertIs(self.live["download_authorized"], False)
        self.assertIs(self.live["model_load_authorized"], False)
        self.assertIs(self.live["localhost_preflight_authorized"], False)
        self.assertIs(self.live["model_contact_authorized"], False)

    def test_r03_exact_candidate_binding(self) -> None:
        expected = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
        self.assertEqual(self.candidate["model_repository_candidate"], expected)
        self.assertEqual(self.candidate["required_loaded_model_id"], expected)
        self.assertEqual(self.candidate["required_quantization"], "Q4_K_M")

    def test_r04_exact_local_preflight_constraints(self) -> None:
        self.assertEqual(self.candidate["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(self.candidate["required_loaded_context_length"], 32768)
        self.assertEqual(self.candidate["generation_request_count_max"], 0)

    def test_r05_requested_scope_is_preflight_only(self) -> None:
        self.assertEqual(
            self.candidate["requested_scope"],
            [
                "download_or_install_exact_candidate",
                "load_exact_candidate_in_lm_studio",
                "localhost_preflight_only_models_inventory_contact",
            ],
        )
        self.assertNotIn("generation", self.candidate["requested_scope"])
        self.assertNotIn("qualification_execution", self.candidate["requested_scope"])

    def test_r06_future_live_status_is_separate(self) -> None:
        self.assertEqual(
            self.candidate["required_future_live_status"],
            "EXPLICIT_USER_APPROVED_PREFLIGHT_ONLY",
        )
        self.assertEqual(
            self.candidate["next_gate_after_merge"],
            "SEPARATE_EXPLICIT_USER_APPROVAL_FOR_DOWNLOAD_LOAD_AND_PREFLIGHT_ONLY",
        )

    def test_r07_no_downstream_approvals(self) -> None:
        for key in (
            "model_qualified",
            "benchmark_approved",
            "generalisation_approved",
            "pilot_approved",
            "production_approved",
            "phase_f_approved",
        ):
            self.assertIs(self.candidate[key], False)

    def test_r08_candidate_does_not_mutate_live_gate(self) -> None:
        self.assertEqual(
            self.candidate["live_authorization_artifact"],
            "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_v0_1.json",
        )
        self.assertEqual(self.live["generation_request_count_max"], 0)
        self.assertIs(self.live["generation_authorized"], False)
        self.assertIs(self.live["qualification_execution_authorized"], False)


if __name__ == "__main__":
    unittest.main()
