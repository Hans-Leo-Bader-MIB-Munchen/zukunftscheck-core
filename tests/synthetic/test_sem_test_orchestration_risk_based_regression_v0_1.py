from __future__ import annotations

import unittest
from unittest.mock import patch

import scripts.zs_ki_b_test_orchestration_risk_based_regression_v0_1 as orch


class TestSemTestOrchestrationRiskBasedRegression(unittest.TestCase):
    def test_01_base_binding_exact(self):
        self.assertEqual(orch.BASE_MAIN_COMMIT, "39d57ded8108b0c8f724db15d36dbce1c22bf212")

    def test_02_deep_allowlist_has_no_duplicates(self):
        self.assertEqual(len(orch.SECURITY_CRITICAL_DEEP_MODULES), len(set(orch.SECURITY_CRITICAL_DEEP_MODULES)))

    def test_03_deep_allowlist_covers_v25_through_v37(self):
        joined = "\n".join(orch.SECURITY_CRITICAL_DEEP_MODULES)
        for version in range(25, 38):
            self.assertIn(f"test_sem_v{version}_", joined)

    def test_04_deep_allowlist_covers_global_runtime_and_freeze_guards(self):
        required = {
            "tests.synthetic.test_sem_runtime_guard_frozen_suite_sweep_v0_1",
            "tests.synthetic.test_semantic_runtime_guard_v0_1",
            "tests.synthetic.test_sem_canonical_binding_integrity_v0_1",
            "tests.synthetic.test_sem_system_qualification_execute_v0_2_gate",
            "tests.synthetic.test_sem_system_qualification_freeze_final_v0_2",
        }
        self.assertTrue(required.issubset(set(orch.SECURITY_CRITICAL_DEEP_MODULES)))

    def test_05_fast_is_exact_subset_of_deep(self):
        self.assertTrue(set(orch.SECURITY_CRITICAL_FAST_MODULES).issubset(set(orch.SECURITY_CRITICAL_DEEP_MODULES)))
        self.assertEqual(len(orch.SECURITY_CRITICAL_FAST_MODULES), 8)

    def test_06_fast_contains_v35_v36_v37_and_global_guards(self):
        required = {
            "tests.synthetic.test_sem_v35_external_attestation_global_single_use_prep_v0_1",
            "tests.synthetic.test_sem_v36_external_attestation_persistent_global_single_use_prep_v0_1",
            "tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1",
            "tests.synthetic.test_sem_runtime_guard_frozen_suite_sweep_v0_1",
            "tests.synthetic.test_semantic_runtime_guard_v0_1",
            "tests.synthetic.test_sem_canonical_binding_integrity_v0_1",
            "tests.synthetic.test_sem_system_qualification_execute_v0_2_gate",
            "tests.synthetic.test_sem_system_qualification_freeze_final_v0_2",
        }
        self.assertEqual(set(orch.SECURITY_CRITICAL_FAST_MODULES), required)

    def test_07_backward_critical_alias_is_deep_not_fast(self):
        self.assertEqual(orch.SECURITY_CRITICAL_MODULES, orch.SECURITY_CRITICAL_DEEP_MODULES)
        self.assertNotEqual(orch.SECURITY_CRITICAL_MODULES, orch.SECURITY_CRITICAL_FAST_MODULES)

    def test_08_focused_accepts_existing_synthetic_test_module(self):
        name = "tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1"
        self.assertEqual(orch._validate_focused_module(name), name)

    def test_09_focused_rejects_non_test_module(self):
        with self.assertRaises(ValueError):
            orch._validate_focused_module("scripts.zs_ki_b_test_orchestration_risk_based_regression_v0_1")

    def test_10_focused_rejects_path_traversal_and_shell_text(self):
        for value in (
            "tests.synthetic...test_x",
            "tests.synthetic.test_x;echo_bad",
            "../tests/synthetic/test_x.py",
            "tests.synthetic.test_x/../../bad",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                orch._validate_focused_module(value)

    def test_11_focused_requires_at_least_one_module(self):
        with self.assertRaises(ValueError):
            orch.build_suite("focused", ())

    def test_12_focused_rejects_duplicate_modules(self):
        name = "tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1"
        with self.assertRaises(ValueError):
            orch.build_suite("focused", (name, name))

    def test_13_unknown_profile_fails_closed(self):
        with self.assertRaises(ValueError):
            orch.build_suite("unknown")

    def test_14_full_profile_uses_repository_test_discovery(self):
        sentinel = unittest.TestSuite()
        with patch.object(orch.unittest.defaultTestLoader, "discover", return_value=sentinel) as discover:
            result = orch.build_suite("full")
        self.assertIs(result, sentinel)
        discover.assert_called_once_with(
            start_dir=str(orch.ROOT / "tests"), pattern="test*.py", top_level_dir=str(orch.ROOT)
        )

    def test_15_critical_fast_uses_exact_fast_allowlist(self):
        sentinel = unittest.TestSuite()
        with patch.object(orch, "_load_named_modules", return_value=sentinel) as loader:
            result = orch.build_suite("critical-fast")
        self.assertIs(result, sentinel)
        loader.assert_called_once_with(orch.SECURITY_CRITICAL_FAST_MODULES)

    def test_16_critical_and_deep_use_exact_deep_allowlist(self):
        for profile in ("critical", "critical-deep"):
            sentinel = unittest.TestSuite()
            with self.subTest(profile=profile), patch.object(orch, "_load_named_modules", return_value=sentinel) as loader:
                result = orch.build_suite(profile)
                self.assertIs(result, sentinel)
                loader.assert_called_once_with(orch.SECURITY_CRITICAL_DEEP_MODULES)

    def test_17_run_profile_returns_nonzero_on_failure(self):
        class Failing(unittest.TestCase):
            def runTest(self):
                self.fail("expected")

        with patch.object(orch, "build_suite", return_value=unittest.TestSuite([Failing()])):
            self.assertEqual(orch.run_profile("critical-fast", verbosity=0), 1)

    def test_18_run_profile_returns_zero_on_success(self):
        class Passing(unittest.TestCase):
            def runTest(self):
                self.assertTrue(True)

        with patch.object(orch, "build_suite", return_value=unittest.TestSuite([Passing()])):
            self.assertEqual(orch.run_profile("critical-fast", verbosity=0), 0)

    def test_19_runner_has_no_model_or_transport_helpers(self):
        forbidden = {
            "execute_once",
            "materialize_live_authorization",
            "_default_transport",
            "_default_preflight",
            "model_contact",
        }
        self.assertTrue(forbidden.isdisjoint(set(vars(orch))))

    def test_20_profiles_do_not_encode_authorization_state(self):
        names = set(vars(orch))
        self.assertNotIn("MODEL_RUN_AUTHORIZED", names)
        self.assertNotIn("MODEL_CONTACT_AUTHORIZED", names)
        self.assertNotIn("MODEL_QUALIFIED", names)

    def test_21_critical_timing_diagnostic_uses_exact_deep_allowlist(self):
        class PassingResult:
            @staticmethod
            def wasSuccessful():
                return True

        calls = []

        def fake_load(names):
            calls.append(tuple(names))
            return unittest.TestSuite()

        with patch.object(orch, "_load_named_modules", side_effect=fake_load), patch.object(
            orch.unittest, "TextTestRunner"
        ) as runner_cls, patch.object(orch.time, "perf_counter", side_effect=range(1000)):
            runner_cls.return_value.run.return_value = PassingResult()
            self.assertEqual(orch.run_critical_module_timings(verbosity=0), 0)

        self.assertEqual(calls, [(name,) for name in orch.SECURITY_CRITICAL_DEEP_MODULES])

    def test_22_critical_timing_diagnostic_stops_fail_closed_on_first_failure(self):
        class FailingResult:
            @staticmethod
            def wasSuccessful():
                return False

        with patch.object(orch, "_load_named_modules", return_value=unittest.TestSuite()), patch.object(
            orch.unittest, "TextTestRunner"
        ) as runner_cls, patch.object(orch.time, "perf_counter", side_effect=range(1000)):
            runner_cls.return_value.run.return_value = FailingResult()
            self.assertEqual(orch.run_critical_module_timings(verbosity=0), 1)
            self.assertEqual(runner_cls.return_value.run.call_count, 1)

    def test_23_cli_accepts_fast_and_deep_profiles(self):
        self.assertEqual(orch._parse_args(["--profile", "critical-fast"]).profile, "critical-fast")
        self.assertEqual(orch._parse_args(["--profile", "critical-deep"]).profile, "critical-deep")

    def test_24_cli_rejects_profile_plus_critical_timings(self):
        with self.assertRaises(SystemExit):
            orch._parse_args(["--profile", "critical-fast", "--critical-timings"])

    def test_25_cli_requires_profile_or_timing_mode(self):
        with self.assertRaises(SystemExit):
            orch._parse_args([])


if __name__ == "__main__":
    unittest.main()
