from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_qualifikation_runner_v2_0_assembly_prep as prep


class V20ExecutableRunnerAssemblyPrepTests(unittest.TestCase):
    def test_f01_assembly_report_passes_model_free(self) -> None:
        report = prep.build_assembly_report()
        self.assertEqual(report["mode"], "MODEL_FREE_EXECUTABLE_RUNNER_ASSEMBLY_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["assembly_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertTrue(report["new_explicit_single_use_model_contact_authorization_required"])
        self.assertFalse(report["model_qualified"])

    def test_f02_all_assembly_checks_are_true(self) -> None:
        report = prep.build_assembly_report()
        self.assertTrue(report["checks"])
        self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_f03_request_binding_is_exact(self) -> None:
        checks = prep.build_assembly_report()["checks"]
        self.assertTrue(checks["runtime_model_id_exact"])
        self.assertTrue(checks["max_tokens_exact"])
        self.assertTrue(checks["stream_false"])
        self.assertTrue(checks["timeout_exact"])
        self.assertTrue(checks["loopback_base_url_exact"])

    def test_f04_artifact_hashes_remain_pinned(self) -> None:
        checks = prep.build_assembly_report()["checks"]
        self.assertTrue(checks["prompt_hash_pinned"])
        self.assertTrue(checks["response_format_hash_pinned"])

    def test_f05_full_context_and_policy_remain_bound(self) -> None:
        checks = prep.build_assembly_report()["checks"]
        self.assertTrue(checks["full_reference_questions"])
        self.assertTrue(checks["full_meaning_layer"])
        self.assertTrue(checks["retry_zero"])
        self.assertTrue(checks["output_repair_false"])
        self.assertTrue(checks["remote_cloud_false"])
        self.assertTrue(checks["real_data_false"])

    def test_f06_authorization_fails_closed(self) -> None:
        with self.assertRaises(PermissionError):
            prep.validate_execution_authorization()

    def test_f07_transport_is_not_called_when_unauthorized(self) -> None:
        calls = []

        def transport(**kwargs):
            calls.append(kwargs)
            return "unexpected", {}

        with self.assertRaises(PermissionError):
            prep.execute_once(transport=transport)
        self.assertEqual(calls, [])

    def test_f08_no_default_transport_is_embedded(self) -> None:
        with self.assertRaises(TypeError):
            prep.execute_once()  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
