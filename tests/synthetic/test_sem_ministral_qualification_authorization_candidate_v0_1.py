from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_authorization_candidate_v0_1 as prep


class TestSemMinistralQualificationAuthorizationCandidate(unittest.TestCase):
    def test_01_exact_prep_base_and_source_bindings(self):
        self.assertEqual(prep.PREP_BASE_MAIN_COMMIT, "5dd6054ec30a531d9e53dfb1a1697bfd41c0edfc")
        self.assertEqual(prep.PRERUN_BLOB_SHA, "0a958fb7abba8d6421f1fb4c58b547a2afff8012")
        self.assertEqual(prep.V26_BLOB_SHA, "f37da460593eec98c56a847188c13308a86c769d")
        prep._validate_sources_before_import()

    def test_02_candidate_awaits_explicit_approval(self):
        candidate = prep.build_authorization_candidate()
        self.assertEqual(candidate["status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertTrue(candidate["approval_required"])
        self.assertTrue(candidate["explicit_user_single_run_approval_required"])
        self.assertTrue(candidate["single_use_only"])

    def test_03_candidate_is_not_authorized_or_consumed(self):
        candidate = prep.build_authorization_candidate()
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "authorization_consumed", "model_qualified",
        ):
            self.assertIs(candidate[key], False, key)

    def test_04_no_approval_artifact_or_proof_materialized(self):
        candidate = prep.build_authorization_candidate()
        self.assertTrue(candidate["separate_approval_artifact_required"])
        self.assertFalse(candidate["approval_artifact_materialized"])
        self.assertFalse(candidate["approval_proof_present"])
        self.assertFalse(candidate["authorization_persisted"])

    def test_05_exact_ministral_and_request_binding(self):
        candidate = prep.build_authorization_candidate()
        self.assertEqual(candidate["runtime_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(candidate["model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(candidate["expected_model_request_count"], 16)
        self.assertEqual(candidate["max_tokens"], 2048)
        self.assertFalse(candidate["output_repair"])
        self.assertFalse(candidate["automatic_retry_authorized"])
        self.assertFalse(candidate["automatic_rerun_authorized"])

    def test_06_exact_prerun_binding(self):
        candidate = prep.build_authorization_candidate()
        bound = candidate["bound_prerun_package"]
        package = prep.prerun.build_prerun_package()
        self.assertEqual(bound["git_blob_sha"], prep.PRERUN_BLOB_SHA)
        self.assertEqual(bound["package_sha256"], package["prerun_package_sha256"])
        self.assertEqual(bound["package_version"], package["prerun_package_version"])
        self.assertEqual(bound["run_type"], package["run_type"])
        self.assertEqual(bound["qualification_snapshot_sha256"], package["qualification_snapshot_sha256"])
        self.assertEqual(bound["ordered_case_ids_sha256"], package["ordered_case_ids_sha256"])

    def test_07_candidate_only_runner_sentinels_are_retained(self):
        candidate = prep.build_authorization_candidate()
        self.assertEqual(candidate["live_runner_version"], prep.v26.CANDIDATE_ONLY_LIVE_RUNNER_VERSION)
        self.assertEqual(candidate["live_run_type"], prep.v26.CANDIDATE_ONLY_LIVE_RUN_TYPE)
        self.assertEqual(candidate["bound_v25_live_runner_version"], prep.v26.v25.RUNNER_VERSION)
        self.assertEqual(candidate["bound_v25_live_run_type"], prep.v26.v25.RUN_TYPE)

    def test_08_direct_status_escalation_is_rejected_by_v25(self):
        candidate = prep.build_authorization_candidate()
        self.assertTrue(prep.direct_status_escalation_rejected_by_v25(candidate))

    def test_09_candidate_hash_is_deterministic(self):
        first = prep.build_authorization_candidate()
        second = prep.build_authorization_candidate()
        self.assertEqual(first, second)
        self.assertEqual(first["authorization_candidate_sha256"], prep.candidate_sha256(first))

    def test_10_tampered_candidate_rejected_even_with_recomputed_hash(self):
        candidate = prep.build_authorization_candidate()
        tampered = copy.deepcopy(candidate)
        tampered["max_tokens"] = 4096
        tampered["authorization_candidate_sha256"] = prep.candidate_sha256(tampered)
        with self.assertRaises(PermissionError):
            prep.validate_authorization_candidate(tampered)

    def test_11_status_or_flags_cannot_be_silently_changed(self):
        candidate = prep.build_authorization_candidate()
        for key, value in (
            ("status", "EXPLICIT_USER_APPROVED"),
            ("execution_authorized", True),
            ("model_run_authorized", True),
            ("model_contact_authorized", True),
        ):
            tampered = copy.deepcopy(candidate)
            tampered[key] = value
            tampered["authorization_candidate_sha256"] = prep.candidate_sha256(tampered)
            with self.assertRaises(PermissionError, msg=key):
                prep.validate_authorization_candidate(tampered)

    def test_12_changed_prerun_boundary_fails_closed(self):
        with patch.object(prep.prerun, "EXPECTED_RUNTIME_MODEL_ID", "other-model"):
            with self.assertRaises(PermissionError):
                prep.build_authorization_candidate()

    def test_13_source_worktree_mismatch_fails_closed(self):
        original = prep._text_blob_sha1

        def fake(path):
            if path.name == Path(prep.V26_PATH).name:
                return "0" * 40
            return original(path)

        with patch.object(prep, "_text_blob_sha1", side_effect=fake):
            with self.assertRaises(PermissionError):
                prep.build_authorization_candidate()

    def test_14_product_and_real_data_flags_remain_false(self):
        candidate = prep.build_authorization_candidate()
        for key in ("benchmark_approved", "real_data", "pilot_approved", "production_approved"):
            self.assertIs(candidate[key], False, key)

    def test_15_report_is_model_free_and_not_ready_for_approval_execution(self):
        report = prep.build_report()
        self.assertEqual(report["mode"], "MODEL_FREE_MINISTRAL_QUALIFICATION_AUTHORIZATION_CANDIDATE_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["governance_status"], "AWAITING_EXPLICIT_USER_APPROVAL")
        self.assertFalse(report["ready_for_explicit_user_approval"])
        self.assertFalse(report["approval_artifact_materialized"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_consumed"])
        self.assertFalse(report["model_qualified"])

    def test_16_module_has_no_execution_transport_or_approval_materialization_entrypoint(self):
        names = set(vars(prep))
        for forbidden in (
            "execute_once", "_default_transport", "_default_preflight",
            "materialize_live_authorization", "build_approval_artifact",
            "consume_authorization", "persist_authorization",
        ):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
