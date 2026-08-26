from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from llm.local_model import structured_output_v0_3 as transport


class StructuredOutputV03Tests(unittest.TestCase):
    def test_01_version_and_default_timeout_are_explicit(self) -> None:
        self.assertEqual(transport.OUTPUT_MODE_VERSION, "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.3")
        self.assertEqual(transport.DEFAULT_TIMEOUT_SECONDS, 300.0)

    def test_02_payload_schema_is_identical_to_v0_2_builder(self) -> None:
        payload = transport.build_structured_payload(
            model="synthetic-model",
            messages=[{"role": "user", "content": "synthetic"}],
        )
        self.assertEqual(payload["response_format"], transport.build_response_format())
        self.assertNotIn("tools", payload)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["temperature"], 0.0)

    def test_03_default_timeout_300_is_passed_to_local_open(self) -> None:
        response = MagicMock()
        response.read.return_value = b'{"choices":[{"message":{"content":"{}"}}]}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        opener = MagicMock()
        opener.open.return_value = response

        with patch.object(transport.urllib.request, "build_opener", return_value=opener):
            content, _ = transport.chat_completion_structured(
                base_url="http://127.0.0.1:1234/v1",
                model="synthetic-model",
                messages=[{"role": "user", "content": "synthetic"}],
            )

        self.assertEqual(content, "{}")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 300.0)

    def test_04_explicit_timeout_override_remains_possible(self) -> None:
        response = MagicMock()
        response.read.return_value = b'{"choices":[{"message":{"content":"{}"}}]}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        opener = MagicMock()
        opener.open.return_value = response

        with patch.object(transport.urllib.request, "build_opener", return_value=opener):
            transport.chat_completion_structured(
                base_url="http://127.0.0.1:1234/v1",
                model="synthetic-model",
                messages=[{"role": "user", "content": "synthetic"}],
                timeout_seconds=17.0,
            )

        self.assertEqual(opener.open.call_args.kwargs["timeout"], 17.0)


if __name__ == "__main__":
    unittest.main()
