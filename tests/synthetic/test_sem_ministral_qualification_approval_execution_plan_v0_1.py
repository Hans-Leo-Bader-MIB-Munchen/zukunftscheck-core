from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1 as prep


class TestSemMinistralQualificationApprovalExecutionPlan(unittest.TestCase):
    def test_01_exact_base_and_candidate_binding(self):
        self.assertEqual(prep.BASE_MAIN_COMMIT, "06e286caaf396e17dc1b8ec44378883f4a17ffb1")
        self.assertEqual(prep.CANDIDATE_BLOB_SHA, "edaad6ff363010af5da5103f314df9f336f9c045")
        prep._validate_candidate_source_before_import()

    def test_02_plan_is_prepared_not_authorized(self):
        plan = prep.build_approval_execution_plan()
        self.assertEqual(plan["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(plan["approval_ceremony_state"], "NOT_STARTED")
        self.assertTrue(plan["no_execution_from_plan"])

    def test_03_exact_ministral_and_request_limits(self):
        plan = prep.build_approval_execution_plan()
        self.assertEqual(plan["runtime_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(plan["model_repository"], "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(plan["expected_model_request_count"], 16)
        self.assertEqual(plan["max_tokens"], 2048)
        self.assertEqual(plan["retry_count"], 0)
        self.assertFalse(plan["output_repair"])

    def test_04_candidate_and_prerun_hashes_are_bound(self):
        plan = prep.build_approval_execution_plan()
        candidate = prep.candidate_prep.build_authorization_candidate()
        self.assertEqual(plan["bound_candidate"]["candidate_sha256"], candidate["authorization_candidate_sha256"])
        self.assertEqual(plan["bound_candidate"]["prerun_package_sha256"], candidate["bound_prerun_package"]["package_sha256"])
        self.assertEqual(plan["bound_candidate"]["qualification_snapshot_sha256"], candidate["bound_prerun_package"]["qualification_snapshot_sha256"])
        self.assertEqual(plan["bound_candidate"]["ordered_case_ids_sha256"], candidate["bound_prerun_package"]["ordered_case_ids_sha256"])

    def test_05_required_sequence_is_exact_and_ordered(self):
        plan = prep.build_approval_execution_plan()
        expected = [
            "EXPLICIT_USER_SINGLE_RUN_APPROVAL",
            "GENERATE_EXTERNAL_APPROVAL_SECRET",
            "BUILD_AND_PERSIST_EXACT_GATE_CHALLENGE_ONCE",
            "MATERIALIZE_AND_VALIDATE_EXACT_APPROVAL_PROOF",
            "ATOMIC_SINGLE_USE_GATE_CLAIM",
            "RUN_AUTHORIZATION_TRANSFORM_AND_PROOF_ENFORCING_GATE",
            "ATOMIC_AUTHORIZATION_CONSUMPTION_BEFORE_FIRST_POSSIBLE_MODEL_CONTACT",
            "EXACTLY_16_MODEL_REQUESTS_OR_FAIL_CLOSED",
            "NO_RETRY_NO_REPAIR_NO_AUTOMATIC_RERUN",
            "HUMAN_GOLD_REVIEW_BEFORE_QUALIFICATION_DECISION",
        ]
        self.assertEqual(plan["required_sequence"], expected)

    def test_06_no_approval_state_has_started(self):
        plan = prep.build_approval_execution_plan()
        for key in (
            "explicit_user_approval_recorded", "approval_secret_generated", "challenge_persisted",
            "approval_proof_materialized", "gate_claim_persisted", "run_authorization_materialized",
            "authorization_persisted", "authorization_consumed", "ready_for_model_contact",
        ):
            self.assertIs(plan[key], False, key)

    def test_07_all_authority_and_product_flags_remain_false(self):
        plan = prep.build_approval_execution_plan()
        for key in (
            "execution_authorized", "model_run_authorized", "model_contact_authorized",
            "model_contact_performed", "model_qualified", "benchmark_approved",
            "real_data", "pilot_approved", "production_approved",
        ):
            self.assertIs(plan[key], False, key)

    def test_08_consumption_boundary_is_explicit(self):
        plan = prep.build_approval_execution_plan()
        self.assertTrue(plan["authorization_must_be_consumed_before_first_possible_model_contact"])
        self.assertTrue(plan["single_use_only"])

    def test_09_candidate_cannot_be_silently_escalated(self):
        candidate = prep.candidate_prep.build_authorization_candidate()
        self.assertTrue(prep.candidate_prep.direct_status_escalation_rejected_by_v25(candidate))

    def test_10_gate_and_transform_primitives_are_available_but_not_invoked(self):
        plan = prep.build_approval_execution_plan()
        self.assertTrue(plan["v28_atomic_claim_primitive_available"])
        self.assertTrue(plan["v29_transform_preview_available"])

    def test_11_all_approval_execution_sources_are_exactly_bound(self):
        plan = prep.build_approval_execution_plan()
        bindings = {item["role"]: item for item in plan["source_bindings"]}
        self.assertEqual(len(bindings), 9)
        for role in (
            "v25_live_runner", "v27_approval_ceremony", "v28_execution_gate",
            "v29_run_authorization_transform", "v30_proof_enforcing_live_gate",
            "v31_authority_state_atomic_consume", "v32_external_state_atomic_consume",
            "v33_canonical_store_toctou", "v42_authority_root_attestation",
        ):
            self.assertIn(role, bindings)
            self.assertEqual(len(bindings[role]["git_blob_sha"]), 40)

    def test_12_source_worktree_mismatch_fails_closed(self):
        original = prep._text_blob_sha1

        def fake(path):
            if path.name == Path(prep.SOURCE_PATHS[1][1]).name:
                return "0" * 40
            return original(path)

        with patch.object(prep, "_text_blob_sha1", side_effect=fake):
            with self.assertRaises(PermissionError):
                prep.build_approval_execution_plan()

    def test_13_changed_candidate_boundary_fails_closed(self):
        with patch.object(prep.candidate_prep, "EXPECTED_RUNTIME_MODEL_ID", "other-model"):
            with self.assertRaises(PermissionError):
                prep.build_approval_execution_plan()

    def test_14_plan_hash_is_deterministic(self):
        first = prep.build_approval_execution_plan()
        second = prep.build_approval_execution_plan()
        self.assertEqual(first, second)
        self.assertEqual(first["approval_execution_plan_sha256"], second["approval_execution_plan_sha256"])

    def test_15_tampered_plan_rejected_even_with_recomputed_hash(self):
        plan = prep.build_approval_execution_plan()
        tampered = copy.deepcopy(plan)
        tampered["expected_model_request_count"] = 17
        unsigned = dict(tampered)
        unsigned.pop("approval_execution_plan_sha256")
        tampered["approval_execution_plan_sha256"] = prep._stable_sha256(unsigned)
        with self.assertRaises(PermissionError):
            prep.validate_approval_execution_plan(tampered)

    def test_16_report_is_fully_model_free(self):
        report = prep.build_report()
        self.assertEqual(report["mode"], "MODEL_FREE_MINISTRAL_QUALIFICATION_APPROVAL_EXECUTION_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["governance_status"], "PREPARED_NOT_AUTHORIZED")
        for key in (
            "explicit_user_approval_recorded", "approval_secret_generated", "challenge_persisted",
            "approval_proof_materialized", "gate_claim_persisted", "authorization_consumed",
            "ready_for_model_contact", "execution_authorized", "model_run_authorized",
            "model_contact_authorized", "model_contact_performed", "model_qualified",
        ):
            self.assertIs(report[key], False, key)

    def test_17_module_has_no_execution_or_materialization_entrypoint(self):
        names = set(vars(prep))
        for forbidden in (
            "execute_once", "_default_transport", "_default_preflight",
            "generate_gate_nonce", "build_gate_challenge_preview", "persist_gate_challenge_once",
            "build_gate_approval_proof_preview", "claim_gate_once_preview",
            "build_run_authorization_preview", "consume_authorization",
            "materialize_live_authorization", "persist_authorization",
        ):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
