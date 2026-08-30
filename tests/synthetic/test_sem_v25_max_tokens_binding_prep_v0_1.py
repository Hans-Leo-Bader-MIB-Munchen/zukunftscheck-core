from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

import scripts.zs_ki_b_sem_qualifikation_runner_v2_4_structured_output_failclosed_repair as v24
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25


class SemV25MaxTokensBindingPrepTests(unittest.TestCase):
    def _approved_auth(self) -> dict:
        auth = deepcopy(v25.build_live_authorization_template())
        auth.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "authorization_consumed": False,
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        return auth

    def test_v25_01_inherits_v24_invalid_json_failclosed(self):
        with self.assertRaises(v24.StructuredOutputError) as ctx:
            v25._validate_structured_output(raw='{"x":"cut', provider_metadata={}, case_id="PF12")
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_INVALID_JSON")

    def test_v25_02_inherits_v24_non_object_failclosed(self):
        with self.assertRaises(v24.StructuredOutputError) as ctx:
            v25._validate_structured_output(raw="[]", provider_metadata={}, case_id="PF12")
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_NOT_OBJECT")

    def test_v25_03_finish_reason_length_remains_failclosed(self):
        with self.assertRaises(v24.StructuredOutputError) as ctx:
            v25._validate_structured_output(raw='{"valid":true}', provider_metadata={"finish_reason": "length"}, case_id="PF12")
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_TRUNCATED")

    def test_v25_04_max_tokens_is_explicitly_2048(self):
        self.assertEqual(v25.MAX_TOKENS, 2048)
        self.assertEqual(v25.build_live_authorization_template()["max_tokens"], 2048)

    def test_v25_05_request_payload_binds_exactly_2048(self):
        case_id = v25.v24.v23.v21._frozen_case_ids()[0]
        payload = v25.build_candidate_request(case_id)
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertFalse(payload["stream"])

    def test_v25_06_request_bound_rejects_1024_and_no_adaptive_raise(self):
        case_id = v25.v24.v23.v21._frozen_case_ids()[0]
        payload = v25.build_candidate_request(case_id)
        payload["max_tokens"] = 1024
        with self.assertRaises(v25.LiveRunnerError):
            v25._assert_request_bounds(payload)
        self.assertEqual(v25.MAX_TOKENS, 2048)

    def test_v25_07_retry_and_repair_remain_forbidden(self):
        self.assertEqual(v25.RETRY_COUNT, 0)
        self.assertFalse(v25.OUTPUT_REPAIR)
        report = v25.build_integration_report()
        self.assertTrue(report["checks"]["automatic_retry_forbidden"])
        self.assertTrue(report["checks"]["adaptive_token_increase_forbidden"])

    def test_v25_08_model_qualified_and_authorization_flags_remain_false(self):
        report = v25.build_integration_report()
        self.assertFalse(report["model_qualified"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertEqual(report["governance_status"], "NO_MODEL_RUN_AUTHORIZED")

    def test_v25_09_old_v24_authorization_cannot_be_reused(self):
        old = deepcopy(v24.build_live_authorization_template())
        old.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "authorization_consumed": False,
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
            }
        )
        with self.assertRaises(PermissionError):
            v25.validate_live_execution_authorization(old)

    def test_v25_10_authorization_consumed_before_preflight(self):
        auth = self._approved_auth()
        order: list[str] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"

            def claim(path, supplied_auth):
                order.append("consume")
                path.write_text("claimed", encoding="utf-8")

            def preflight(**kwargs):
                order.append("preflight")
                raise RuntimeError("synthetic preflight stop")

            with mock.patch.object(v25.v24.v23.v22, "claim_authorization_once", side_effect=claim):
                output = v25.execute_once(
                    authorization=auth,
                    consumption_path=consumption,
                    result_path=result,
                    preflight=preflight,
                    transport=lambda **kwargs: self.fail("transport must not run"),
                )
            self.assertEqual(order, ["consume", "preflight"])
            self.assertEqual(output["status"], "FAILED_PRESERVED_NO_RETRY")

    def test_v25_11_length_failure_stops_after_one_attempt_without_retry(self):
        auth = self._approved_auth()
        calls: list[int] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"

            def transport(**kwargs):
                calls.append(kwargs["payload"]["max_tokens"])
                return '{"otherwise":"valid"}', {"finish_reason": "length", "usage": {"completion_tokens": 2048}}

            output = v25.execute_once(
                authorization=auth,
                consumption_path=consumption,
                result_path=result,
                preflight=lambda **kwargs: {"synthetic": True},
                transport=transport,
            )
            self.assertEqual(calls, [2048])
            self.assertEqual(output["observed_model_request_count"], 1)
            self.assertEqual(output["error_code"], "STRUCTURED_OUTPUT_TRUNCATED")
            self.assertFalse(output["automatic_retry_authorized"])
            self.assertFalse(output["automatic_rerun_authorized"])
            self.assertFalse(output["output_repair"])

    def test_v25_12_report_is_model_free_and_exposes_bound(self):
        report = v25.build_integration_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["selected_max_tokens_candidate"], 2048)
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertEqual(report["run_003_evidence"]["pf12_completion_tokens"], 1024)
        self.assertFalse(report["run_003_evidence"]["exact_required_bound_known"])

    def test_v25_13_v24_blob_is_unchanged_from_merged_v24(self):
        self.assertEqual(
            v25.v24.v23._git("rev-parse", "HEAD:scripts/zs_ki_b_sem_qualifikation_runner_v2_4_structured_output_failclosed_repair.py"),
            "af810ec05015ed4d39d4854dcfb350f653b3a7d0",
        )

    def test_v25_14_candidate_comparison_is_explicit(self):
        report = v25.build_integration_report()
        self.assertEqual(set(report["candidate_assessment"]), {"1536", "2048", "3072", "4096"})
        self.assertIn("selected", report["candidate_assessment"]["2048"]["assessment"])


if __name__ == "__main__":
    unittest.main()
