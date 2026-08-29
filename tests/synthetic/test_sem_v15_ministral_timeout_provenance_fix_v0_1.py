from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v1_5 as v15


class MinistralV15TimeoutProvenanceFixTests(unittest.TestCase):
    def test_t01_runner_identity_is_new_and_model_unchanged(self) -> None:
        self.assertEqual(v15.RUNNER_VERSION, "v1.5")
        self.assertEqual(v15.RUNTIME_MODEL_ID, "ministral-3-14b-instruct-2512")
        self.assertEqual(v15.REQUIRED_TIMEOUT, 1800)
        self.assertNotEqual(v15.RUN_TYPE, v15.v14.RUN_TYPE)

    def test_t02_transport_binds_actual_timeout_to_1800(self) -> None:
        calls = []
        original = v15._ORIGINAL_TRANSPORT
        try:
            def fake_transport(**kwargs):
                calls.append(kwargs)
                return "{}", {"choices": [{"message": {"content": "{}"}}]}

            v15._ORIGINAL_TRANSPORT = fake_transport
            v15._transport_with_required_timeout(
                base_url="http://127.0.0.1:1234/v1",
                model=v15.RUNTIME_MODEL_ID,
                messages=[{"role": "user", "content": "synthetic"}],
                temperature=0.0,
            )
        finally:
            v15._ORIGINAL_TRANSPORT = original

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["timeout_seconds"], 1800)
        self.assertEqual(calls[0]["model"], v15.RUNTIME_MODEL_ID)

    def test_t03_execution_provenance_records_authorized_and_preflight_pass(self) -> None:
        payload = {
            "mode": "EXECUTING_SEM_QUALIFICATION_V0_9",
            "manifest": {
                "execution_attempted": True,
                "observed_model_request_count": 1,
                "execution_authorized": False,
                "model_run_authorized": False,
                "preflight_pass_observed": False,
            },
            "preflight": {"loaded_instance_id": v15.RUNTIME_MODEL_ID},
        }
        result = v15.normalize_execution_provenance(payload)
        manifest = result["manifest"]
        self.assertEqual(result["mode"], "EXECUTING_SEM_QUALIFICATION_V1_5")
        self.assertTrue(manifest["execution_authorized"])
        self.assertTrue(manifest["model_run_authorized"])
        self.assertTrue(manifest["preflight_pass_observed"])
        self.assertTrue(manifest["model_contact_performed"])
        self.assertEqual(manifest["request_timeout_seconds"], 1800)

    def test_t04_dry_provenance_remains_closed(self) -> None:
        payload = {
            "mode": "DRY_RUN_SEM_QUALIFICATION_V1_5",
            "manifest": {
                "execution_attempted": False,
                "observed_model_request_count": 0,
                "execution_authorized": False,
                "model_run_authorized": False,
                "preflight_pass_observed": False,
            },
        }
        result = v15.normalize_execution_provenance(payload)
        manifest = result["manifest"]
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_performed"])
        self.assertFalse(manifest["preflight_pass_observed"])

    def test_t05_execution_is_fail_closed_without_new_authorization_artifact(self) -> None:
        self.assertFalse(v15.AUTH_PATH.exists())
        with self.assertRaises(PermissionError):
            v15.validate_execution_authorization(v15.RUNTIME_MODEL_ID)


if __name__ == "__main__":
    unittest.main()
