import json
import unittest
from pathlib import Path

from scripts.zs_ki_b_sem_system_qualification_freeze_gitblob_repair_v0_2_1 import canonical_sha256

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_frozen_v0_2.json"
REPAIR_CANDIDATE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_gitblob_repair_candidate_v0_2_1.json"
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_policy_frozen_v0_2.json"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_suite_frozen_v0_2.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FinalFreezeV02Tests(unittest.TestCase):
    def setUp(self):
        self.manifest = load(MANIFEST)
        self.repair = load(REPAIR_CANDIDATE)
        self.policy = load(POLICY)
        self.suite = load(SUITE)

    def test_statuses(self):
        self.assertEqual(self.manifest["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(self.policy["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(self.suite["status"], "HUMAN_APPROVED_FROZEN")
        self.assertEqual(self.repair["status"], "TECHNICAL_REPAIR_CANDIDATE")
        self.assertTrue(self.repair["human_reapproval_required_before_replacing_frozen_manifest"])

    def test_hashes(self):
        # The original frozen manifest retains its historical approval record and
        # platform-dependent worktree hashes. Cross-platform integrity is verified
        # against the already prepared Git-blob repair candidate without silently
        # promoting that candidate to a new HUMAN_APPROVED_FROZEN manifest.
        self.assertEqual(self.repair["repair_of"], self.manifest["freeze_version"])
        self.assertEqual(self.repair["hash_basis"], "CANONICAL_GIT_BLOB_BYTES")
        commit = self.repair["hash_basis_commit"]
        for artifact in self.repair["artifacts"]:
            self.assertEqual(
                canonical_sha256(commit, artifact["path"]),
                artifact["sha256"],
                artifact["role"],
            )

    def test_case_count(self):
        self.assertEqual(self.manifest["system_case_count"], 29)
        self.assertEqual(self.suite["case_count"], 29)
        self.assertEqual(len(self.suite["cases"]), 29)

    def test_guard_bindings(self):
        paths = {x["role"]: x["path"] for x in self.manifest["artifacts"]}
        self.assertEqual(paths["semantic_runtime_guard"], "core/validation/semantic_runtime_guard_v0_2.py")
        self.assertEqual(paths["semantic_completeness_audit_pf2"], "core/validation/semantic_completeness_audit_v0_2.py")

    def test_no_execution_authority(self):
        for obj in (self.manifest, self.policy, self.suite, self.repair):
            self.assertFalse(obj["execution_authorized"])
            self.assertFalse(obj["model_contact_authorized"])
        self.assertEqual(self.manifest["model_qualification_status_preserved"], "NOT_QUALIFIED")
        self.assertEqual(self.manifest["guarded_system_qualification_status"], "NOT_YET_EXECUTED")

    def test_generic_composition_still_open(self):
        self.assertEqual(self.manifest["generic_v0_2_system_composition_status"], "NOT_YET_IMPLEMENTED")
        self.assertEqual(self.policy["component_composition_boundary"]["generic_v0_2_system_composition_status"], "NOT_YET_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
