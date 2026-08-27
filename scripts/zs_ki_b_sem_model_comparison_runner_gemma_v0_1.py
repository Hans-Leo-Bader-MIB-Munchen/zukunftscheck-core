#!/usr/bin/env python3
"""Fail-closed Gemma semantic comparison runner.

Reuses the v1.1 qualification implementation while changing only the exact model
binding and run identity for the first model-comparison run. Prompt v0.6 and all
frozen semantic assets remain unchanged. Execution is blocked until the separate
Gemma authorization artifact is explicitly approved.

Important: the comparison wrapper temporarily binds shared runner modules and
restores their prior module state afterwards. This prevents import/test-order
state leakage into the historical v1.0/v1.1 runners.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_1 as v11

RUN_TYPE = "ZS-KI-B-SEM-MODELLVERGLEICH-GEMMA-SYNTHETIC-2026-012"
RUNNER_VERSION = "gemma-comparison-v0.1"
MODEL = "gemma-3-12b-it-qat"
PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_6"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_model_comparison_gemma_authorization_v0_1.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_model_comparison_gemma_result_v0_1.json"
REQUIRED_LOADED_CONTEXT_LENGTH = 32768
REQUEST_TIMEOUT_SECONDS = 1800.0
COMPARISON_PLAN_VERSION = "ZS-KI-B-SEM-MODELLVERGLEICH-NACH-PF2-REPRODUKTION-2026-001_v0.1"


def _state_targets() -> tuple[tuple[object, tuple[str, ...]], ...]:
    return (
        (v11, ("RUN_TYPE", "RUNNER_VERSION", "AUTH_PATH", "DEFAULT_OUTPUT")),
        (
            v11.v10,
            (
                "RUN_TYPE",
                "RUNNER_VERSION",
                "AUTH_PATH",
                "DEFAULT_OUTPUT",
                "REQUIRED_LOADED_CONTEXT_LENGTH",
                "REQUEST_TIMEOUT_SECONDS",
            ),
        ),
        (
            v11.v10.v09,
            (
                "RUN_TYPE",
                "RUNNER_VERSION",
                "AUTH_PATH",
                "DEFAULT_OUTPUT",
                "REQUIRED_LOADED_CONTEXT_LENGTH",
            ),
        ),
        (
            v11.v10.v09.base,
            ("RUN_TYPE", "RUNNER_VERSION", "AUTH_PATH", "DEFAULT_OUTPUT"),
        ),
    )


def _snapshot_state() -> list[tuple[object, str, Any]]:
    snapshot: list[tuple[object, str, Any]] = []
    for module, names in _state_targets():
        for name in names:
            snapshot.append((module, name, getattr(module, name)))
    return snapshot


def _restore_state(snapshot: list[tuple[object, str, Any]]) -> None:
    for module, name, value in reversed(snapshot):
        setattr(module, name, value)


def _configure() -> None:
    v11.RUN_TYPE = RUN_TYPE
    v11.RUNNER_VERSION = RUNNER_VERSION
    v11.AUTH_PATH = AUTH_PATH
    v11.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.RUN_TYPE = RUN_TYPE
    v11.v10.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.AUTH_PATH = AUTH_PATH
    v11.v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.REQUIRED_LOADED_CONTEXT_LENGTH = REQUIRED_LOADED_CONTEXT_LENGTH
    v11.v10.REQUEST_TIMEOUT_SECONDS = REQUEST_TIMEOUT_SECONDS
    v11.v10.v09.RUN_TYPE = RUN_TYPE
    v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.AUTH_PATH = AUTH_PATH
    v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.REQUIRED_LOADED_CONTEXT_LENGTH = REQUIRED_LOADED_CONTEXT_LENGTH
    v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.base.AUTH_PATH = AUTH_PATH
    v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT


@contextmanager
def _temporary_bindings() -> Iterator[None]:
    snapshot = _snapshot_state()
    _configure()
    try:
        yield
    finally:
        _restore_state(snapshot)


def validate_execution_authorization(model: str) -> dict[str, Any]:
    if model != MODEL:
        raise PermissionError(f"Gemma comparison requires exact model {MODEL!r}")
    with _temporary_bindings():
        auth = v11.validate_execution_authorization(model)
        if auth.get("model") != MODEL:
            raise PermissionError("authorization model does not match Gemma comparison model")
        if auth.get("comparison_plan_version") != COMPARISON_PLAN_VERSION:
            raise PermissionError("authorization comparison plan does not match")
        if auth.get("qwen3_14b_rerun_authorized") is not False:
            raise PermissionError("comparison authorization must keep qwen3-14b rerun blocked")
        return auth


def build_dry_run_manifest(*, model: str = MODEL, base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    if model != MODEL:
        raise PermissionError(f"Gemma comparison requires exact model {MODEL!r}")
    with _temporary_bindings():
        payload = v11.build_dry_run_manifest(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_MODEL_COMPARISON_GEMMA_V0_1"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["comparison_model"] = MODEL
    manifest["comparison_plan_version"] = COMPARISON_PLAN_VERSION
    manifest["reference_model"] = "qwen3-14b"
    manifest["reference_failure"] = "PF2 missing required 2.2/PF2 reproduced in 2026-010 and 2026-011"
    return payload


def _install_bindings() -> None:
    """Install comparison hooks only for the duration of main()."""
    _configure()
    v11.validate_execution_authorization = validate_execution_authorization
    v11.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    snapshot = _snapshot_state()
    original_validate = v11.validate_execution_authorization
    original_dry_run = v11.build_dry_run_manifest
    try:
        _install_bindings()
        return v11.main()
    finally:
        v11.validate_execution_authorization = original_validate
        v11.build_dry_run_manifest = original_dry_run
        _restore_state(snapshot)


if __name__ == "__main__":
    raise SystemExit(main())
