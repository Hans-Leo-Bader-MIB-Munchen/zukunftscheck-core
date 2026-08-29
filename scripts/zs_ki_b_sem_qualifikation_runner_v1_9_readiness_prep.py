#!/usr/bin/env python3
"""Model-free execution-readiness preparation for a future ZS-KI-B qualification runner.

This module validates the intended future request binding without transmitting any
request. It exposes no HTTP, localhost, preflight or model-generation path and creates
no authorization artifact. A separately versioned executable runner and a new explicit
single-use model-contact authorization remain mandatory before any future execution.
"""
from __future__ import annotations

import json
from typing import Any

import scripts.zs_ki_b_sem_qualifikation_runner_v1_8_prep as v18

RUNNER_VERSION = "v1.9-readiness-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-9-EXECUTION-READINESS-PREP-2026-020"
EXPECTED_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
EXPECTED_CONTRACT = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate"
EXPECTED_PROMPT = "zs_ki_b_sem_qualifikation_system_v0_7_candidate"
EXPECTED_OUTPUT_MODE = "ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.7-candidate"
EXPECTED_PROMPT_SHA256 = "a8e51fecbadbd674a8c36f762b234c2e6d157e84d53e0666204d0a998291eecc"
EXPECTED_RESPONSE_FORMAT_SHA256 = "4bf81e884cdd478f22083c61db404aeb84ca3c4fe3cf64ab9621ada400367e43"
EXPECTED_BASE_URL = "http://127.0.0.1:1234/v1"
EXPECTED_MAX_TOKENS = 1024
EXPECTED_TIMEOUT_SECONDS = 1800.0
EXPECTED_REFERENCE_QUESTION_COUNT = 67
EXPECTED_MEANING_COUNT = 67


def build_readiness_report() -> dict[str, Any]:
    payload = v18.build_dry_run_manifest()
    manifest = payload["manifest"]
    request = v18.build_candidate_request_preview()
    response_format = request.get("response_format", {})
    json_schema = response_format.get("json_schema", {}) if isinstance(response_format, dict) else {}

    checks = {
        "runtime_model_id_exact": manifest.get("runtime_model_id") == EXPECTED_MODEL_ID,
        "model_repository_exact": manifest.get("model_repository") == EXPECTED_MODEL_REPOSITORY,
        "prompt_exact": manifest.get("prompt_version") == EXPECTED_PROMPT,
        "prompt_sha256_exact": manifest.get("prompt_sha256") == EXPECTED_PROMPT_SHA256,
        "contract_exact": manifest.get("contract_version") == EXPECTED_CONTRACT,
        "output_mode_exact": manifest.get("candidate_output_mode_version") == EXPECTED_OUTPUT_MODE,
        "response_format_sha256_exact": manifest.get("candidate_response_format_sha256") == EXPECTED_RESPONSE_FORMAT_SHA256,
        "full_reference_questions": manifest.get("full_reference_question_count") == EXPECTED_REFERENCE_QUESTION_COUNT,
        "full_meaning_layer": manifest.get("full_meaning_count") == EXPECTED_MEANING_COUNT,
        "no_context_reduction": manifest.get("context_reduction_performed") is False,
        "no_pf_prefiltering": manifest.get("pf_prefiltering_performed") is False,
        "retry_zero": manifest.get("retry_count") == 0,
        "output_repair_false": manifest.get("output_repair") is False,
        "remote_cloud_false": manifest.get("remote_cloud") is False,
        "real_data_false": manifest.get("real_data") is False,
        "loopback_base_url_exact": manifest.get("base_url") == EXPECTED_BASE_URL,
        "timeout_design_exact": manifest.get("request_timeout_seconds") == EXPECTED_TIMEOUT_SECONDS,
        "max_tokens_exact": request.get("max_tokens") == EXPECTED_MAX_TOKENS,
        "no_max_completion_tokens": "max_completion_tokens" not in request,
        "stream_false": request.get("stream") is False,
        "strict_json_schema": response_format.get("type") == "json_schema" and json_schema.get("strict") is True,
        "execution_not_authorized": manifest.get("execution_authorized") is False,
        "model_run_not_authorized": manifest.get("model_run_authorized") is False,
        "model_contact_not_authorized": manifest.get("model_contact_authorized") is False,
        "model_contact_not_performed": manifest.get("model_contact_performed") is False,
        "authorization_path_absent": manifest.get("authorization_path") is None,
        "model_not_qualified": manifest.get("model_qualified") is False,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_EXECUTION_READINESS_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "checks": checks,
        "technical_binding_ready_for_future_authorization_design": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "authorization_artifact_created": False,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def validate_execution_authorization() -> dict[str, Any]:
    raise PermissionError(
        "v1.9 execution-readiness prep is model-free only; no execution authorization exists"
    )


def main() -> int:
    report = build_readiness_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
