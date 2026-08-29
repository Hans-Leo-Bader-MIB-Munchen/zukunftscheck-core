import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v2_3_live_integration_prep as prep
import scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 as integrity


class V23LiveRunnerIntegrationPrepTests(unittest.TestCase):
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

    def test_i01_report_is_model_free_and_closed(self):
        report = prep.build_integration_report()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["live_runner_integration_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["preflight_performed"])
        self.assertFalse(report["model_qualified"])
        self.assertTrue(all(report["checks"].values()))

    def test_i02_template_binds_current_commit_runner_blob_and_exact_suite(self):
        template = prep.build_live_authorization_template()
        self.assertEqual(template["live_runner_git_commit"], prep.current_git_commit())
        self.assertEqual(template["live_runner_blob_oid"], prep.current_runner_blob_oid())
        self.assertEqual(template["integration_base_commit"], prep.INTEGRATION_BASE_COMMIT)
        self.assertEqual(tuple(template["ordered_case_ids"]), integrity.EXPECTED_ORDERED_CASE_IDS)
        self.assertEqual(template["expected_model_request_count"], 16)
        self.assertEqual(template["required_base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(template["max_tokens"], 1024)
        self.assertIs(template["stream"], False)
        self.assertEqual(template["required_request_timeout_seconds"], 1800.0)
        self.assertEqual(template["retry_count"], 0)
        self.assertIs(template["output_repair"], False)

    def test_i03_unapproved_template_cannot_execute_or_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(PermissionError):
                prep.execute_once(
                    authorization=prep.build_live_authorization_template(),
                    consumption_path=root / "consumed.json",
                    result_path=root / "result.json",
                    preflight=lambda **_: self.fail("preflight must not be reached"),
                    transport=lambda **_: self.fail("transport must not be reached"),
                )
            self.assertFalse((root / "consumed.json").exists())
            self.assertFalse((root / "result.json").exists())

    def test_i04_consumption_exists_before_preflight_and_all_16_calls_are_exact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"
            auth = self._approved_auth()
            calls = []

            def preflight(**kwargs):
                self.assertTrue(consumption.exists())
                persisted = json.loads(consumption.read_text(encoding="utf-8"))
                self.assertEqual(persisted["status"], "CONSUMED_PRE_MODEL_CONTACT")
                self.assertEqual(kwargs["base_url"], prep.BASE_URL)
                return {"model_key": "synthetic-preflight"}

            def transport(**kwargs):
                self.assertTrue(consumption.exists())
                payload = kwargs["payload"]
                self.assertEqual(kwargs["base_url"], prep.BASE_URL)
                self.assertEqual(kwargs["timeout_seconds"], 1800.0)
                self.assertEqual(payload["max_tokens"], 1024)
                self.assertIs(payload["stream"], False)
                calls.append(kwargs["case_id"])
                return '{"synthetic":true}', {"id": f"env-{len(calls)}", "model": "synthetic-model"}

            outcome = prep.execute_once(
                authorization=auth,
                consumption_path=consumption,
                result_path=result,
                preflight=preflight,
                transport=transport,
            )
            self.assertEqual(tuple(calls), integrity.EXPECTED_ORDERED_CASE_IDS)
            self.assertEqual(outcome["status"], "AWAITING_HUMAN_REVIEW")
            self.assertEqual(outcome["observed_model_request_count"], 16)
            self.assertEqual(outcome["human_gold_evaluation"], "PENDING_HUMAN_REVIEW")
            self.assertFalse(outcome["model_qualified"])
            self.assertTrue(result.exists())
            self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["status"], "AWAITING_HUMAN_REVIEW")
            self.assertEqual(auth["status"], "CONSUMED_PRE_MODEL_CONTACT")
            self.assertFalse(auth["model_contact_authorized"])

    def test_i05_preflight_failure_is_preserved_after_consumption_with_zero_model_requests(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"
            auth = self._approved_auth()
            transport_calls = []

            def preflight(**_):
                self.assertTrue(consumption.exists())
                raise TimeoutError("synthetic preflight timeout")

            outcome = prep.execute_once(
                authorization=auth,
                consumption_path=consumption,
                result_path=result,
                preflight=preflight,
                transport=lambda **kwargs: transport_calls.append(kwargs),
            )
            self.assertEqual(outcome["status"], "FAILED_PRESERVED_NO_RETRY")
            self.assertEqual(outcome["stage"], "PREFLIGHT_AFTER_CONSUMPTION")
            self.assertEqual(outcome["observed_model_request_count"], 0)
            self.assertEqual(transport_calls, [])
            self.assertTrue(consumption.exists())
            self.assertTrue(result.exists())
            self.assertFalse(outcome["automatic_retry_authorized"])
            self.assertFalse(outcome["automatic_rerun_authorized"])
            self.assertFalse(outcome["model_qualified"])

    def test_i06_first_model_timeout_is_counted_and_preserved_without_retry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consumption = root / "consumed.json"
            result = root / "result.json"
            auth = self._approved_auth()
            calls = []

            def transport(**kwargs):
                calls.append(kwargs["case_id"])
                raise TimeoutError("synthetic model timeout")

            outcome = prep.execute_once(
                authorization=auth,
                consumption_path=consumption,
                result_path=result,
                preflight=lambda **_: {"ok": True},
                transport=transport,
            )
            self.assertEqual(len(calls), 1)
            self.assertEqual(outcome["status"], "FAILED_PRESERVED_NO_RETRY")
            self.assertEqual(outcome["stage"], "MODEL_REQUEST_AFTER_CONSUMPTION")
            self.assertEqual(outcome["observed_model_request_count"], 1)
            self.assertEqual(outcome["completed_cases"], [])
            self.assertFalse(outcome["automatic_retry_authorized"])
            self.assertTrue(result.exists())

    def test_i07_consumed_authorization_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            auth = self._approved_auth()
            prep.execute_once(
                authorization=auth,
                consumption_path=root / "consumed-1.json",
                result_path=root / "result-1.json",
                preflight=lambda **_: {"ok": True},
                transport=lambda **kwargs: ('{"ok":true}', {"id": kwargs["case_id"]}),
            )
            with self.assertRaises(PermissionError):
                prep.execute_once(
                    authorization=auth,
                    consumption_path=root / "consumed-2.json",
                    result_path=root / "result-2.json",
                    preflight=lambda **_: self.fail("preflight must not be reached on reuse"),
                    transport=lambda **_: self.fail("transport must not be reached on reuse"),
                )

    def test_i08_existing_result_blocks_before_consumption_or_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = root / "result.json"
            result.write_text("{}\n", encoding="utf-8")
            consumption = root / "consumed.json"
            with self.assertRaises(FileExistsError):
                prep.execute_once(
                    authorization=self._approved_auth(),
                    consumption_path=consumption,
                    result_path=result,
                    preflight=lambda **_: self.fail("preflight must not be reached"),
                    transport=lambda **_: self.fail("transport must not be reached"),
                )
            self.assertFalse(consumption.exists())

    def test_i09_mutated_runner_binding_is_rejected_before_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            auth = self._approved_auth()
            auth["live_runner_blob_oid"] = "0" * 40
            with self.assertRaises(PermissionError):
                prep.execute_once(
                    authorization=auth,
                    consumption_path=root / "consumed.json",
                    result_path=root / "result.json",
                    preflight=lambda **_: self.fail("preflight must not be reached"),
                    transport=lambda **_: self.fail("transport must not be reached"),
                )
            self.assertFalse((root / "consumed.json").exists())


if __name__ == "__main__":
    unittest.main()
