import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as runner

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_authorization_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class V13ModelRunAuthorizationApprovedV02Tests(unittest.TestCase):
    def setUp(self):
        self.auth = load(AUTH)

    def test_exact_authorization_identity_scope_and_consumed_state(self):
        a = self.auth
        self.assertEqual(a["status"], "CONSUMED")
        self.assertEqual(a["run_type"], runner.RUN_TYPE)
        self.assertEqual(a["runner_version"], "v1.3")
        self.assertEqual(a["model"], "qwen3-14b")
        self.assertEqual(a["prompt_version"], runner.PROMPT_VERSION)
        self.assertEqual(a["expected_run_count"], 1)
        self.assertEqual(a["expected_model_request_count"], 16)
        self.assertTrue(a["single_run_only"])
        self.assertTrue(a["approval_is_single_use"])
        self.assertTrue(a["authorization_consumed"])
        self.assertEqual(a["consumed_observed_model_request_count"], 2)
        self.assertFalse(a["execution_authorized"])
        self.assertFalse(a["model_run_authorized"])
        self.assertFalse(a["model_contact_authorized"])

    def test_runtime_constraints_are_exact(self):
        a = self.auth
        self.assertEqual(a["required_loaded_context_length"], 32768)
        self.assertEqual(a["required_request_timeout_seconds"], 1800)
        self.assertTrue(a["synthetic_only"])
        self.assertTrue(a["local_loopback_only"])
        self.assertEqual(a["retry_count"], 0)
        self.assertFalse(a["output_repair"])
        self.assertFalse(a["remote_cloud"])
        self.assertFalse(a["real_data"])

    def test_semantic_scope_is_exact(self):
        a = self.auth
        self.assertEqual(a["semantic_boundary_version"], "semantic-boundary-v0.2")
        self.assertTrue(a["generic_system_composition_required"])
        self.assertEqual(a["generic_system_composition_version"], "semantic-system-composition-v0.1")
        self.assertEqual(a["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(a["non_profile_cases_boundary_only"])

    def test_runner_rejects_consumed_authorization_model_free(self):
        with self.assertRaises(PermissionError):
            runner.validate_execution_authorization("qwen3-14b")

    def test_dry_run_reports_closed_consumed_state_without_model_contact(self):
        with patch(
            "scripts.zs_ki_b_sem_qualifikation_runner_v0_8.current_git_commit",
            return_value="MODEL_FREE_TEST_COMMIT",
        ):
            payload = runner.build_dry_run_manifest(model="qwen3-14b")
        manifest = payload["manifest"]
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertEqual(manifest["expected_model_request_count"], 16)

    def test_no_downstream_release_is_authorized(self):
        a = self.auth
        for key in (
            "benchmark_approved",
            "generalisation_approved",
            "pilot_approved",
            "production_approved",
            "phase_f_approved",
        ):
            self.assertFalse(a[key])
        self.assertFalse(a["model_qualified_before_run"])
        self.assertTrue(a["model_qualification_may_only_change_after_result_review"])


if __name__ == "__main__":
    unittest.main()
