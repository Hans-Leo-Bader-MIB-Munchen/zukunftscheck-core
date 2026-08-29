from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 import (
    ARTIFACT_PATHS,
    EXPECTED_ORDERED_CASE_IDS,
    HASH_SEMANTICS,
    ROOT,
    SOURCE_BASE_COMMIT,
    _ordered_case_ids_from_bytes,
    build_binding_snapshot,
    build_integrity_report,
    canonical_sha256_bytes,
    canonical_worktree_sha256,
    validate_execution_authorization,
)


class CanonicalBindingIntegrityV01Tests(unittest.TestCase):
    def test_lf_and_crlf_have_identical_canonical_hash(self):
        lf = b'{\n  "a": 1,\n  "b": 2\n}\n'
        crlf = lf.replace(b"\n", b"\r\n")
        self.assertEqual(canonical_sha256_bytes(lf), canonical_sha256_bytes(crlf))

    def test_content_change_changes_canonical_hash(self):
        first = b'{\n  "value": "alpha"\n}\n'
        second = b'{\n  "value": "beta"\n}\n'
        self.assertNotEqual(canonical_sha256_bytes(first), canonical_sha256_bytes(second))

    def test_required_artifacts_are_content_bound(self):
        snapshot = build_binding_snapshot()
        by_role = {row["role"]: row for row in snapshot["artifacts"]}
        self.assertEqual(
            set(by_role),
            {
                "qualification_suite",
                "reference_questions",
                "reference_question_meanings",
                "finding_type_meanings",
                "system_prompt",
                "response_schema",
            },
        )
        for row in by_role.values():
            self.assertEqual(len(row["canonical_sha256"]), 64)
            self.assertEqual(len(row["git_blob_oid"]), 40)

    def test_same_case_count_but_changed_suite_content_fails_hash_binding(self):
        snapshot = build_binding_snapshot()
        suite_binding = next(row for row in snapshot["artifacts"] if row["role"] == "qualification_suite")
        suite_path = ROOT / dict(ARTIFACT_PATHS)["qualification_suite"]
        original = suite_path.read_bytes()
        changed = original.replace(
            "Den Auftrag für die Orientierungsprüfung erteilt die Gemeinde Beispielstadt.".encode("utf-8"),
            "Den Auftrag für die Orientierungsprüfung erteilt die Gemeinde Musterstadt.".encode("utf-8"),
            1,
        )
        self.assertEqual(len(_ordered_case_ids_from_bytes(changed)), 16)
        self.assertNotEqual(canonical_sha256_bytes(changed), suite_binding["canonical_sha256"])

    def test_same_16_cases_in_other_order_fail_order_binding(self):
        suite_path = ROOT / dict(ARTIFACT_PATHS)["qualification_suite"]
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
        self.assertEqual(tuple(case["case_id"] for case in suite["cases"]), EXPECTED_ORDERED_CASE_IDS)
        suite["cases"][0], suite["cases"][1] = suite["cases"][1], suite["cases"][0]
        mutated = (json.dumps(suite, ensure_ascii=False) + "\n").encode("utf-8")
        reordered = _ordered_case_ids_from_bytes(mutated)
        self.assertEqual(len(reordered), 16)
        self.assertCountEqual(reordered, EXPECTED_ORDERED_CASE_IDS)
        self.assertNotEqual(reordered, EXPECTED_ORDERED_CASE_IDS)

    def test_worktree_hash_is_platform_independent_for_text_checkout(self):
        payload = "Größe\nZeile 2\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            lf_path = Path(tmp) / "lf.txt"
            crlf_path = Path(tmp) / "crlf.txt"
            lf_path.write_bytes(payload)
            crlf_path.write_bytes(payload.replace(b"\n", b"\r\n"))
            self.assertEqual(canonical_worktree_sha256(lf_path), canonical_worktree_sha256(crlf_path))

    def test_snapshot_binds_source_commit_runners_and_ordered_cases(self):
        snapshot = build_binding_snapshot()
        self.assertEqual(snapshot["source_base_commit"], SOURCE_BASE_COMMIT)
        self.assertEqual(snapshot["hash_semantics"], HASH_SEMANTICS)
        self.assertEqual(tuple(snapshot["ordered_case_ids"]), EXPECTED_ORDERED_CASE_IDS)
        self.assertEqual(len(snapshot["ordered_case_ids"]), 16)
        self.assertEqual(len(snapshot["ordered_case_ids_sha256"]), 64)
        self.assertEqual(len(snapshot["qualification_snapshot_sha256"]), 64)
        self.assertEqual(
            {row["role"] for row in snapshot["runner_bindings"]},
            {"authorization_prep_v21", "persistent_consumption_prep_v22"},
        )

    def test_current_repository_binding_is_exact_and_model_free(self):
        report = build_integrity_report()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["binding_ready_for_future_single_use_authorization"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_authorized"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertFalse(report["model_qualified"])

    def test_no_execution_authorization_can_be_created(self):
        with self.assertRaises(PermissionError):
            validate_execution_authorization()


if __name__ == "__main__":
    unittest.main()
