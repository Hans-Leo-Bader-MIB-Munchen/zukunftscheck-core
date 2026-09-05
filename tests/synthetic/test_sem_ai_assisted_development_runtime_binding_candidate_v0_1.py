import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BINDING_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_runtime_binding_candidate_v0_1.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentRuntimeBindingCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def test_runtime_binding_is_model_free_and_fail_closed(self):
        b = self.binding
        self.assertEqual(b["status"], "RUNTIME_BOUND_AWAITING_STATIC_VALIDATION")
        self.assertEqual(b["mode"], "MODEL_FREE_RUNTIME_BINDING_PREP_ONLY")
        self.assertFalse(b["execution_authorized"])
        self.assertFalse(b["model_contact_authorized"])
        self.assertFalse(b["preflight_authorized"])
        self.assertFalse(b["qualification_claim_allowed"])
        self.assertFalse(b["ready_for_user_approval"])

    def test_exact_runtime_parameters(self):
        p = self.binding["runtime_parameters"]
        self.assertEqual(p["model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(p["model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(p["quantization"], "Q4_K_M")
        self.assertEqual(p["adapter_version"], "LM_STUDIO_OPENAI_COMPATIBLE_CHAT_COMPLETIONS_V1")
        self.assertEqual(p["endpoint_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(p["endpoint_path"], "/chat/completions")
        self.assertEqual(p["max_tokens"], 2048)
        self.assertEqual(p["temperature"], 0.0)
        self.assertIs(p["stream"], False)
        self.assertEqual(p["request_timeout_seconds"], 1800.0)
        self.assertEqual(p["retry_count"], 0)
        self.assertIs(p["output_repair"], False)
        self.assertEqual(p["required_loaded_context_min"], 32768)

    def test_strict_structured_output_contract_is_blob_bound(self):
        cfg = self.binding["runtime_parameters"]["structured_output_runtime_config"]
        self.assertEqual(cfg["type"], "json_schema")
        self.assertIs(cfg["strict"], True)
        path = ROOT / cfg["schema_path"]
        self.assertTrue(path.is_file())
        self.assertEqual(git_blob_sha1(path), cfg["schema_git_blob_sha"])
        self.assertEqual(cfg["contract_version"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate")

    def test_prompt_and_prep_freeze_are_exactly_bound(self):
        for key in ("prompt_binding", "bound_prep_freeze"):
            record = self.binding[key]
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), key)
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], key)

    def test_run_scope_and_no_retry_repair_are_preserved(self):
        self.assertEqual(self.binding["expected_run_count"], 1)
        self.assertEqual(self.binding["expected_case_count"], 24)
        self.assertEqual(self.binding["expected_model_request_count"], 24)
        self.assertEqual(self.binding["preflight_generation_request_count"], 0)
        self.assertFalse(self.binding["automatic_retry_authorized"])
        self.assertFalse(self.binding["automatic_rerun_authorized"])
        self.assertFalse(self.binding["output_repair_authorized"])

    def test_state_requires_static_countercheck_before_approval(self):
        self.assertEqual(self.binding["runtime_parameter_state"], "BOUND_AWAITING_STATIC_COUNTERCHECK")
        self.assertIn(
            "independent_static_countercheck_required_before_ready_for_user_approval",
            self.binding["approval_requirements"],
        )
        self.assertEqual(
            self.binding["hard_stop"],
            "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION",
        )


if __name__ == "__main__":
    unittest.main()
