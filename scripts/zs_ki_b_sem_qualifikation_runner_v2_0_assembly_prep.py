#!/usr/bin/env python3
"""Model-free assembly preparation for a future executable qualification runner.

The module assembles the future call boundary but intentionally has no valid
execution authorization. Authorization is checked before the injected transport
callable can be reached. No localhost/model contact is performed by this module.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_9_readiness_prep as v19
import scripts.zs_ki_b_sem_qualifikation_runner_v1_8_prep as v18

RUNNER_VERSION = "v2.0-assembly-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-0-EXECUTABLE-ASSEMBLY-PREP-2026-021"
BASE_URL = v19.EXPECTED_BASE_URL
TIMEOUT_SECONDS = v19.EXPECTED_TIMEOUT_SECONDS
RUNTIME_MODEL_ID = v19.EXPECTED_MODEL_ID
MODEL_REPOSITORY = v19.EXPECTED_MODEL_REPOSITORY

TransportCallable = Callable[..., tuple[str, dict[str, Any]]]


def validate_execution_authorization() -> dict[str, Any]:
    raise PermissionError(
        "v2.0 assembly prep has no execution authorization; explicit single-use model-contact authorization is required"
    )


def build_assembly_report() -> dict[str, Any]:
    readiness = v19.build_readiness_report()
    request = v18.build_candidate_request_preview()
    checks = {
        "v19_readiness_pass": readiness.get("status") == "PASS",
        "v19_not_ready_to_execute": readiness.get("ready_to_execute") is False,
        "runtime_model_id_exact": request.get("model") == RUNTIME_MODEL_ID,
        "max_tokens_exact": request.get("max_tokens") == v19.EXPECTED_MAX_TOKENS,
        "stream_false": request.get("stream") is False,
        "timeout_exact": TIMEOUT_SECONDS == 1800.0,
        "loopback_base_url_exact": BASE_URL == "http://127.0.0.1:1234/v1",
        "prompt_hash_pinned": readiness["checks"].get("prompt_sha256_exact") is True,
        "response_format_hash_pinned": readiness["checks"].get("response_format_sha256_exact") is True,
        "full_reference_questions": readiness["checks"].get("full_reference_questions") is True,
        "full_meaning_layer": readiness["checks"].get("full_meaning_layer") is True,
        "retry_zero": readiness["checks"].get("retry_zero") is True,
        "output_repair_false": readiness["checks"].get("output_repair_false") is True,
        "remote_cloud_false": readiness["checks"].get("remote_cloud_false") is True,
        "real_data_false": readiness["checks"].get("real_data_false") is True,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_EXECUTABLE_RUNNER_ASSEMBLY_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "checks": checks,
        "assembly_ready": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "authorization_artifact_created": False,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def execute_once(*, transport: TransportCallable) -> tuple[str, dict[str, Any]]:
    """Future execution boundary; fail-closed before transport in the current block."""
    validate_execution_authorization()
    request = v18.build_candidate_request_preview()
    return transport(
        base_url=BASE_URL,
        payload=request,
        timeout_seconds=TIMEOUT_SECONDS,
    )


def main() -> int:
    report = build_assembly_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
