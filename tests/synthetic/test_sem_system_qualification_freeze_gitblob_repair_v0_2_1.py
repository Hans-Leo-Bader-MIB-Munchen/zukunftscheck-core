import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from scripts.zs_ki_b_sem_system_qualification_freeze_gitblob_repair_v0_2_1 import (
    build_repair_candidate,
    canonical_sha256,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_frozen_v0_2.json"
POLICY_PATH = "tests/fixtures/zs_ki_b_sem_system_qualification_policy_candidate_v0_2.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FreezeGitBlobRepairV021Tests(unittest.TestCase):
    def setUp(self):
        self.source = load(SOURCE)
        self.repaired = build_repair_candidate(self.source)
        self.commit = self.source["approved_main_commit"]

    def test_repair_candidate_is_not_a_new_freeze_or_execution_authority(self):
        self.assertEqual(self.repaired["status"], "TECHNICAL_REPAIR_CANDIDATE")
        self.assertTrue(self.repaired["human_reapproval_required_before_replacing_frozen_manifest"])
        self.assertFalse(self.repaired["execution_authorized"])
        self.assertFalse(self.repaired["model_contact_authorized"])
        self.assertEqual(self.repaired["decision_authority"], "NONE")

    def test_repair_preserves_original_artifact_paths_and_count(self):
        old_paths = [row["path"] for row in self.source["artifacts"]]
        new_paths = [row["path"] for row in self.repaired["artifacts"]]
        self.assertEqual(new_paths, old_paths)
        self.assertEqual(len(new_paths), 9)
        self.assertFalse(self.repaired["artifact_paths_changed"])

    def test_hash_basis_is_original_approved_commit_git_blob_bytes(self):
        self.assertEqual(self.repaired["hash_basis"], "CANONICAL_GIT_BLOB_BYTES")
        self.assertEqual(self.repaired["hash_basis_commit"], self.source["approved_main_commit"])

    def test_policy_canonical_hash_matches_repository_blob_bytes(self):
        blob_sha = subprocess.check_output(
            ["git", "rev-parse", f"{self.commit}:{POLICY_PATH}"],
            cwd=ROOT,
            text=True,
        ).strip()
        blob = subprocess.check_output(["git", "cat-file", "blob", blob_sha], cwd=ROOT)
        expected = hashlib.sha256(blob).hexdigest()
        self.assertEqual(canonical_sha256(self.commit, POLICY_PATH), expected)
        self.assertEqual(expected, "43ba84a22cf2b9681f70052e468e299517e650b8cd9e92371b10218c23080d7c")

    def test_all_nine_repaired_hashes_match_canonical_git_blobs(self):
        for artifact in self.repaired["artifacts"]:
            self.assertEqual(
                artifact["sha256"],
                canonical_sha256(self.commit, artifact["path"]),
                artifact["role"],
            )

    def test_original_freeze_exposes_platform_dependent_policy_hash(self):
        original_policy = next(row for row in self.source["artifacts"] if row["role"] == "policy")
        canonical_policy = next(row for row in self.repaired["artifacts"] if row["role"] == "policy")
        self.assertEqual(original_policy["sha256"], "ff93d76aebf6e0c2179d7214e8c7cf73bfe92e40661f61b948ba39a5edd5b8fe")
        self.assertNotEqual(original_policy["sha256"], canonical_policy["sha256"])

    def test_semantic_and_model_qualification_statuses_are_not_upgraded(self):
        self.assertTrue(self.repaired["technical_repair_only"])
        self.assertFalse(self.repaired["semantic_scope_changed"])
        self.assertEqual(
            self.repaired["model_qualification_status_preserved"],
            self.source["model_qualification_status_preserved"],
        )
        self.assertEqual(
            self.repaired["guarded_system_qualification_status"],
            self.source["guarded_system_qualification_status"],
        )


if __name__ == "__main__":
    unittest.main()
