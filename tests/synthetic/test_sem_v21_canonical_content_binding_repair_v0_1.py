from __future__ import annotations

import copy
import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep as prep
import scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 as integrity


class V21CanonicalContentBindingRepairV01Tests(unittest.TestCase):
    def _approved_auth(self):
        auth = prep.build_authorization_template()
        auth.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        return auth

    def test_authorization_template_binds_all_required_semantic_artifacts(self):
        template = prep.build_authorization_template()
        roles = {row["role"] for row in template["bound_artifacts"]}
        self.assertEqual(
            roles,
            {
                "qualification_suite",
                "reference_questions",
                "reference_question_meanings",
                "finding_type_meanings",
                "system_prompt",
                "response_schema",
            },
        )
        for row in template["bound_artifacts"]:
            self.assertEqual(len(row["canonical_sha256"]), 64)
            self.assertEqual(len(row["git_blob_oid"]), 40)

    def test_authorization_template_binds_exact_case_identity_and_order(self):
        template = prep.build_authorization_template()
        self.assertEqual(tuple(template["ordered_case_ids"]), integrity.EXPECTED_ORDERED_CASE_IDS)
        self.assertEqual(len(template["ordered_case_ids"]), 16)
        self.assertEqual(len(template["ordered_case_ids_sha256"]), 64)

    def test_same_count_but_different_content_binding_is_rejected(self):
        auth = self._approved_auth()
        tampered = copy.deepcopy(auth)
        tampered["bound_artifacts"][0]["canonical_sha256"] = "0" * 64
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization(tampered)

    def test_same_cases_but_other_order_is_rejected(self):
        auth = self._approved_auth()
        reordered = copy.deepcopy(auth)
        reordered["ordered_case_ids"][0], reordered["ordered_case_ids"][1] = (
            reordered["ordered_case_ids"][1],
            reordered["ordered_case_ids"][0],
        )
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization(reordered)

    def test_source_commit_and_composed_snapshot_are_authorization_fields(self):
        template = prep.build_authorization_template()
        self.assertEqual(template["source_base_commit"], integrity.SOURCE_BASE_COMMIT)
        self.assertEqual(template["hash_semantics"], integrity.HASH_SEMANTICS)
        self.assertEqual(len(template["qualification_snapshot_sha256"]), 64)

    def test_model_free_report_remains_non_authorizing(self):
        report = prep.build_authorization_report()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["authorization_binding_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertFalse(report["model_qualified"])


if __name__ == "__main__":
    unittest.main()
