from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

import scripts.zs_ki_b_sem_qualifikation_runner_v2_2_persistent_consumption_prep as prep


class V22PersistentAuthorizationConsumptionPrepTests(unittest.TestCase):
    def _approved_auth(self):
        auth = prep.v21.build_authorization_template()
        auth.update({
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        })
        return auth

    def test_h01_persistence_report_passes_model_free(self) -> None:
        report = prep.build_persistence_report()
        self.assertEqual(report["mode"], "MODEL_FREE_PERSISTENT_AUTHORIZATION_CONSUMPTION_PREP")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["persistent_consumption_binding_ready"])
        self.assertFalse(report["ready_to_execute"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_contact_authorized"])
        self.assertFalse(report["model_contact_performed"])
        self.assertFalse(report["authorization_artifact_created"])
        self.assertFalse(report["consumption_artifact_created_by_report"])
        self.assertTrue(report["new_explicit_single_use_model_contact_authorization_required"])
        self.assertFalse(report["model_qualified"])

    def test_h02_all_persistence_checks_are_true(self) -> None:
        report = prep.build_persistence_report()
        self.assertTrue(report["checks"])
        self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_h03_invalid_authorization_cannot_create_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consumed.json"
            with self.assertRaises(PermissionError):
                prep.claim_authorization_once(path, prep.v21.build_authorization_template())
            self.assertFalse(path.exists())

    def test_h04_exact_authorization_is_persisted_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consumed.json"
            auth = self._approved_auth()
            state = prep.claim_authorization_once(path, auth)
            self.assertTrue(path.exists())
            self.assertEqual(state["status"], "CONSUMED_PRE_MODEL_CONTACT")
            self.assertTrue(state["authorization_consumed"])
            self.assertFalse(state["execution_authorized"])
            self.assertFalse(state["model_run_authorized"])
            self.assertFalse(state["model_contact_authorized"])
            self.assertTrue(auth["authorization_consumed"])
            self.assertFalse(auth["model_contact_authorized"])

    def test_h05_persisted_state_validates_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consumed.json"
            prep.claim_authorization_once(path, self._approved_auth())
            state = prep.validate_persisted_consumption(path)
            self.assertEqual(state["persistence_version"], prep.PERSISTENCE_VERSION)
            self.assertEqual(state["consumption_boundary"], "BEFORE_FIRST_MODEL_CONTACT")
            self.assertTrue(state["single_use_claimed"])

    def test_h06_second_claim_same_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consumed.json"
            prep.claim_authorization_once(path, self._approved_auth())
            with self.assertRaises(FileExistsError):
                prep.claim_authorization_once(path, self._approved_auth())

    def test_h07_reusing_consumed_in_memory_auth_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            auth = self._approved_auth()
            prep.claim_authorization_once(first, auth)
            with self.assertRaises(PermissionError):
                prep.claim_authorization_once(second, auth)
            self.assertFalse(second.exists())

    def test_h08_existing_sentinel_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consumed.json"
            path.write_text("sentinel", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prep.claim_authorization_once(path, self._approved_auth())
            self.assertEqual(path.read_text(encoding="utf-8"), "sentinel")

    def test_h09_missing_parent_fails_without_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing" / "consumed.json"
            with self.assertRaises(FileNotFoundError):
                prep.claim_authorization_once(path, self._approved_auth())
            self.assertFalse(path.exists())

    def test_h10_no_network_or_subprocess_imports(self) -> None:
        source = Path(prep.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue({"urllib", "requests", "httpx", "socket", "subprocess"}.isdisjoint(imported))

    def test_h11_direct_report_has_no_file_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = set(Path(tmp).iterdir())
            report = prep.build_persistence_report()
            after = set(Path(tmp).iterdir())
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
