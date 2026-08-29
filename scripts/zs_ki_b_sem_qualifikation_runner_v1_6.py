#!/usr/bin/env python3
"""Model-free v1.6 gate-state correction after the v1.5 timeout run.

This successor intentionally does not authorize or execute model contact. It exists
only to correct the dry-run gate representation: a previously preserved successful
Ministral preflight must be reported as observed instead of being hard-coded false.
A separate future authorization architecture is required before any v1.6 execution.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import scripts.zs_ki_b_sem_qualifikation_runner_v1_5 as v15

ROOT = Path(__file__).resolve().parents[1]
RUNNER_VERSION = "v1.6"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-6-MINISTRAL-2026-017"
RUNTIME_MODEL_ID = v15.RUNTIME_MODEL_ID
MODEL_REPOSITORY = v15.MODEL_REPOSITORY
REQUIRED_TIMEOUT = v15.REQUIRED_TIMEOUT
PREFLIGHT_RESULT_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_preflight_result_v1_1_preserved_v0_1.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v16_ministral_model_run_authorization_v0_1.json"


def _preserved_preflight_pass_observed() -> bool:
    if not PREFLIGHT_RESULT_PATH.exists():
        return False
    try:
        payload = json.loads(PREFLIGHT_RESULT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    preflight = payload.get("preflight")
    return (
        payload.get("status") == "PRESERVED_PREFLIGHT_PASS"
        and isinstance(preflight, dict)
        and payload.get("runtime_model_id") == RUNTIME_MODEL_ID
        and preflight.get("model_key") == RUNTIME_MODEL_ID
        and preflight.get("loaded_instance_id") == RUNTIME_MODEL_ID
        and preflight.get("loaded_context_length") == 32768
        and preflight.get("quantization") == "Q4_K_M"
        and payload.get("generation_request_count") == 0
    )


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    payload = v15.build_dry_run_manifest(model=model or RUNTIME_MODEL_ID, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_6"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["preflight_pass_observed"] = _preserved_preflight_pass_observed()
    manifest["authorization_path"] = str(AUTH_PATH.relative_to(ROOT))
    manifest["execution_authorized"] = False
    manifest["model_run_authorized"] = False
    manifest["model_contact_performed"] = False
    manifest["model_qualified"] = False
    manifest["v15_timeout_failure_requires_analysis_before_new_execution"] = True
    return payload


def validate_execution_authorization(model: str) -> dict[str, Any]:
    raise PermissionError(
        "v1.6 execution is not authorized; this revision is model-free gate-state correction only"
    )


if __name__ == "__main__":
    raise SystemExit("v1.6 is model-free gate-state correction only; no execution entry point is enabled")
