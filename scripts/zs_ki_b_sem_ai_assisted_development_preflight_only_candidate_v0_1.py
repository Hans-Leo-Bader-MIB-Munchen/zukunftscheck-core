#!/usr/bin/env python3
"""Fail-closed preflight-only candidate for the 24-case synthetic development path.

No localhost/model contact occurs unless a separately approved preflight authorization
is supplied to execute_preflight(). The default CLI path is static validation only.
The preflight performs identity/context inspection only and has generation_request_count=0.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_BINDING_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_runtime_binding_candidate_v0_1.json"

PREFLIGHT_VERSION = "v0.1-preflight-only-candidate-not-authorized"
PREFLIGHT_TYPE = "ZS-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-PREFLIGHT-ONLY-2026-001"
EXPECTED_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
EXPECTED_QUANTIZATION = "Q4_K_M"
EXPECTED_BASE_URL = "http://127.0.0.1:1234/v1"
REQUIRED_CONTEXT_MIN = 32768
GENERATION_REQUEST_COUNT = 0
HARD_STOP = "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION"

ProbeCallable = Callable[..., dict[str, Any]]


def load_runtime_binding() -> dict[str, Any]:
    return json.loads(RUNTIME_BINDING_PATH.read_text(encoding="utf-8"))


def validate_static_binding() -> dict[str, Any]:
    binding = load_runtime_binding()
    runtime = binding["runtime_parameters"]
    if binding.get("execution_authorized") is not False:
        raise PermissionError("runtime binding must remain non-authorizing")
    if binding.get("model_contact_authorized") is not False:
        raise PermissionError("runtime binding must remain non-authorizing")
    if binding.get("preflight_authorized") is not False:
        raise PermissionError("runtime binding must remain non-authorizing")
    if runtime.get("model_id") != EXPECTED_MODEL_ID:
        raise ValueError("model id binding changed")
    if runtime.get("model_repository") != EXPECTED_MODEL_REPOSITORY:
        raise ValueError("model repository binding changed")
    if runtime.get("quantization") != EXPECTED_QUANTIZATION:
        raise ValueError("quantization binding changed")
    if runtime.get("endpoint_base_url") != EXPECTED_BASE_URL:
        raise ValueError("base URL binding changed")
    if int(runtime.get("required_loaded_context_min", 0)) != REQUIRED_CONTEXT_MIN:
        raise ValueError("required context binding changed")
    return binding


def validate_preflight_authorization(authorization: dict[str, Any] | None) -> None:
    if not isinstance(authorization, dict):
        raise PermissionError("separate preflight authorization missing")
    if authorization.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("preflight explicit user approval missing")
    if authorization.get("preflight_authorized") is not True:
        raise PermissionError("preflight authorization flag missing")
    if authorization.get("model_contact_authorized") is not True:
        raise PermissionError("model-contact authorization for identity probe missing")
    if authorization.get("execution_authorized") is not False:
        raise PermissionError("development execution must remain unauthorized during preflight")
    if authorization.get("expected_preflight_run_count") != 1:
        raise PermissionError("preflight scope must be exactly one")
    if authorization.get("expected_generation_request_count") != 0:
        raise PermissionError("preflight must authorize zero generation requests")


def _default_probe(*, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    if base_url != EXPECTED_BASE_URL:
        raise PermissionError("unexpected preflight base URL")
    req = urllib.request.Request(base_url + "/models", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"preflight identity probe failed: {exc}") from exc
    return envelope


def normalize_probe_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize provider-specific probe metadata without performing generation."""
    if not isinstance(raw, dict):
        raise ValueError("preflight probe response must be an object")
    model_id = raw.get("model_id") or raw.get("id")
    model_repository = raw.get("model_repository") or raw.get("repository")
    quantization = raw.get("quantization")
    loaded_context = raw.get("loaded_context") or raw.get("context_length")
    return {
        "model_id": model_id,
        "model_repository": model_repository,
        "quantization": quantization,
        "loaded_context": loaded_context,
    }


def evaluate_probe(normalized: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "model_id_exact": normalized.get("model_id") == EXPECTED_MODEL_ID,
        "model_repository_exact": normalized.get("model_repository") == EXPECTED_MODEL_REPOSITORY,
        "quantization_exact": normalized.get("quantization") == EXPECTED_QUANTIZATION,
        "loaded_context_min": isinstance(normalized.get("loaded_context"), (int, float)) and int(normalized["loaded_context"]) >= REQUIRED_CONTEXT_MIN,
    }
    passed = all(checks.values())
    return {
        "status": "PASS_FROZEN_CANDIDATE" if passed else "FAIL_CLOSED",
        "preflight_type": PREFLIGHT_TYPE,
        "preflight_version": PREFLIGHT_VERSION,
        "checks": checks,
        "model_id": normalized.get("model_id"),
        "model_repository": normalized.get("model_repository"),
        "quantization": normalized.get("quantization"),
        "loaded_context": normalized.get("loaded_context"),
        "generation_request_count": 0,
        "development_execution_authorized": False,
        "qualification_claim_allowed": False,
    }


def execute_preflight(*, authorization: dict[str, Any], probe: ProbeCallable | None = None) -> dict[str, Any]:
    binding = validate_static_binding()
    validate_preflight_authorization(authorization)
    timeout_seconds = float(binding["runtime_parameters"]["request_timeout_seconds"])
    probe_fn = probe or _default_probe
    raw = probe_fn(base_url=EXPECTED_BASE_URL, timeout_seconds=timeout_seconds)
    normalized = normalize_probe_result(raw)
    return evaluate_probe(normalized)


def main() -> int:
    validate_static_binding()
    print(json.dumps({
        "status": "STATIC_PREFLIGHT_CANDIDATE_NOT_AUTHORIZED",
        "preflight_version": PREFLIGHT_VERSION,
        "expected_preflight_run_count": 1,
        "generation_request_count": 0,
        "hard_stop": HARD_STOP,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
