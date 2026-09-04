import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_manifest_candidate_v0_1.json"

EXPECTED_CASE_IDS = [
    "ZS-KI-B-SEM-DEVCHAL-2026-PF1-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF2-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF3-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF4-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF5-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF6-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF7-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF8-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF9-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF10-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF11-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-PF12-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-CROSS-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-CROSS-002",
    "ZS-KI-B-SEM-DEVCHAL-2026-CROSS-003",
    "ZS-KI-B-SEM-DEVCHAL-2026-CROSS-004",
    "ZS-KI-B-SEM-DEVCHAL-2026-EVIDENCE-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-EVIDENCE-002",
    "ZS-KI-B-SEM-DEVCHAL-2026-TIME-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-TIME-002",
    "ZS-KI-B-SEM-DEVCHAL-2026-SPECIFICITY-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-SPECIFICITY-002",
    "ZS-KI-B-SEM-DEVCHAL-2026-BOUNDARY-001",
    "ZS-KI-B-SEM-DEVCHAL-2026-BOUNDARY-002",
]


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentManifestCandidateV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_authorization_flags_fail_closed(self):
        m = self.manifest
        self.assertFalse(m["qualification_claim_allowed"])
        self.assertFalse(m["execution_authorized"])
        self.assertFalse(m["model_contact_authorized"])
        self.assertFalse(m["preflight_authorized"])
        self.assertFalse(m["automatic_retry_authorized"])
        self.assertFalse(m["automatic_rerun_authorized"])
        self.assertFalse(m["output_repair_authorized"])
        self.assertEqual(m["hard_stop"], "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION")

    def test_case_order_exact(self):
        self.assertEqual(self.manifest["expected_case_count"], 24)
        self.assertEqual(self.manifest["expected_model_request_count"], 24)
        self.assertEqual(self.manifest["ordered_case_ids"], EXPECTED_CASE_IDS)
        self.assertEqual(len(set(EXPECTED_CASE_IDS)), 24)

    def test_bound_blobs_exact(self):
        for name, binding in self.manifest["bindings"].items():
            path = ROOT / binding["path"]
            self.assertTrue(path.is_file(), f"missing bound artifact {name}: {path}")
            self.assertEqual(git_blob_sha1(path), binding["git_blob_sha"], f"blob mismatch: {name}")

    def test_manifest_is_prep_only(self):
        self.assertEqual(self.manifest["mode"], "DEVELOPMENT_PREP_ONLY")
        self.assertEqual(self.manifest["data_class"], "SYNTHETIC_ONLY")

    def test_no_network_or_model_runtime_code_in_test(self):
        text = Path(__file__).read_text(encoding="utf-8").lower()
        forbidden = ["requests.", "httpx", "urllib.request", "socket.", "lm studio", "localhost:", "openai("]
        for token in forbidden:
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
