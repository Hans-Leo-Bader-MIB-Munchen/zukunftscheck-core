from __future__ import annotations

import unittest

import scripts.zs_ki_b_sem_ministral_timeout_rootcause_audit_v0_1 as audit


class MinistralTimeoutRootCauseAuditTests(unittest.TestCase):
    def test_a01_audit_is_explicitly_model_free(self) -> None:
        payload = audit.build_audit()
        self.assertEqual(payload["mode"], "MODEL_FREE_STATIC_AUDIT")
        self.assertFalse(payload["model_contact_performed"])
        self.assertFalse(payload["localhost_contact_performed"])
        self.assertFalse(payload["remote_contact_performed"])

    def test_a02_pf1_request_contains_full_meaning_layer(self) -> None:
        payload = audit.build_audit()
        profile = payload["request_profile"]
        self.assertEqual(profile["reference_question_count"], 67)
        self.assertEqual(profile["meaning_count"], 67)
        self.assertEqual(profile["source_location_count"], 1)
        self.assertGreater(profile["components"]["reference_question_meanings"]["utf8_bytes"], 0)

    def test_a03_transport_has_no_output_token_cap(self) -> None:
        transport = audit.build_audit()["transport_profile"]
        self.assertTrue(transport["stream_false"])
        self.assertFalse(transport["has_max_tokens_parameter"])
        self.assertFalse(transport["has_max_completion_tokens_parameter"])
        self.assertEqual(transport["v15_required_timeout_seconds"], 1800)

    def test_a04_schema_has_unbounded_arrays(self) -> None:
        schema = audit.build_audit()["schema_profile"]
        self.assertTrue(schema["strict_json_schema"])
        self.assertGreater(schema["unbounded_array_count"], 0)
        joined = "\n".join(schema["array_paths_without_max_items"])
        self.assertIn("proposals", joined)
        self.assertIn("assignment_candidates", joined)

    def test_a05_no_runtime_or_network_modules_are_used(self) -> None:
        source = audit.__file__
        text = open(source, encoding="utf-8").read()
        for forbidden in (
            "urllib.request",
            "requests.",
            "chat_completion_structured",
            "preflight_loaded_model",
            "subprocess",
            "/chat/completions",
            "/api/v1/models",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
