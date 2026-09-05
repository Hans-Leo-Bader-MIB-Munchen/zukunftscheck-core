import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREP_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_authorization_prep_candidate_v0_1.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentAuthorizationPrepCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = json.loads(PREP_PATH.read_text(encoding="utf-8"))

    def test_status_is_awaiting_explicit_user_approval(self):
        self.assertEqual(self.prep["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertEqual(self.prep["mode"], "DEVELOPMENT_AUTHORIZATION_PREP_ONLY")
        self.assertEqual(self.prep["data_class"], "SYNTHETIC_ONLY")

    def test_all_authorization_flags_remain_false(self):
        for key in (
            "qualification_claim_allowed",
            "execution_authorized",
            "model_contact_authorized",
            "preflight_authorized",
            "automatic_retry_authorized",
            "automatic_rerun_authorized",
            "output_repair_authorized",
        ):
            self.assertIs(self.prep[key], False, key)

    def test_prep_freeze_and_final_countercheck_are_exactly_bound(self):
        for key in ("bound_prep_freeze", "bound_final_static_countercheck"):
            record = self.prep[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), f"missing bound artifact: {key}")
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], f"blob mismatch: {key}")

    def test_runtime_parameters_are_unbound_and_not_ready_for_approval(self):
        self.assertEqual(self.prep["runtime_parameter_state"], "UNBOUND_NOT_READY_FOR_APPROVAL")
        params = self.prep["runtime_parameters"]
        self.assertEqual(
            set(params),
            {"model_id", "adapter_version", "endpoint", "max_tokens", "temperature", "structured_output_runtime_config"},
        )
        self.assertTrue(all(value is None for value in params.values()))

    def test_scope_is_exactly_one_synthetic_development_run_after_separate_approval(self):
        self.assertEqual(self.prep["expected_run_count"], 1)
        self.assertEqual(self.prep["expected_case_count"], 24)
        self.assertEqual(self.prep["expected_model_request_count"], 24)
        self.assertEqual(
            self.prep["authorization_scope"],
            "ONE_SYNTHETIC_DEVELOPMENT_RUN_ONLY_IF_SEPARATELY_EXPLICITLY_APPROVED",
        )

    def test_hard_stop_and_case_order_hash_are_preserved(self):
        self.assertEqual(
            self.prep["hard_stop"],
            "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION",
        )
        self.assertEqual(
            self.prep["ordered_case_ids_sha256"],
            "b02bc870f83c322cd000f47e2000a1e17617f465293afb990ff949f534c6b2e8",
        )


if __name__ == "__main__":
    unittest.main()
