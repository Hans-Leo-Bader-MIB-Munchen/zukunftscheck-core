from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_prerun_package_v0_1.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_authorization_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip().lower()


class TestSemV13ModelRunPrerunPackageV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = load(PACKAGE_PATH)

    def test_p01_package_is_prepared_but_not_authorized(self) -> None:
        p = self.package
        self.assertEqual(p["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["model_run_authorized"])
        self.assertFalse(p["model_contact_authorized"])
        self.assertFalse(p["model_contact_performed"])
        self.assertEqual(p["authorization_gate"]["current_state"], "CLOSED")
        self.assertTrue(p["authorization_gate"]["explicit_user_approval_required"])
        self.assertTrue(p["authorization_gate"]["authorization_artifact_must_be_changed_separately"])

    def test_p02_scope_is_exact_and_synthetic_only(self) -> None:
        p = self.package
        self.assertEqual(p["runner_version"], "v1.3")
        self.assertEqual(p["model"], "qwen3-14b")
        self.assertEqual(p["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")
        self.assertEqual(p["expected_model_request_count"], 16)
        self.assertEqual(p["qualified_completeness_pfs"], ["PF2", "PF9", "PF12"])
        self.assertTrue(p["non_profile_cases_boundary_only"])
        self.assertTrue(p["synthetic_only"])
        self.assertTrue(p["local_loopback_only"])
        self.assertTrue(p["single_run_only"])
        self.assertEqual(p["retry_count"], 0)
        self.assertFalse(p["output_repair"])
        self.assertFalse(p["remote_cloud"])
        self.assertFalse(p["real_data"])

    def test_p03_all_frozen_artifact_blob_bindings_match_head(self) -> None:
        for name, artifact in self.package["artifacts"].items():
            with self.subTest(artifact=name):
                self.assertEqual(git_blob_sha(artifact["path"]), artifact["git_blob_sha"])

    def test_p04_authorization_placeholder_remains_not_approved(self) -> None:
        auth = load(AUTH_PATH)
        self.assertEqual(auth["status"], "NOT_APPROVED")
        self.assertEqual(auth["runner_version"], "v1.3")
        self.assertEqual(auth["model"], "qwen3-14b")
        self.assertEqual(auth["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_6")

    def test_p05_historical_system_qualification_evidence_is_bound(self) -> None:
        first_meta = self.package["artifacts"]["system_qualification_first_fail"]
        final_meta = self.package["artifacts"]["system_qualification_final_pass"]
        first = load(ROOT / first_meta["path"])
        final = load(ROOT / final_meta["path"])

        self.assertFalse(first["qualification_passed"])
        self.assertEqual(first["passed_case_count"], 26)
        self.assertEqual(first["failed_case_count"], 3)
        self.assertFalse(first["model_contact_observed"])

        self.assertTrue(final["qualification_passed"])
        self.assertEqual(final["passed_case_count"], 29)
        self.assertEqual(final["failed_case_count"], 0)
        self.assertFalse(final["model_contact_observed"])

    def test_p06_no_downstream_approval_is_created(self) -> None:
        p = self.package
        self.assertFalse(p["model_qualified"])
        self.assertFalse(p["benchmark_approved"])
        self.assertFalse(p["generalisation_approved"])
        self.assertFalse(p["pilot_approved"])
        self.assertFalse(p["production_approved"])
        self.assertFalse(p["phase_f_approved"])


if __name__ == "__main__":
    unittest.main()
