"""Versioned localhost-only structured-output transport for ZS-KI-B.

v0.3 preserves the v0.2 payload/schema behavior and raises only the default
local request timeout from 120s to 300s. No retry, repair, tool use, web access,
MCP call or remote transmission is introduced.
"""
from __future__ import annotations

from llm.local_model.structured_output_v0_2 import (
    build_response_format,
    build_structured_payload,
    load_semantic_schema,
)
from llm.local_model.openai_compatible import LocalModelError, _RejectRedirects, validate_local_base_url

import json
import urllib.error
import urllib.request
from typing import Any

OUTPUT_MODE_VERSION = "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.3"
DEFAULT_TIMEOUT_SECONDS = 300.0


def chat_completion_structured(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, dict[str, Any]]:
    """Execute exactly one structured local chat-completion request."""
    base = validate_local_base_url(base_url)
    payload = build_structured_payload(model=model, messages=messages, temperature=temperature)
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(_RejectRedirects())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LocalModelError(f"lokaler strukturierter Modellendpunkt nicht erreichbar oder Redirect verworfen: {exc}") from exc

    try:
        envelope = json.loads(raw)
        content = envelope["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise LocalModelError("ungültige OpenAI-kompatible Antwortstruktur") from exc
    if not isinstance(content, str) or not content.strip():
        raise LocalModelError("Modellantwort enthält keinen Text")
    return content, envelope
