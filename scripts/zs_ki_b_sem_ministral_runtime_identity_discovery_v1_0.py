#!/usr/bin/env python3
"""Isolated LM Studio runtime-identity discovery with zero generation capability.

This step intentionally does not bind a runtime model id. It performs at most one
GET to the local LM Studio model inventory after separate explicit authorization,
records loaded instances and their metadata, and leaves binding to a later
model-free review step.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.local_model.openai_compatible import validate_local_base_url

DISCOVERY_VERSION = "v1.0"
DISCOVERY_TYPE = "ZS-KI-B-SEM-MINISTRAL-RUNTIME-IDENTITY-DISCOVERY-2026-001"
MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
REQUIRED_QUANTIZATION = "Q4_K_M"
REQUIRED_BASE_URL = "http://127.0.0.1:1234/v1"
REQUIRED_CONTEXT = 32768
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_runtime_identity_discovery_authorization_v0_1.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_ministral_runtime_identity_discovery_result_v1_0.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_exact_base_url(base_url: str) -> str:
    normalized = validate_local_base_url(base_url)
    if normalized.rstrip("/") != REQUIRED_BASE_URL.rstrip("/"):
        raise PermissionError(
            f"discovery base URL must exactly match {REQUIRED_BASE_URL!r}, got {normalized!r}"
        )
    return REQUIRED_BASE_URL


def _models_url(base_url: str) -> str:
    parts = urlsplit(_normalized_exact_base_url(base_url))
    return f"{parts.scheme}://{parts.netloc}/api/v1/models"


def _authorization_matches(auth: dict[str, Any]) -> bool:
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED_DISCOVERY_ONLY"
        and auth.get("discovery_version") == DISCOVERY_VERSION
        and auth.get("discovery_type") == DISCOVERY_TYPE
        and auth.get("model_repository") == MODEL_REPOSITORY
        and auth.get("required_quantization") == REQUIRED_QUANTIZATION
        and auth.get("required_base_url") == REQUIRED_BASE_URL
        and auth.get("required_loaded_context_length") == REQUIRED_CONTEXT
        and auth.get("localhost_inventory_contact_authorized") is True
        and auth.get("model_contact_authorized") is True
        and auth.get("generation_authorized") is False
        and auth.get("qualification_execution_authorized") is False
        and auth.get("generation_request_count_max") == 0
        and auth.get("inventory_request_count_max") == 1
        and auth.get("single_use_discovery_only") is True
        and auth.get("synthetic_only") is True
        and auth.get("local_loopback_only") is True
        and auth.get("remote_cloud") is False
        and auth.get("real_data") is False
        and auth.get("authorization_consumed") is False
    )


def validate_discovery_authorization() -> dict[str, Any]:
    auth = load(AUTH_PATH)
    if not _authorization_matches(auth):
        raise PermissionError("Ministral runtime-identity discovery is not explicitly and exactly authorized")
    return auth


def _extract_loaded_instances(payload: dict[str, Any]) -> list[dict[str, Any]]:
    models = payload.get("models")
    if not isinstance(models, list):
        raise RuntimeError("LM Studio inventory response has no models list")

    observed: list[dict[str, Any]] = []
    for model_row in models:
        if not isinstance(model_row, dict):
            continue
        quantization = model_row.get("quantization")
        quantization_name = quantization.get("name") if isinstance(quantization, dict) else None
        instances = model_row.get("loaded_instances") or []
        if not isinstance(instances, list):
            continue
        for instance in instances:
            if not isinstance(instance, dict):
                continue
            config = instance.get("config") or {}
            context_length = config.get("context_length") if isinstance(config, dict) else None
            observed.append(
                {
                    "model_key": model_row.get("key"),
                    "runtime_instance_id": instance.get("id"),
                    "loaded_context_length": context_length,
                    "max_context_length": model_row.get("max_context_length"),
                    "quantization": quantization_name,
                    "format": model_row.get("format"),
                }
            )
    return observed


def perform_discovery_only(*, base_url: str = REQUIRED_BASE_URL, timeout_seconds: float = 5.0) -> dict[str, Any]:
    exact_base_url = _normalized_exact_base_url(base_url)
    validate_discovery_authorization()
    url = _models_url(exact_base_url)
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            inventory = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"LM Studio identity discovery failed: {type(exc).__name__}: {exc}") from exc

    loaded = _extract_loaded_instances(inventory)
    if not loaded:
        raise RuntimeError("LM Studio identity discovery found no loaded model instances")

    compatible = [
        row
        for row in loaded
        if row.get("quantization") == REQUIRED_QUANTIZATION
        and isinstance(row.get("loaded_context_length"), int)
        and row["loaded_context_length"] >= REQUIRED_CONTEXT
    ]

    return {
        "mode": "RUNTIME_IDENTITY_DISCOVERY_OBSERVED_NOT_BOUND",
        "discovery_version": DISCOVERY_VERSION,
        "discovery_type": DISCOVERY_TYPE,
        "model_repository": MODEL_REPOSITORY,
        "required_quantization": REQUIRED_QUANTIZATION,
        "required_base_url": REQUIRED_BASE_URL,
        "required_loaded_context_length": REQUIRED_CONTEXT,
        "endpoint": url,
        "loaded_instances": loaded,
        "compatible_loaded_instances": compatible,
        "runtime_identity_bound": False,
        "binding_requires_separate_model_free_review": True,
        "inventory_request_count": 1,
        "generation_request_count": 0,
        "generation_authorized": False,
        "qualification_execution_authorized": False,
        "model_qualified": False,
    }


def build_dry_run_manifest() -> dict[str, Any]:
    auth = load(AUTH_PATH)
    return {
        "mode": "RUNTIME_IDENTITY_DISCOVERY_NOT_EXECUTED",
        "discovery_version": DISCOVERY_VERSION,
        "discovery_type": DISCOVERY_TYPE,
        "model_repository": MODEL_REPOSITORY,
        "authorization_status": auth.get("status"),
        "discovery_contact_authorized": _authorization_matches(auth),
        "runtime_identity_bound": False,
        "inventory_request_count": 0,
        "generation_request_count": 0,
        "generation_authorized": False,
        "qualification_execution_authorized": False,
        "model_qualified": False,
    }


def _persist(payload: dict[str, Any], output: str) -> None:
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-discovery", action="store_true")
    parser.add_argument("--base-url", default=REQUIRED_BASE_URL)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.execute_discovery:
        print(json.dumps(build_dry_run_manifest(), ensure_ascii=False, indent=2))
        return 0

    try:
        result = perform_discovery_only(base_url=args.base_url)
    except (PermissionError, RuntimeError) as exc:
        parser.error(str(exc))
    _persist(result, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
