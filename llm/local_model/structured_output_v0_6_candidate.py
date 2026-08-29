"""Model-free bounded structured-output candidate for ZS-KI-B v1.7.

This module intentionally contains no HTTP, localhost, model, LM Studio, subprocess,
or generation execution path. It only builds the bounded response format and request
payload that a future separately authorized transport revision may consume.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "domains" / "zukunftscheck" / "schema" / "b_semantic_contract_v0_3_candidate.schema.json"
RESPONSE_FORMAT_NAME = "zs_ki_b_semantic_response_v0_3_candidate"
OUTPUT_MODE_VERSION = "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.6-candidate"
MAX_COMPLETION_TOKENS = 1024
REQUEST_TIMEOUT_SECONDS = 1800.0


def _without_schema_annotations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_schema_annotations(item)
            for key, item in value.items()
            if key not in {"$schema", "$id", "title", "description"}
        }
    if isinstance(value, list):
        return [_without_schema_annotations(item) for item in value]
    return copy.deepcopy(value)


def load_candidate_schema() -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("bounded semantic candidate schema must be a JSON object")
    return schema


def build_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": RESPONSE_FORMAT_NAME,
            "strict": True,
            "schema": _without_schema_annotations(load_candidate_schema()),
        },
    }


def build_structured_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_completion_tokens: int = MAX_COMPLETION_TOKENS,
) -> dict[str, Any]:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be set")
    if not isinstance(max_completion_tokens, int) or isinstance(max_completion_tokens, bool):
        raise ValueError("max_completion_tokens must be an integer")
    if max_completion_tokens <= 0 or max_completion_tokens > MAX_COMPLETION_TOKENS:
        raise ValueError(f"max_completion_tokens must be within 1..{MAX_COMPLETION_TOKENS}")
    return {
        "model": model,
        "messages": copy.deepcopy(messages),
        "response_format": build_response_format(),
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
        "stream": False,
    }
