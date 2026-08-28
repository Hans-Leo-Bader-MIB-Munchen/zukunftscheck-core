#!/usr/bin/env python3
"""Isolated Ministral preflight-only v1.1 using the API-observed runtime model id.

This path is deliberately separate from the qualification runner. It can perform at
most one local LM Studio inventory/preflight contact after a separately approved,
single-use authorization. It contains no generation loop and does not authorize
qualification execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_9 as v09
import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14
from llm.local_model.openai_compatible import validate_local_base_url

PREFLIGHT_VERSION = "v1.1"
PREFLIGHT_TYPE = "ZS-KI-B-SEM-MINISTRAL-PREFLIGHT-ONLY-2026-002"
MODEL_REPOSITORY = v14.MODEL_REPOSITORY
RUNTIME_MODEL_ID = v14.RUNTIME_MODEL_ID
REQUIRED_QUANTIZATION = "Q4_K_M"
REQUIRED_BASE_URL = "http://127.0.0.1:1234/v1"
REQUIRED_CONTEXT = 32768
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_only_authorization_v0_2.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_ministral_preflight_result_v1_1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_exact_base_url(base_url: str) -> str:
    normalized = validate_local_base_url(base_url)
    if normalized.rstrip("/") != REQUIRED_BASE_URL.rstrip("/"):
        raise PermissionError(
            f"preflight base URL must exactly match {REQUIRED_BASE_URL!r}, got {normalized!r}"
        )
    return REQUIRED_BASE_URL


def _authorization_matches(auth: dict[str, Any]) -> bool:
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED_PREFLIGHT_ONLY"
        and auth.get("preflight_version") == PREFLIGHT_VERSION
        and auth.get("preflight_type") == PREFLIGHT_TYPE
        and auth.get("model_repository") == MODEL_REPOSITORY
        and auth.get("runtime_model_id") == RUNTIME_MODEL_ID
        and auth.get("model") == RUNTIME_MODEL_ID
        and auth.get("required_quantization") == REQUIRED_QUANTIZATION
        and auth.get("required_base_url") == REQUIRED_BASE_URL
        and auth.get("required_loaded_context_length") == REQUIRED_CONTEXT
        and auth.get("download_authorized") is False
        and auth.get("model_load_authorized") is False
        and auth.get("localhost_preflight_authorized") is True
        and auth.get("model_contact_authorized") is True
        and auth.get("generation_authorized") is False
        and auth.get("qualification_execution_authorized") is False
        and auth.get("inventory_request_count_max") == 1
        and auth.get("generation_request_count_max") == 0
        and auth.get("single_use_preflight_only") is True
        and auth.get("synthetic_only") is True
        and auth.get("local_loopback_only") is True
        and auth.get("remote_cloud") is False
        and auth.get("real_data") is False
        and auth.get("runtime_identity_binding_review_passed") is True
        and auth.get("authorization_consumed") is False
    )


def validate_preflight_authorization() -> dict[str, Any]:
    auth = load(AUTH_PATH)
    if not _authorization_matches(auth):
        raise PermissionError("Ministral preflight-only v1.1 contact is not explicitly and exactly authorized")
    return auth


def build_dry_run_manifest() -> dict[str, Any]:
    auth = load(AUTH_PATH)
    return {
        "mode": "PREFLIGHT_ONLY_V1_1_NOT_EXECUTED",
        "preflight_version": PREFLIGHT_VERSION,
        "preflight_type": PREFLIGHT_TYPE,
        "model_repository": MODEL_REPOSITORY,
        "runtime_model_id": RUNTIME_MODEL_ID,
        "model": RUNTIME_MODEL_ID,
        "required_quantization": REQUIRED_QUANTIZATION,
        "required_base_url": REQUIRED_BASE_URL,
        "required_loaded_context_length": REQUIRED_CONTEXT,
        "authorization_status": auth.get("status"),
        "preflight_contact_authorized": _authorization_matches(auth),
        "inventory_request_count": 0,
        "generation_request_count": 0,
        "generation_authorized": False,
        "qualification_execution_authorized": False,
        "model_qualified": False,
    }


def perform_preflight_only(*, base_url: str = REQUIRED_BASE_URL) -> dict[str, Any]:
    exact_base_url = _normalized_exact_base_url(base_url)
    validate_preflight_authorization()

    preflight = v09.preflight_loaded_model(base_url=exact_base_url, model=RUNTIME_MODEL_ID)
    if preflight.get("loaded_instance_id") != RUNTIME_MODEL_ID:
        raise RuntimeError("loaded LM Studio instance id does not exactly match the bound runtime model id")
    if preflight.get("loaded_context_length", 0) < REQUIRED_CONTEXT:
        raise RuntimeError("loaded context is below the preflight requirement")
    if preflight.get("quantization") != REQUIRED_QUANTIZATION:
        raise RuntimeError(
            f"loaded quantization does not match required quantization: "
            f"{preflight.get('quantization')!r} != {REQUIRED_QUANTIZATION!r}"
        )
    if preflight.get("generation_request_count") != 0:
        raise RuntimeError("preflight-only path reported a non-zero generation request count")

    return {
        "mode": "PREFLIGHT_ONLY_V1_1_PASSED",
        "preflight_version": PREFLIGHT_VERSION,
        "preflight_type": PREFLIGHT_TYPE,
        "model_repository": MODEL_REPOSITORY,
        "runtime_model_id": RUNTIME_MODEL_ID,
        "model": RUNTIME_MODEL_ID,
        "required_quantization": REQUIRED_QUANTIZATION,
        "required_base_url": REQUIRED_BASE_URL,
        "required_loaded_context_length": REQUIRED_CONTEXT,
        "preflight": preflight,
        "inventory_request_count": 1,
        "generation_request_count": 0,
        "generation_authorized": False,
        "qualification_execution_authorized": False,
        "model_qualified": False,
    }


def _persist(payload: dict[str, Any], output: str) -> None:
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-preflight", action="store_true")
    parser.add_argument("--base-url", default=REQUIRED_BASE_URL)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.execute_preflight:
        print(json.dumps(build_dry_run_manifest(), ensure_ascii=False, indent=2))
        return 0

    try:
        result = perform_preflight_only(base_url=args.base_url)
    except (PermissionError, RuntimeError) as exc:
        parser.error(str(exc))
    _persist(result, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
