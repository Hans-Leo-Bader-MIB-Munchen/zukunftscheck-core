from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from scripts.zs_ki_b_sem_system_qualification_freeze_hash_repair_v0_2_1 import (
    FROZEN_PATHS,
    ROOT,
    SOURCE,
    build_repair_candidate,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class FreezeHashRepairV021Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = build_repair_candidate()

    def test_r01_is_repair_candidate_not_frozen(self) -> None:
        self.assertEqual(self.candidate["status"], "TECHNICAL_REPAIR_CANDIDATE")
        self.assertTrue(self.candidate["technical_repair_only"])
        self.assertTrue(self.candidate["human_reapproval_required_before_frozen_status"])

    def test_r02_source_manifest_is_bound(self) -> None:
        self.assertEqual(self.candidate["source_frozen_manifest"], SOURCE.relative_to(ROOT).as_posix())
        self.assertEqual(self.candidate["source_frozen_manifest_sha256"], sha256_file(SOURCE))

    def test_r03_policy_and_suite_use_actual_frozen_paths(self) -> None:
        paths = {row["role"]: row["path"] for row in self.candidate["artifacts"]}
        self.assertEqual(paths["policy"], FROZEN_PATHS["policy"])
        self.assertEqual(paths["suite"], FROZEN_PATHS["suite"])

    def test_r04_all_materialized_hashes_match_checked_out_bytes(self) -> None:
        for row in self.candidate["artifacts"]:
            path = ROOT / row["path"]
            self.assertEqual(row["sha256"], sha256_file(path), row["role"])

    def test_r05_no_authority_or_model_qualification_change(self) -> None:
        self.assertFalse(self.candidate["execution_authorized"])
        self.assertFalse(self.candidate["model_contact_authorized"])
        self.assertEqual(self.candidate["model_qualification_status_preserved"], "NOT_QUALIFIED")
        self.assertEqual(self.candidate["decision_authority"], "NONE")
        self.assertFalse(self.candidate["real_data_authorized"])
        self.assertFalse(self.candidate["pilot_authorized"])
        self.assertFalse(self.candidate["production_authorized"])
        self.assertFalse(self.candidate["phase_f_authorized"])

    def test_r06_artifact_roles_are_preserved(self) -> None:
        roles = [row["role"] for row in self.candidate["artifacts"]]
        self.assertEqual(len(roles), 9)
        self.assertEqual(len(set(roles)), 9)
        self.assertIn("semantic_runtime_guard", roles)
        self.assertIn("semantic_completeness_audit_pf2", roles)


if __name__ == "__main__":
    unittest.main()
