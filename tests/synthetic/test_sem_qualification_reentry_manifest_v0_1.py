from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualification_reentry_manifest_v0_1 as prep


class TestSemQualificationReentryManifest(unittest.TestCase):
    def test_01_base_and_source_bindings_exact(self):
        self.assertEqual(prep.BASE_MAIN_COMMIT, "a3bdf89d4aab82e346a1bdec37285743efc993d8")
        self.assertEqual(prep.SOURCE_INTEGRITY_BLOB_SHA, "1b7d5f81995036561718885555fe793bd05c15c6")
        self.assertEqual(prep.SOURCE_V25_RUNNER_BLOB_SHA, "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866")
        prep._validate_sources_before_import()

    def test_02_frozen_supplements_are_exact_and_model_invisible(self):
        freeze = prep._validate_frozen_supplements()
        self.assertEqual(freeze["status"], "HUMAN_APPROVED_FROZEN")
        self.assertIs(freeze["model_execution_authorized"], False)
        self.assertIs(freeze["artifacts"]["human_gold"]["model_visible"], False)

    def test_03_manifest_binds_exact_16_case_snapshot(self):
        manifest = prep.build_reentry_manifest()
        self.assertEqual(manifest["qualification_case_count"], 16)
        self.assertEqual(tuple(manifest["ordered_case_ids"]), prep.integrity.EXPECTED_ORDERED_CASE_IDS)
        self.assertEqual(len(manifest["qualification_snapshot_sha256"]), 64)
        self.assertEqual(len(manifest["ordered_case_ids_sha256"]), 64)

    def test_04_manifest_binds_actual_v25_request_boundaries(self):
        manifest = prep.build_reentry_manifest()
        self.assertEqual(manifest["runtime_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(manifest["model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(manifest["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(manifest["expected_model_request_count"], 16)
        self.assertEqual(manifest["max_tokens"], 2048)
        self.assertEqual(manifest["retry_count"], 0)
        self.assertIs(manifest["output_repair"], False)

    def test_05_manifest_keeps_authorization_gate_closed_and_target_resolved(self):
        manifest = prep.build_reentry_manifest()
        self.assertEqual(manifest["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(manifest["authorization_gate"]["state"], "CLOSED")
        self.assertIs(manifest["authorization_gate"]["explicit_user_single_run_approval_required"], True)
        self.assertIs(manifest["authorization_gate"]["no_execution_from_manifest"], True)
        self.assertIs(manifest["qualification_target_decision_required"], False)
        self.assertEqual(manifest["qualification_target_binding_source"], "EXISTING_V19_V25_RUNNER_BINDING")
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "model_qualified", "benchmark_approved",
            "pilot_approved", "production_approved",
        ):
            self.assertIs(manifest[key], False, key)

    def test_06_manifest_preserves_human_gold_outside_model_view(self):
        manifest = prep.build_reentry_manifest()
        self.assertEqual(manifest["human_gold"]["git_blob_sha"], prep.EXPECTED_HUMAN_GOLD_BLOB_SHA)
        self.assertIs(manifest["human_gold"]["model_visible"], False)
        self.assertEqual(manifest["human_gold_evaluation"], "NOT_STARTED")
        self.assertIs(manifest["human_review_required_after_run"], True)

    def test_07_residual_architecture_issue_remains_bound(self):
        manifest = prep.build_reentry_manifest()
        self.assertEqual(manifest["residual_architecture_issue"], 130)

    def test_08_manifest_hash_is_deterministic(self):
        first = prep.build_reentry_manifest()
        second = prep.build_reentry_manifest()
        self.assertEqual(first, second)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_09_tampered_manifest_rejected_even_with_recomputed_hash(self):
        manifest = prep.build_reentry_manifest()
        tampered = copy.deepcopy(manifest)
        tampered["runtime_model_id"] = "attacker-model"
        unsigned = dict(tampered)
        unsigned.pop("manifest_sha256")
        tampered["manifest_sha256"] = prep._stable_sha256(unsigned)
        with self.assertRaises(PermissionError):
            prep.validate_reentry_manifest(tampered)

    def test_10_changed_v25_boundary_fails_closed(self):
        with patch.object(prep.v25, "MAX_TOKENS", 4096):
            with self.assertRaises(PermissionError):
                prep.build_reentry_manifest()

    def test_11_changed_loopback_binding_fails_closed(self):
        with patch.object(prep.v25, "BASE_URL", "https://example.invalid/v1"):
            with self.assertRaises(PermissionError):
                prep.build_reentry_manifest()

    def test_12_report_is_model_free_not_authorized_and_target_resolved(self):
        report = prep.build_report()
        self.assertEqual(report["mode"], "MODEL_FREE_QUALIFICATION_REENTRY_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertIs(report["qualification_target_decision_required"], False)
        self.assertEqual(report["qualification_target_binding_source"], "EXISTING_V19_V25_RUNNER_BINDING")
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "model_qualified",
        ):
            self.assertIs(report[key], False, key)

    def test_13_script_contains_no_execution_or_transport_entrypoint(self):
        names = set(vars(prep))
        self.assertNotIn("execute_once", names)
        self.assertNotIn("_default_transport", names)
        self.assertNotIn("_default_preflight", names)
        self.assertNotIn("materialize_live_authorization", names)


if __name__ == "__main__":
    unittest.main()
