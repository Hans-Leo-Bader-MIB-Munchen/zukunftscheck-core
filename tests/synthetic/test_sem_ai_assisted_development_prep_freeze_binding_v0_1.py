import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BINDING_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_prep_freeze_binding_v0_1.json"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class TestSemAiAssistedDevelopmentPrepFreezeBindingV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def test_freeze_binding_is_fail_closed(self):
        b = self.binding
        self.assertEqual(b["status"], "STATIC_PREP_BINDING_ONLY")
        self.assertFalse(b["execution_authorized"])
        self.assertFalse(b["model_contact_authorized"])
        self.assertFalse(b["preflight_authorized"])
        self.assertFalse(b["qualification_claim_allowed"])
        self.assertEqual(b["hard_stop"], "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION")

    def test_manifest_and_runner_are_externally_bound(self):
        self.assertIn("manifest_candidate", self.binding["bindings"])
        self.assertIn("runner_candidate", self.binding["bindings"])
        for name, record in self.binding["bindings"].items():
            path = ROOT / record["path"]
            self.assertTrue(path.is_file(), f"missing freeze-bound artifact: {name}")
            self.assertEqual(git_blob_sha1(path), record["git_blob_sha"], f"freeze blob mismatch: {name}")

    def test_case_order_hash_is_bound(self):
        self.assertEqual(
            self.binding["ordered_case_ids_sha256"],
            "b02bc870f83c322cd000f47e2000a1e17617f465293afb990ff949f534c6b2e8",
        )


if __name__ == "__main__":
    unittest.main()
