from __future__ import annotations

import io
import unittest
import urllib.error
from unittest.mock import patch

from llm.local_model.structured_output_v0_5 import LocalModelError, chat_completion_structured


class StructuredOutputV05HttpErrorTests(unittest.TestCase):
    def test_t25_http_400_preserves_local_endpoint_response_body(self) -> None:
        response_body = b'{"error":{"message":"Invalid schema for response_format: unsupported keyword"}}'
        http_error = urllib.error.HTTPError(
            url="http://127.0.0.1:1234/v1/chat/completions",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(response_body),
        )

        with patch("llm.local_model.structured_output_v0_5.urllib.request.OpenerDirector.open", side_effect=http_error):
            with self.assertRaises(LocalModelError) as caught:
                chat_completion_structured(
                    base_url="http://127.0.0.1:1234/v1",
                    model="qwen3-14b",
                    messages=[{"role": "user", "content": "synthetic diagnostic only"}],
                )

        message = str(caught.exception)
        self.assertIn("HTTP 400", message)
        self.assertIn("Invalid schema for response_format", message)
        self.assertNotIn("nicht erreichbar oder Redirect verworfen", message)


if __name__ == "__main__":
    unittest.main()
