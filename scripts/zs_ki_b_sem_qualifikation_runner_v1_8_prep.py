#!/usr/bin/env python3
"""Model-free v1.8 LM Studio token-cap compatibility preparation.

Builds the exact candidate request preview using LM Studio's documented `max_tokens`
parameter while preserving the v1.7 candidate prompt, schema and full 67/67 semantic
context. No request is transmitted. No preflight or model execution path is exposed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from llm.smoketest import canonical_json
from llm.local_model import structured_output_v0_7_candidate as bounded
import scripts.zs_ki_b_sem_qualifikation_runner_v1_7_prep as v17

ROOT = Path(__file__).resolve().parents[1]
RUNNER_VERSION = "v1.8-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-8-LMSTUDIO-TOKEN-CAP-PREP-2026-019"
RUNTIME_MODEL_ID = v17.RUNTIME_MODEL_ID
MODEL_REPOSITORY = v17.MODEL_REPOSITORY
PROMPT_VERSION = v17.PROMPT_VERSION
PROMPT_PATH = v17.PROMPT_PATH
CANDIDATE_SCHEMA_PATH = bounded.SCHEMA_PATH
ACTIVE_SCHEMA_PATH = v17.ACTIVE_SCHEMA_PATH
TARGET_CASE_ID = v17.TARGET_CASE_ID


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_candidate_messages(case_id: str = TARGET_CASE_ID) -> list[dict[str, str]]:
    return v17.build_candidate_messages(case_id)


def build_candidate_request_preview(
    *, case_id: str = TARGET_CASE_ID, model: str = RUNTIME_MODEL_ID
) -> dict[str, Any]:
    return bounded.build_structured_payload(
        model=model,
        messages=build_candidate_messages(case_id),
        max_tokens=bounded.MAX_TOKENS,
    )


def build_dry_run_manifest() -> dict[str, Any]:
    payload = v17.build_dry_run_manifest()
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_8_LMSTUDIO_TOKEN_CAP_PREP"
    manifest = payload["manifest"]
    messages = build_candidate_messages()
    response_format = bounded.build_response_format()
    manifest.pop("max_completion_tokens", None)
    manifest.update(
        {
            "run_type": RUN_TYPE,
            "runner_version": RUNNER_VERSION,
            "prompt_version": PROMPT_VERSION,
            "prompt_sha256": _sha256_text(messages[0]["content"]),
            "candidate_output_mode_version": bounded.OUTPUT_MODE_VERSION,
            "response_format_sha256": _sha256_text(canonical_json(response_format)),
            "candidate_response_format_sha256": _sha256_text(canonical_json(response_format)),
            "output_token_parameter": "max_tokens",
            "max_tokens": bounded.MAX_TOKENS,
            "request_timeout_seconds": bounded.REQUEST_TIMEOUT_SECONDS,
            "lmstudio_documented_chat_completion_parameter_binding_prepared": True,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "model_contact_performed": False,
            "authorization_path": None,
            "model_qualified": False,
            "new_explicit_model_contact_authorization_required_before_any_execution": True,
        }
    )
    return payload


def validate_execution_authorization(model: str = RUNTIME_MODEL_ID) -> dict[str, Any]:
    raise PermissionError(
        "v1.8 LM Studio token-cap prep is model-free only; no execution authorization exists"
    )


def main() -> int:
    print(json.dumps(build_dry_run_manifest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
