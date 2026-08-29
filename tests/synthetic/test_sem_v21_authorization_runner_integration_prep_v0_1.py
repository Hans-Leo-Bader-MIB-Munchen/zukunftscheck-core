from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep as prep


class V21AuthorizationRunnerIntegrationPrepTests(unittest.TestCase):
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

    def test_g05_default_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization(prep.build_authorization_template())

    def test_g06_mismatched_authorization_fails_closed(self) -> None:
        auth = prep.build_authorization_template()
        auth.update({
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
            "max_tokens": 2048,
        })
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

    def test_g08_exact_explicit_artifact_can_unlock_injected_test_transport(self) -> None:
        auth = prep.build_authorization_template()
        auth.update({
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        })
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            return "synthetic-test-only", {"ok": True}

        result = prep.execute_once(transport=transport, authorization=auth)
        self.assertEqual(result[0], "synthetic-test-only")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["base_url"], "http://127.0.0.1:1234/v1")
        self.assertEqual(calls[0]["timeout_seconds"], 1800.0)


if __name__ == "__main__":
    unittest.main()
