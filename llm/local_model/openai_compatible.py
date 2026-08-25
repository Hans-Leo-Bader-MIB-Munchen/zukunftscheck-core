"""Minimal localhost-only adapter for an OpenAI-compatible local inference server.

Current ZS-KI-B smoke-test policy deliberately rejects non-loopback endpoints.
No web, tools, MCP or cloud integration is implemented here.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class LocalModelError(RuntimeError):
    pass


def validate_local_base_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise LocalModelError("base_url muss http oder https verwenden")
    if parsed.hostname not in LOOPBACK_HOSTS:
        raise LocalModelError("nur Loopback-/localhost-Endpunkte sind in diesem Block zulässig")
    if parsed.username or parsed.password:
        raise LocalModelError("Credentials in base_url sind nicht zulässig")
    return base_url.rstrip("/")


def chat_completion(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    timeout_seconds: float = 120.0,
) -> tuple[str, dict[str, Any]]:
    base = validate_local_base_url(base_url)
    if not model.strip():
        raise LocalModelError("model muss gesetzt sein")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LocalModelError(f"lokaler Modellendpunkt nicht erreichbar: {exc}") from exc

    try:
        envelope = json.loads(raw)
        content = envelope["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise LocalModelError("ungültige OpenAI-kompatible Antwortstruktur") from exc
    if not isinstance(content, str) or not content.strip():
        raise LocalModelError("Modellantwort enthält keinen Text")
    return content, envelope
