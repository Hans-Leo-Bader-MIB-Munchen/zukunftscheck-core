#!/usr/bin/env python3
"""Fail-closed v1.0 wrapper for the frozen v0.7 semantic qualification.

Preserves v0.9 exact-model/context preflight and binds a longer local transport
request timeout (1800 seconds) before any additional authorized model execution.
The frozen suite, Human-Gold, policy, prompt, Meaning Layer, contract and semantic
boundary remain unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_9 as v09

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V0-7-FROZEN-2026-010"
RUNNER_VERSION = "v1.0"
EXPECTED_MODEL_REQUEST_COUNT = 16
REQUIRED_LOADED_CONTEXT_LENGTH = 32768
REQUEST_TIMEOUT_SECONDS = 1800.0
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_0.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_model_run_authorization_v0_3.json"
PREVIOUS_FAILURE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v09_execution_failure_timeout_v0_1.json"

_ORIGINAL_VALIDATE_AUTH = v09.validate_execution_authorization
_ORIGINAL_BUILD_DRY_RUN = v09.build_dry_run_manifest
_ORIGINAL_CHAT = v09.chat_completion_structured


def _configure_v09() -> None:
    v09.RUN_TYPE = RUN_TYPE
    v09.RUNNER_VERSION = RUNNER_VERSION
    v09.EXPECTED_MODEL_REQUEST_COUNT = EXPECTED_MODEL_REQUEST_COUNT
    v09.REQUIRED_LOADED_CONTEXT_LENGTH = REQUIRED_LOADED_CONTEXT_LENGTH
    v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v09.AUTH_PATH = AUTH_PATH
    v09.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH


def validate_execution_authorization(model: str) -> dict[str, Any]:
    _configure_v09()
    auth = _ORIGINAL_VALIDATE_AUTH(model)
    if auth.get("required_request_timeout_seconds") != int(REQUEST_TIMEOUT_SECONDS):
        raise PermissionError("authorization request-timeout requirement does not match runner requirement")
    return auth


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _configure_v09()
    payload = _ORIGINAL_BUILD_DRY_RUN(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_0"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["expected_model_request_count"] = EXPECTED_MODEL_REQUEST_COUNT
    manifest["required_loaded_context_length"] = REQUIRED_LOADED_CONTEXT_LENGTH
    manifest["request_timeout_seconds"] = int(REQUEST_TIMEOUT_SECONDS)
    manifest["previous_failed_run_recorded"] = PREVIOUS_FAILURE_PATH.exists()
    return payload


def chat_completion_structured(*, base_url: str, model: str, messages: list[dict[str, str]], temperature: float = 0.0):
    return _ORIGINAL_CHAT(
        base_url=base_url,
        model=model,
        messages=messages,
        temperature=temperature,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )


def _install_bindings() -> None:
    _configure_v09()
    v09.validate_execution_authorization = validate_execution_authorization
    v09.build_dry_run_manifest = build_dry_run_manifest
    v09.chat_completion_structured = chat_completion_structured


def main() -> int:
    _install_bindings()
    return v09.main()


if __name__ == "__main__":
    raise SystemExit(main())
