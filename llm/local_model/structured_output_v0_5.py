"""Versioned localhost-only structured-output transport for ZS-KI-B v0.5.

Preserves the v0.4 localhost-only request behavior and 600s default timeout,
but binds structured generation to semantic contract v0.2. No retry, repair,
tool use, web access, MCP call or remote transmission is introduced.
"""
from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from llm.local_model.openai_compatible import LocalModelError, _RejectRedirects, validate_local_base_url

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_SCHEMA_PATH = ROOT / "domains" / "zukunftscheck" / "schema" / "b_semantic_contract_v0_2.schema.json"
RESPONSE_FORMAT_NAME = "zs_ki_b_semantic_response_v0_2"
OUTPUT_MODE_VERSION = "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.5"
DEFAULT_TIMEOUT_SECONDS = 600.0


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


def load_semantic_schema() -> dict[str, Any]:
    schema = json.loads(SEMANTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise LocalModelError("Semantikvertrag ist kein JSON-Schema-Objekt")
    return schema


def build_response_format() -> dict[str, Any]:
    schema = _without_schema_annotations(load_semantic_schema())
    return {
        "type": "json_schema",
        "json_schema": {
            "name": RESPONSE_FORMAT_NAME,
            "strict": True,
            "schema": schema,
        },
    }


def build_structured_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
) -> dict[str, Any]:
    if not model.strip():
        raise LocalModelError("model muss gesetzt sein")
    return {
        "model": model,
        "messages": messages,
        "response_format": build_response_format(),
        "temperature": temperature,
        "stream": False,
    }


def chat_completion_structured(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, dict[str, Any]]:
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
    except urllib.error.HTTPError as exc:
        try:
            response_body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            response_body = ""
        detail = response_body or str(exc.reason or exc)
        raise LocalModelError(f"lokaler strukturierter Modellendpunkt HTTP {exc.code}: {detail}") from exc
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
