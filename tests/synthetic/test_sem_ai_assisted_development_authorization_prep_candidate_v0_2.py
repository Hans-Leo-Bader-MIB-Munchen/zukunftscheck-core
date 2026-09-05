import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_authorization_prep_candidate_v0_2.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentAuthorizationPrepCandidateV02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = json.loads(PREP.read_text(encoding="utf-8"))

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

    def test_runtime_and_machine_fixtures_are_blob_bound(self):
        for key in (
            "bound_prep_freeze",
            "bound_final_static_countercheck",
            "bound_runtime_binding_candidate",
            "bound_machine_readable_challenges",
            "bound_machine_readable_development_gold",
        ):
            record = self.prep[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], key)

    def test_runtime_parameters_are_concrete_and_fail_closed(self):
        p = self.prep["runtime_parameters"]
        self.assertEqual(p["model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(p["endpoint_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(p["endpoint_path"], "/chat/completions")
        self.assertEqual(p["max_tokens"], 2048)
        self.assertEqual(p["temperature"], 0.0)
        self.assertIs(p["stream"], False)
        self.assertEqual(p["retry_count"], 0)
        self.assertIs(p["output_repair"], False)
        self.assertEqual(p["structured_output_runtime_config"]["type"], "json_schema")
        self.assertIs(p["structured_output_runtime_config"]["strict"], True)

    def test_not_ready_until_live_runner_and_preflight_architecture_resolved(self):
        self.assertEqual(
            self.prep["runtime_parameter_state"],
            "BOUND_AWAITING_LIVE_RUNNER_AND_PREFLIGHT_ARCHITECTURE",
        )
        requirements = set(self.prep["approval_requirements"])
        self.assertIn("live_execution_runner_candidate_must_be_created_and_blob_bound", requirements)
        self.assertIn("preflight_architecture_must_be_explicitly_resolved_before_ready_for_user_approval", requirements)

    def test_scope_remains_exactly_one_24_request_development_run(self):
        self.assertEqual(self.prep["expected_run_count"], 1)
        self.assertEqual(self.prep["expected_case_count"], 24)
        self.assertEqual(self.prep["expected_model_request_count"], 24)
        self.assertEqual(
            self.prep["authorization_scope"],
            "ONE_SYNTHETIC_DEVELOPMENT_RUN_ONLY_IF_SEPARATELY_EXPLICITLY_APPROVED",
        )


if __name__ == "__main__":
    unittest.main()
