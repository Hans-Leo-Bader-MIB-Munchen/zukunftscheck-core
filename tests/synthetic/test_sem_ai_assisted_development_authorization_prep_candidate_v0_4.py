import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREP_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_authorization_prep_candidate_v0_4.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentAuthorizationPrepCandidateV04(unittest.TestCase):
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

    def test_all_new_preflight_bindings_are_blob_exact(self):
        for key in (
            "bound_prep_v0_3",
            "bound_live_runner_candidate",
            "bound_preflight_only_candidate",
            "bound_preflight_static_test",
            "bound_preflight_authorization_prep",
        ):
            record = self.prep[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], key)

    def test_preflight_is_zero_generation_and_separate(self):
        requirement = self.prep["preflight_requirement"]
        self.assertTrue(requirement["separate_explicit_preflight_authorization_required"])
        self.assertEqual(requirement["expected_preflight_run_count"], 1)
        self.assertEqual(requirement["expected_generation_request_count"], 0)
        self.assertEqual(requirement["required_frozen_result_status_before_development_run"], "PASS_FROZEN")
        self.assertFalse(requirement["preflight_result_bound"])

    def test_runtime_identity_requirements_are_exact(self):
        requirement = self.prep["preflight_requirement"]
        self.assertEqual(requirement["required_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(requirement["required_model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(requirement["required_quantization"], "Q4_K_M")
        self.assertEqual(requirement["required_loaded_context_min"], 32768)

    def test_state_is_still_countercheck_only(self):
        self.assertEqual(
            self.prep["runtime_parameter_state"],
            "LIVE_RUNNER_AND_PREFLIGHT_ARCHITECTURE_BOUND_AWAITING_STATIC_COUNTERCHECK",
        )
        self.assertIn("frozen_preflight_PASS_required_before_separate_development_run_authorization", self.prep["approval_requirements"])
        self.assertEqual(self.prep["hard_stop"], "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION")


if __name__ == "__main__":
    unittest.main()
