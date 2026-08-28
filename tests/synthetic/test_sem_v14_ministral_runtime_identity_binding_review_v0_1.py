from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14

ROOT = Path(__file__).resolve().parents[2]


class MinistralRuntimeIdentityBindingReviewTests(unittest.TestCase):
    def test_b01_repository_and_runtime_identity_are_separate(self) -> None:
        self.assertEqual(v14.MODEL_REPOSITORY, "mistralai/Ministral-3-14B-Instruct-2512-GGUF")
        self.assertEqual(v14.RUNTIME_MODEL_ID, "ministral-3-14b-instruct-2512")
        self.assertEqual(v14.MODEL, v14.RUNTIME_MODEL_ID)
        self.assertNotEqual(v14.MODEL_REPOSITORY, v14.RUNTIME_MODEL_ID)

    def test_b02_binding_review_matches_preserved_discovery(self) -> None:
        review = v14.validate_runtime_binding_review()
        discovery = json.loads(
            (ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_runtime_identity_discovery_result_v0_1.json").read_text(
                encoding="utf-8"
            )
        )
        observed = discovery["compatible_loaded_instances"]
        self.assertEqual(len(observed), 1)
        self.assertEqual(review["runtime_model_id"], observed[0]["runtime_instance_id"])
        self.assertEqual(review["observed_model_key"], observed[0]["model_key"])
        self.assertEqual(review["observed_quantization"], observed[0]["quantization"])
        self.assertEqual(review["observed_loaded_context_length"], observed[0]["loaded_context_length"])

    def test_b03_binding_review_is_model_free(self) -> None:
        review = v14.validate_runtime_binding_review()
        self.assertFalse(review["new_inventory_contact_performed"])
        self.assertEqual(review["generation_request_count"], 0)
        self.assertFalse(review["generation_authorized"])
        self.assertFalse(review["qualification_execution_authorized"])
        self.assertFalse(review["model_contact_authorized"])
        self.assertFalse(review["model_qualified"])

    def test_b04_model_run_authorization_remains_closed(self) -> None:
        auth = v14.load(v14.AUTH_PATH)
        self.assertEqual(auth["status"], "NOT_APPROVED")
        self.assertEqual(auth["model_repository"], v14.MODEL_REPOSITORY)
        self.assertEqual(auth["runtime_model_id"], v14.RUNTIME_MODEL_ID)
        self.assertEqual(auth["model"], v14.RUNTIME_MODEL_ID)
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["model_run_authorized"])
        self.assertFalse(auth["model_contact_authorized"])
        self.assertFalse(auth["model_qualified"])

    def test_b05_closed_authorization_rejects_execution(self) -> None:
        with self.assertRaises(PermissionError):
            v14.validate_execution_authorization(v14.RUNTIME_MODEL_ID)

    def test_b06_repository_id_cannot_be_used_as_runtime_model(self) -> None:
        auth = v14.load(v14.AUTH_PATH)
        self.assertFalse(v14._authorization_matches(auth, v14.MODEL_REPOSITORY))

    def test_b07_dry_run_records_both_identities_and_stays_closed(self) -> None:
        with patch.object(
            v14.v13.v11.v10.v09.base,
            "current_git_commit",
            return_value="MODEL_FREE_TEST_COMMIT",
        ):
            payload = v14.build_dry_run_manifest()
        manifest = payload["manifest"]
        self.assertEqual(manifest["model_repository"], v14.MODEL_REPOSITORY)
        self.assertEqual(manifest["runtime_model_id"], v14.RUNTIME_MODEL_ID)
        self.assertEqual(manifest["selected_candidate"], v14.MODEL_REPOSITORY)
        self.assertEqual(manifest["selected_runtime_model_id"], v14.RUNTIME_MODEL_ID)
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["model_run_authorized"])
        self.assertFalse(manifest["model_contact_performed"])

    def test_b08_source_introduces_no_new_contact_or_generation_path(self) -> None:
        source = (ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v1_4.py").read_text(encoding="utf-8")
        self.assertNotIn("urllib.request.urlopen", source)
        self.assertNotIn("/api/v1/models", source)
        self.assertNotIn("chat_completion_structured(", source)
        self.assertIn("MODEL_REPOSITORY", source)
        self.assertIn("RUNTIME_MODEL_ID", source)


if __name__ == "__main__":
    unittest.main()
