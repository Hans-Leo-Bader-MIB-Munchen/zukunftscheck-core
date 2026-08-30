import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v2_4_structured_output_failclosed_repair as prep


class V24StructuredOutputFailclosedRepairTests(unittest.TestCase):
    def _approved_auth(self):
        auth = deepcopy(prep.build_live_authorization_template())
        auth.update(
            {
                "status": "EXPLICIT_USER_APPROVED",
                "execution_authorized": True,
                "model_run_authorized": True,
                "model_contact_authorized": True,
                "authorization_consumed": False,
            }
        )
        return auth

    def _execute_with_transport(self, transport):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        return prep.execute_once(
            authorization=self._approved_auth(),
            consumption_path=root / "consumed.json",
            result_path=root / "result.json",
            preflight=lambda **_: {"ok": True},
            transport=transport,
        )

    def test_v24_01_valid_json_object_is_accepted(self):
        parsed = prep._validate_structured_output(
            raw='{"synthetic":true}', provider_metadata={}, case_id="SYN-1"
        )
        self.assertEqual(parsed, {"synthetic": True})

    def test_v24_02_pf12_like_truncated_json_string_fails_closed(self):
        with self.assertRaises(prep.StructuredOutputError) as ctx:
            prep._validate_structured_output(
                raw='{"finding":"cut off mid-string',
                provider_metadata={"usage": {"completion_tokens": 1024}},
                case_id="PF12",
            )
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_INVALID_JSON")

    def test_v24_03_damaged_json_fails_closed(self):
        with self.assertRaises(prep.StructuredOutputError) as ctx:
            prep._validate_structured_output(
                raw='{"a":1,,"b":2}', provider_metadata={}, case_id="SYN-3"
            )
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_INVALID_JSON")

    def test_v24_04_json_array_fails_closed(self):
        with self.assertRaises(prep.StructuredOutputError) as ctx:
            prep._validate_structured_output(
                raw='[{"a":1}]', provider_metadata={}, case_id="SYN-4"
            )
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_NOT_OBJECT")

    def test_v24_05_finish_reason_length_fails_even_with_valid_json(self):
        with self.assertRaises(prep.StructuredOutputError) as ctx:
            prep._validate_structured_output(
                raw='{"a":1}', provider_metadata={"finish_reason": "length"}, case_id="SYN-5"
            )
        self.assertEqual(ctx.exception.error_code, "STRUCTURED_OUTPUT_TRUNCATED")

    def test_v24_06_finish_reason_stop_accepts_valid_json(self):
        parsed = prep._validate_structured_output(
            raw='{"a":1}', provider_metadata={"finish_reason": "stop"}, case_id="SYN-6"
        )
        self.assertEqual(parsed, {"a": 1})

    def test_v24_07_missing_finish_reason_accepts_valid_json(self):
        parsed = prep._validate_structured_output(
            raw='{"a":1}', provider_metadata={"id": "synthetic"}, case_id="SYN-7"
        )
        self.assertEqual(parsed, {"a": 1})

    def test_v24_08_case_n_failure_counts_attempt_preserves_prior_and_stops(self):
        calls = []
        case_ids = list(prep.v23.integrity.EXPECTED_ORDERED_CASE_IDS)

        def transport(**kwargs):
            calls.append(kwargs["case_id"])
            if len(calls) < 3:
                return '{"ok":true}', {"finish_reason": "stop", "id": kwargs["case_id"]}
            if len(calls) == 3:
                return '{"finding":"cut', {
                    "finish_reason": "length",
                    "usage": {"completion_tokens": 1024},
                    "id": kwargs["case_id"],
                }
            self.fail("case N+1 must not be executed")

        outcome = self._execute_with_transport(transport)
        self.assertEqual(calls, case_ids[:3])
        self.assertEqual(outcome["observed_model_request_count"], 3)
        self.assertEqual([c["case_id"] for c in outcome["completed_cases"]], case_ids[:2])
        self.assertEqual(outcome["error_code"], "STRUCTURED_OUTPUT_TRUNCATED")

    def test_v24_09_failure_result_flags_are_fail_closed(self):
        outcome = self._execute_with_transport(
            lambda **_: ('{"broken":', {"finish_reason": "stop"})
        )
        self.assertEqual(outcome["status"], "FAILED_PRESERVED_NO_RETRY")
        self.assertEqual(outcome["stage"], "MODEL_REQUEST_AFTER_CONSUMPTION")
        self.assertEqual(outcome["observed_model_request_count"], 1)
        self.assertEqual(outcome["completed_cases"], [])
        self.assertEqual(outcome["error_code"], "STRUCTURED_OUTPUT_INVALID_JSON")
        self.assertEqual(outcome["retry_count"], 0)
        self.assertIs(outcome["output_repair"], False)
        self.assertIs(outcome["automatic_retry_authorized"], False)
        self.assertIs(outcome["automatic_rerun_authorized"], False)
        self.assertIs(outcome["model_qualified"], False)

    def test_v24_10_authorization_consumption_stays_before_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"
            auth = self._approved_auth()

            def preflight(**_):
                self.assertTrue(consumption.exists())
                persisted = json.loads(consumption.read_text(encoding="utf-8"))
                self.assertEqual(persisted["status"], "CONSUMED_PRE_MODEL_CONTACT")
                self.assertFalse(persisted["execution_authorized"])
                self.assertFalse(persisted["model_contact_authorized"])
                raise TimeoutError("synthetic stop after consumption")

            outcome = prep.execute_once(
                authorization=auth,
                consumption_path=consumption,
                result_path=result,
                preflight=preflight,
                transport=lambda **_: self.fail("transport must not be reached"),
            )
            self.assertEqual(outcome["status"], "FAILED_PRESERVED_NO_RETRY")
            self.assertEqual(outcome["observed_model_request_count"], 0)
            self.assertTrue(result.exists())

    def test_v24_11_default_transport_persists_finish_reason_without_inventing_it(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        class FakeOpener:
            def __init__(self, payload):
                self.payload = payload
            def open(self, *_args, **_kwargs):
                return FakeResponse(self.payload)

        request = prep.v23.v18.build_candidate_request_preview(
            case_id=prep.v23.integrity.EXPECTED_ORDERED_CASE_IDS[0]
        )
        envelope = {
            "id": "synthetic-env",
            "model": "synthetic-model",
            "created": 1,
            "usage": {"completion_tokens": 7},
            "choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}],
        }
        with patch("urllib.request.build_opener", return_value=FakeOpener(envelope)):
            raw, metadata = prep._default_transport(
                base_url=prep.BASE_URL,
                payload=request,
                timeout_seconds=prep.TIMEOUT_SECONDS,
                case_id="SYN-11",
            )
        self.assertEqual(raw, '{"ok":true}')
        self.assertEqual(metadata["finish_reason"], "stop")
        self.assertEqual(metadata["usage"]["completion_tokens"], 7)

        envelope_without_finish = {
            "choices": [{"message": {"content": '{"ok":true}'}}],
        }
        with patch("urllib.request.build_opener", return_value=FakeOpener(envelope_without_finish)):
            _, metadata_without_finish = prep._default_transport(
                base_url=prep.BASE_URL,
                payload=request,
                timeout_seconds=prep.TIMEOUT_SECONDS,
                case_id="SYN-11B",
            )
        self.assertNotIn("finish_reason", metadata_without_finish)

    def test_v24_12_report_is_model_free_closed_and_keeps_max_tokens_1024(self):
        report = prep.build_integration_report()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["live_runner_repair_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])
        self.assertFalse(report["model_qualified"])
        self.assertTrue(report["checks"]["max_tokens_1024_unchanged"])
        self.assertTrue(all(report["checks"].values()))


if __name__ == "__main__":
    unittest.main()
