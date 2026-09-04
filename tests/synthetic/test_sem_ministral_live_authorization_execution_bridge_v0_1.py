from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_ministral_live_authorization_execution_bridge_v0_1 as bridge


class TestSemMinistralLiveAuthorizationExecutionBridge(unittest.TestCase):
    def _paths(self, root: Path, head: str) -> tuple[Path, Path]:
        consume = root / f"zs_ki_b_sem_ministral_{head}_consumed.json"
        result = root / f"zs_ki_b_sem_ministral_qualification_{head}_result.json"
        return consume, result

    def _materialize(self, root: Path):
        head = bridge.current_git_commit()
        consume, result = self._paths(root, head)
        approval = bridge.expected_approval_text(head)
        with patch.object(bridge, "current_branch", return_value="main"), patch.object(
            bridge, "working_tree_clean", return_value=True
        ):
            auth = bridge.materialize_live_authorization(
                approval_text=approval, consumption_path=consume, result_path=result
            )
        return auth, consume, result

    def test_01_exact_base_plan_and_v25_bindings(self):
        self.assertEqual(bridge.BRIDGE_BASE_MAIN_COMMIT, "4cad196736fabd0a7baee85ba3930cec3d15a8c4")
        self.assertEqual(bridge.PLAN_BLOB_SHA, "6ee75efa9949c0678b25aaa1b19fbd60d36f7493")
        self.assertEqual(bridge.V25_BLOB_SHA, "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866")
        bridge._validate_bound_sources_before_import()

    def test_02_report_is_model_free(self):
        report = bridge.build_bridge_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authorization_materialized_by_report"])
        self.assertFalse(report["authorization_consumed_by_report"])
        self.assertFalse(report["model_contact_performed_by_report"])
        self.assertFalse(report["model_run_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_qualified"])

    def test_03_exact_synthetic_model_and_request_bounds(self):
        report = bridge.build_bridge_report()
        self.assertEqual(report["data_class"], "SYNTHETIC_ONLY")
        self.assertEqual(report["runtime_model_id"], "ministral-3-14b-instruct-2512")
        self.assertEqual(report["expected_model_request_count"], 16)
        self.assertEqual(report["max_tokens"], 2048)
        self.assertEqual(report["retry_count"], 0)
        self.assertFalse(report["output_repair"])

    def test_04_expected_approval_text_binds_exact_commit(self):
        head = "a" * 40
        text = bridge.expected_approval_text(head)
        self.assertIn(f"`main` `{head}`", text)
        self.assertTrue(text.endswith("Keine Retries, kein Output-Repair, kein automatischer Rerun."))

    def test_05_bad_commit_rejected_by_approval_text_builder(self):
        for bad in ("abc", "A" * 40, "g" * 40, None):
            with self.assertRaises(PermissionError):
                bridge.expected_approval_text(bad)  # type: ignore[arg-type]

    def test_06_old_base_approval_is_rejected_on_current_head(self):
        head = bridge.current_git_commit()
        old = bridge.expected_approval_text(bridge.BRIDGE_BASE_MAIN_COMMIT)
        with tempfile.TemporaryDirectory() as td:
            consume, result = self._paths(Path(td), head)
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=old, consumption_path=consume, result_path=result
                    )

    def test_07_non_main_branch_rejected(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            consume, result = self._paths(Path(td), head)
            with patch.object(bridge, "current_branch", return_value="feature"):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=consume,
                        result_path=result,
                    )

    def test_08_dirty_worktree_rejected(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            consume, result = self._paths(Path(td), head)
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=False
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=consume,
                        result_path=result,
                    )

    def test_09_noncanonical_consumption_filename_rejected(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, result = self._paths(root, head)
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=root / "other.json",
                        result_path=result,
                    )

    def test_10_noncanonical_result_filename_rejected(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consume, _ = self._paths(root, head)
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=consume,
                        result_path=root / "other.json",
                    )

    def test_11_existing_consumption_receipt_rejects_replay(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consume, result = self._paths(root, head)
            consume.write_text("claimed", encoding="utf-8")
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=consume,
                        result_path=result,
                    )

    def test_12_existing_result_rejects_rerun(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consume, result = self._paths(root, head)
            result.write_text("existing", encoding="utf-8")
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ):
                with self.assertRaises(PermissionError):
                    bridge.materialize_live_authorization(
                        approval_text=bridge.expected_approval_text(head),
                        consumption_path=consume,
                        result_path=result,
                    )

    def test_13_materialized_authorization_is_exact_v25_shape(self):
        with tempfile.TemporaryDirectory() as td:
            auth, _, _ = self._materialize(Path(td))
            template = bridge.v25.build_live_authorization_template()
            self.assertEqual(set(auth), set(template))
            self.assertEqual(auth["status"], "EXPLICIT_USER_APPROVED")
            self.assertTrue(auth["execution_authorized"])
            self.assertTrue(auth["model_run_authorized"])
            self.assertTrue(auth["model_contact_authorized"])
            self.assertFalse(auth["authorization_consumed"])

    def test_14_materialization_does_not_persist_or_contact(self):
        with tempfile.TemporaryDirectory() as td:
            _, consume, result = self._materialize(Path(td))
            self.assertFalse(consume.exists())
            self.assertFalse(result.exists())

    def test_15_v25_accepts_materialized_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            auth, _, _ = self._materialize(Path(td))
            validated = bridge.v25.validate_live_execution_authorization(auth)
            self.assertEqual(validated, auth)

    def test_16_execute_bridge_hands_immediately_to_v25_execute_once(self):
        head = bridge.current_git_commit()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            consume, result = self._paths(root, head)
            approval = bridge.expected_approval_text(head)
            sentinel = {"status": "FAKE_EXECUTED"}
            with patch.object(bridge, "current_branch", return_value="main"), patch.object(
                bridge, "working_tree_clean", return_value=True
            ), patch.object(bridge.v25, "execute_once", return_value=sentinel) as execute:
                observed = bridge.execute_approved_once(
                    approval_text=approval, consumption_path=consume, result_path=result
                )
            self.assertIs(observed, sentinel)
            execute.assert_called_once()
            kwargs = execute.call_args.kwargs
            self.assertEqual(kwargs["consumption_path"], consume)
            self.assertEqual(kwargs["result_path"], result)
            self.assertEqual(kwargs["authorization"]["status"], "EXPLICIT_USER_APPROVED")

    def test_17_source_worktree_mismatch_fails_closed(self):
        original = bridge._text_blob_sha1

        def fake(path: Path):
            if path.name == Path(bridge.V25_PATH).name:
                return "0" * 40
            return original(path)

        with patch.object(bridge, "_text_blob_sha1", side_effect=fake):
            with self.assertRaises(PermissionError):
                bridge.build_bridge_report()

    def test_18_changed_frozen_plan_fails_closed(self):
        with patch.object(bridge.plan_prep, "EXPECTED_RUNTIME_MODEL_ID", "other-model"):
            with self.assertRaises(PermissionError):
                bridge.build_bridge_report()

    def test_19_old_user_approval_is_not_recorded_or_consumed_by_development(self):
        report = bridge.build_bridge_report()
        self.assertTrue(report["new_exact_current_main_user_approval_required"])
        self.assertFalse(report["authorization_consumed_by_report"])
        self.assertFalse(report["model_contact_performed_by_report"])

    def test_20_residual_issue_and_nonproduct_boundaries_remain(self):
        report = bridge.build_bridge_report()
        self.assertEqual(report["residual_architecture_issue"], 130)
        self.assertFalse(report["real_data"])
        self.assertFalse(report["pilot_approved"])
        self.assertFalse(report["production_approved"])
        self.assertFalse(report["model_qualified"])


if __name__ == "__main__":
    unittest.main()
