"""Model-free LM Studio-compatible bounded structured-output candidate for ZS-KI-B.

This module only builds a request payload. It contains no HTTP, localhost, model,
LM Studio, subprocess or generation execution path. The output cap uses `max_tokens`
because LM Studio documents that field for its OpenAI-compatible /v1/chat/completions
endpoint. Any future transmission requires a separately versioned transport and a
new explicit model-contact authorization.
"""
from __future__ import annotations

import copy
from typing import Any

from llm.local_model import structured_output_v0_6_candidate as previous

RESPONSE_FORMAT_NAME = previous.RESPONSE_FORMAT_NAME
OUTPUT_MODE_VERSION = "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.7-candidate"
MAX_TOKENS = 1024
REQUEST_TIMEOUT_SECONDS = previous.REQUEST_TIMEOUT_SECONDS
SCHEMA_PATH = previous.SCHEMA_PATH


def load_candidate_schema() -> dict[str, Any]:
    return previous.load_candidate_schema()


def build_response_format() -> dict[str, Any]:
    return previous.build_response_format()


def build_structured_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = MAX_TOKENS,
) -> dict[str, Any]:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be set")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool):
        raise ValueError("max_tokens must be an integer")
    if max_tokens <= 0 or max_tokens > MAX_TOKENS:
        raise ValueError(f"max_tokens must be within 1..{MAX_TOKENS}")
    return {
        "model": model,
        "messages": copy.deepcopy(messages),
        "response_format": build_response_format(),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
