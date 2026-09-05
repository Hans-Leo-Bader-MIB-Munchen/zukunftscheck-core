import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREP_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_authorization_prep_candidate_v0_3.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentAuthorizationPrepCandidateV03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = json.loads(PREP_PATH.read_text(encoding="utf-8"))

    def test_all_authorization_flags_remain_false(self):
        for key in (
            "qualification_claim_allowed",
            "execution_authorized",
            "model_contact_authorized",
            "preflight_authorized",
            "automatic_retry_authorized",
            "automatic_rerun_authorized",
            "output_repair_authorized",
            "ready_for_user_approval",
        ):
            self.assertIs(self.prep[key], False, key)

    def test_live_runner_and_static_test_are_blob_bound(self):
        for key in ("bound_live_runner_candidate", "bound_live_runner_static_test"):
            record = self.prep[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], key)

    def test_prior_prep_runtime_cases_and_gold_remain_bound(self):
        for key in (
            "bound_prep_v0_2",
            "bound_runtime_binding_candidate",
            "bound_machine_readable_challenges",
            "bound_machine_readable_development_gold",
        ):
            record = self.prep[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], key)

    def test_preflight_is_mandatory_but_not_yet_bound(self):
        p = self.prep["preflight_requirement"]
        self.assertIs(p["required_before_live_execution"], True)
        self.assertEqual(p["required_status"], "PASS_FROZEN")
        self.assertEqual(p["required_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(p["required_loaded_context_min"], 32768)
        self.assertIs(p["preflight_result_bound"], False)
        self.assertIs(p["preflight_authorization_bound"], False)

    def test_state_is_not_ready_for_user_approval(self):
        self.assertEqual(
            self.prep["runtime_parameter_state"],
            "LIVE_RUNNER_BOUND_AWAITING_PREFLIGHT_ARCHITECTURE_AND_STATIC_COUNTERCHECK",
        )
        self.assertEqual(self.prep["expected_run_count"], 1)
        self.assertEqual(self.prep["expected_case_count"], 24)
        self.assertEqual(self.prep["expected_model_request_count"], 24)
        self.assertEqual(self.prep["hard_stop"], "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION")


if __name__ == "__main__":
    unittest.main()
