#!/usr/bin/env python3
"""Fail-closed v1.1 qualification configuration using prompt v0.6.

Reuses the proven v1.0 local-model/context/timeout controls while binding the
separately versioned prompt v0.6. The frozen 16-case suite, Human-Gold, policy,
Meaning Layer, semantic contract and boundary remain unchanged. Execution is
blocked unless the separately versioned v1.1 authorization is explicitly approved.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_0 as v10

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-1-PROMPT-V0-6-2026-011"
RUNNER_VERSION = "v1.1"
PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_6"
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v11_model_run_authorization_v0_1.json"
PREVIOUS_FAILURE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v10_execution_failure_gold_pf2_v0_1.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_1.json"


def _configure() -> None:
    v10.RUN_TYPE = RUN_TYPE
    v10.RUNNER_VERSION = RUNNER_VERSION
    v10.AUTH_PATH = AUTH_PATH
    v10.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH
    v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v10.v09.RUN_TYPE = RUN_TYPE
    v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v10.v09.AUTH_PATH = AUTH_PATH
    v10.v09.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH
    v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v10.v09.base.RUN_TYPE = RUN_TYPE
    v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v10.v09.base.AUTH_PATH = AUTH_PATH
    v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v10.v09.base.PROMPT_VERSION = PROMPT_VERSION
    v10.v09.base.PROMPT_PATH = PROMPT_PATH


def validate_execution_authorization(model: str) -> dict[str, Any]:
    _configure()
    auth = v10.validate_execution_authorization(model)
    if auth.get("prompt_version") != PROMPT_VERSION:
        raise PermissionError("authorization prompt version does not match runner prompt version")
    return auth


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _configure()
    payload = v10.build_dry_run_manifest(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_1"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["prompt_version"] = PROMPT_VERSION
    manifest["prompt_change_only"] = True
    manifest["previous_semantic_failure_recorded"] = PREVIOUS_FAILURE_PATH.exists()
    return payload


def _install_bindings() -> None:
    _configure()
    v10.validate_execution_authorization = validate_execution_authorization
    v10.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    _install_bindings()
    return v10.main()


if __name__ == "__main__":
    raise SystemExit(main())
