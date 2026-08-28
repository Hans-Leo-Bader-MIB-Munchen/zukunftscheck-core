import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_authorization_candidate_v0_2.json"
PRERUN = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_prerun_package_v0_1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class V13ModelRunAuthorizationCandidateV02Tests(unittest.TestCase):
    def setUp(self):
        self.auth = load(AUTH)
        self.prerun = load(PRERUN)

    def test_candidate_remains_closed(self):
        self.assertEqual(self.auth["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(self.auth["execution_authorized"])
        self.assertFalse(self.auth["model_run_authorized"])
        self.assertFalse(self.auth["model_contact_authorized"])
        self.assertTrue(self.auth["approval_gate"]["no_execution_from_candidate"])

    def test_exact_single_run_scope(self):
        self.assertEqual(self.auth["expected_run_count"], 1)
        self.assertEqual(self.auth["expected_model_request_count"], 16)
        self.assertTrue(self.auth["single_run_only"])
        self.assertTrue(self.auth["approval_gate"]["approval_is_single_use"])

    def test_model_runner_prompt_are_fixed(self):
        self.assertEqual(self.auth["model"], "qwen3-14b")
        self.assertEqual(self.auth["runner_version"], "v1.3")
        self.assertEqual(self.auth["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")

    def test_local_synthetic_no_retry_no_repair(self):
        self.assertTrue(self.auth["synthetic_only"])
        self.assertTrue(self.auth["local_loopback_only"])
        self.assertEqual(self.auth["retry_count"], 0)
        self.assertFalse(self.auth["output_repair"])
        self.assertFalse(self.auth["remote_cloud"])
        self.assertFalse(self.auth["real_data"])

    def test_composition_scope_is_limited(self):
        self.assertEqual(self.auth["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertEqual(self.auth["generic_system_composition_version"], "semantic-system-composition-v0.1")
        self.assertEqual(self.auth["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(self.auth["non_profile_cases_boundary_only"])

    def test_prerun_reference_matches_frozen_package(self):
        self.assertEqual(self.auth["prerun_package"]["status"], self.prerun["status"])
        self.assertEqual(self.prerun["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertFalse(self.prerun["execution_authorized"])
        self.assertFalse(self.prerun["model_run_authorized"])

    def test_no_downstream_release_is_implied(self):
        for key in (
            "benchmark_approved",
            "generalisation_approved",
            "pilot_approved",
            "production_approved",
            "phase_f_approved",
        ):
            self.assertFalse(self.auth[key])
        self.assertFalse(self.auth["model_qualified_before_run"])
        self.assertTrue(self.auth["model_qualification_may_only_change_after_result_review"])


if __name__ == "__main__":
    unittest.main()
