from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep as prep


class V21AuthorizationRunnerIntegrationPrepTests(unittest.TestCase):
    def _approved_auth(self):
        auth = prep.build_authorization_template()
        auth.update({
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        })
        return auth

    def test_g01_authorization_report_passes_model_free(self) -> None:
        report = prep.build_authorization_report()
        self.assertEqual(report["mode"], "MODEL_FREE_AUTHORIZATION_RUNNER_INTEGRATION_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["authorization_binding_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertTrue(report["future_live_runner_must_persist_consumption_before_model_contact"])
        self.assertTrue(report["new_explicit_single_use_model_contact_authorization_required"])
        self.assertFalse(report["model_qualified"])

    def test_g02_all_authorization_checks_are_true(self) -> None:
        report = prep.build_authorization_report()
        self.assertTrue(report["checks"])
        self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_g03_template_is_non_authorizing(self) -> None:
        template = prep.build_authorization_template()
        self.assertEqual(template["status"], "NOT_AUTHORIZED_TEMPLATE")
        self.assertFalse(template["execution_authorized"])
        self.assertFalse(template["model_run_authorized"])
        self.assertFalse(template["model_contact_authorized"])
        self.assertFalse(template["authorization_consumed"])

    def test_g04_exact_artifact_bindings_are_present(self) -> None:
        template = prep.build_authorization_template()
        self.assertEqual(template["runtime_model_id"], prep.v19.EXPECTED_MODEL_ID)
        self.assertEqual(template["prompt_sha256"], prep.v19.EXPECTED_PROMPT_SHA256)
        self.assertEqual(template["response_format_sha256"], prep.v19.EXPECTED_RESPONSE_FORMAT_SHA256)
        self.assertEqual(template["expected_model_request_count"], 16)
        self.assertEqual(template["max_tokens"], 1024)
        self.assertEqual(template["required_request_timeout_seconds"], 1800.0)
        self.assertEqual(len(prep._frozen_case_ids()), 16)

    def test_g05_default_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization(prep.build_authorization_template())

    def test_g06_mismatched_authorization_fails_closed(self) -> None:
        auth = self._approved_auth()
        auth["max_tokens"] = 2048
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization(auth)

    def test_g07_transport_not_called_without_authorization(self) -> None:
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            return "unexpected", {}

        with self.assertRaises(PermissionError):
            prep.execute_once(transport=transport)
        self.assertEqual(calls, [])

    def test_g08_exact_explicit_artifact_drives_all_16_injected_test_calls(self) -> None:
        auth = self._approved_auth()
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            return kwargs["case_id"], {"ok": True}

        results = prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(len(results), 16)
        self.assertEqual(len(calls), 16)
        self.assertEqual([call["case_id"] for call in calls], prep._frozen_case_ids())
        self.assertTrue(auth["authorization_consumed"])
        self.assertTrue(all(call["base_url"] == "http://127.0.0.1:1234/v1" for call in calls))
        self.assertTrue(all(call["timeout_seconds"] == 1800.0 for call in calls))

    def test_g09_same_authorization_cannot_be_reused(self) -> None:
        auth = self._approved_auth()
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            return "ok", {}

        prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(len(calls), 16)
        with self.assertRaises(PermissionError):
            prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(len(calls), 16)

    def test_g10_authorization_is_consumed_before_transport_failure(self) -> None:
        auth = self._approved_auth()
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            raise RuntimeError("synthetic transport failure")

        with self.assertRaises(RuntimeError):
            prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(len(calls), 1)
        self.assertTrue(auth["authorization_consumed"])
        with self.assertRaises(PermissionError):
            prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(len(calls), 1)

    def test_g11_execution_path_fails_closed_when_current_binding_is_not_exact(self) -> None:
        auth = self._approved_auth()
        original = prep.v20.build_assembly_report
        try:
            prep.v20.build_assembly_report = lambda: {
                "status": "FAIL_CLOSED",
                "assembly_ready": False,
                "ready_to_execute": False,
                "checks": {"prompt_hash_pinned": False},
            }
            calls = []

            def transport(**kwargs):
                calls.append(kwargs)
                return "unexpected", {}

            with self.assertRaises(PermissionError):
                prep.execute_once(transport=transport, authorization=auth)
            self.assertEqual(calls, [])
            self.assertFalse(auth["authorization_consumed"])
        finally:
            prep.v20.build_assembly_report = original


if __name__ == "__main__":
    unittest.main()
