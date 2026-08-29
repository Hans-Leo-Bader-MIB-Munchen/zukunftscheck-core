#!/usr/bin/env python3
"""Qualification runner v1.5: Ministral timeout binding and provenance correction.

Model-free correction layer over v1.4. It preserves the frozen 16-case suite,
Human Gold, policy, Meaning Layer v0.7, prompt v0.6, Semantic Boundary v0.2 and
Generic System Composition v0.1, while fixing two defects observed in the first
v1.4 execution:
- the authorized 1800s request timeout is now passed to the structured transport;
- execution provenance reflects an authorized execution and observed preflight PASS.

This module does not itself authorize a model run. A new, separately versioned
single-use authorization artifact is required before any execution.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_4 as v14

RUNNER_VERSION = "v1.5"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-5-MINISTRAL-2026-016"
MODEL_REPOSITORY = v14.MODEL_REPOSITORY
RUNTIME_MODEL_ID = v14.RUNTIME_MODEL_ID
MODEL = RUNTIME_MODEL_ID
PROMPT_VERSION = v14.PROMPT_VERSION
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v15_ministral_model_run_authorization_v0_1.json"
BINDING_REVIEW_PATH = v14.BINDING_REVIEW_PATH
REQUIRED_PREFLIGHT_VERSION = v14.REQUIRED_PREFLIGHT_VERSION
REQUIRED_PREFLIGHT_TYPE = v14.REQUIRED_PREFLIGHT_TYPE
REQUIRED_PREFLIGHT_AUTH_PATH = v14.REQUIRED_PREFLIGHT_AUTH_PATH
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_5.json"
REQUIRED_CONTEXT = v14.REQUIRED_CONTEXT
REQUIRED_TIMEOUT = 1800

_ORIGINAL_TRANSPORT = v14.v13.v11.v10.v09.chat_completion_structured
_ORIGINAL_PERSIST = v14._ORIGINAL_PERSIST

_MODE_MAP = {
    "PRECONDITION_FAILED_SEM_QUALIFICATION_V0_9": "PRECONDITION_FAILED_SEM_QUALIFICATION_V1_5",
    "EXECUTING_SEM_QUALIFICATION_V0_9": "EXECUTING_SEM_QUALIFICATION_V1_5",
    "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_5",
    "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V1_5",
    "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V1_5",
}


def load(path: Path) -> dict[str, Any]:
    return v14.load(path)


def validate_runtime_binding_review() -> dict[str, Any]:
    return v14.validate_runtime_binding_review()


def _transport_with_required_timeout(*, base_url: str, model: str, messages: list[dict[str, str]], temperature: float = 0.0):
    return _ORIGINAL_TRANSPORT(
        base_url=base_url,
        model=model,
        messages=messages,
        temperature=temperature,
        timeout_seconds=REQUIRED_TIMEOUT,
    )


def normalize_execution_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode")
    if isinstance(mode, str) and mode in _MODE_MAP:
        payload["mode"] = _MODE_MAP[mode]
    manifest = payload.get("manifest")
    if isinstance(manifest, dict):
        manifest["run_type"] = RUN_TYPE
        manifest["runner_version"] = RUNNER_VERSION
        manifest["model_repository"] = MODEL_REPOSITORY
        manifest["runtime_model_id"] = RUNTIME_MODEL_ID
        manifest["required_request_timeout_seconds"] = REQUIRED_TIMEOUT
        manifest["request_timeout_seconds"] = REQUIRED_TIMEOUT
        observed = manifest.get("observed_model_request_count")
        execution_attempted = manifest.get("execution_attempted") is True
        manifest["model_contact_performed"] = isinstance(observed, int) and observed > 0
        if execution_attempted:
            manifest["execution_authorized"] = True
            manifest["model_run_authorized"] = True
        if isinstance(payload.get("preflight"), dict):
            manifest["preflight_pass_observed"] = True
    return payload


def _persist(payload: dict[str, Any], output: str) -> None:
    normalize_execution_provenance(payload)
    _ORIGINAL_PERSIST(payload, output)


def _authorization_matches(auth: dict[str, Any], model: str) -> bool:
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED"
        and auth.get("runner_version") == RUNNER_VERSION
        and auth.get("run_type") == RUN_TYPE
        and auth.get("model_repository") == MODEL_REPOSITORY
        and auth.get("runtime_model_id") == model == RUNTIME_MODEL_ID
        and auth.get("model") == RUNTIME_MODEL_ID
        and auth.get("prompt_version") == PROMPT_VERSION
        and auth.get("expected_model_request_count") == 16
        and auth.get("required_loaded_context_length") == REQUIRED_CONTEXT
        and auth.get("required_request_timeout_seconds") == REQUIRED_TIMEOUT
        and auth.get("generic_system_composition_required") is True
        and auth.get("generic_system_composition_version") == "semantic-system-composition-v0.1"
        and auth.get("qualified_completeness_pfs") == ["PF2", "PF9", "PF12"]
        and auth.get("synthetic_only") is True
        and auth.get("local_loopback_only") is True
        and auth.get("required_base_url") == "http://127.0.0.1:1234/v1"
        and auth.get("single_run_only") is True
        and auth.get("retry_count") == 0
        and auth.get("output_repair") is False
        and auth.get("remote_cloud") is False
        and auth.get("real_data") is False
        and auth.get("runtime_identity_binding_review_passed") is True
        and auth.get("required_preflight_version") == REQUIRED_PREFLIGHT_VERSION
        and auth.get("required_preflight_type") == REQUIRED_PREFLIGHT_TYPE
        and auth.get("required_preflight_authorization_path") == REQUIRED_PREFLIGHT_AUTH_PATH
        and auth.get("preflight_pass_required") is True
        and auth.get("preflight_pass_observed") is True
        and auth.get("qualification_authorization_must_follow_preflight_pass") is True
        and auth.get("authorization_consumed") is False
        and auth.get("execution_authorized") is True
        and auth.get("model_run_authorized") is True
        and auth.get("model_contact_authorized") is True
    )


def validate_execution_authorization(model: str) -> dict[str, Any]:
    validate_runtime_binding_review()
    if not AUTH_PATH.exists():
        raise PermissionError("v1.5 Ministral model run authorization artifact is absent")
    auth = load(AUTH_PATH)
    if not _authorization_matches(auth, model):
        raise PermissionError("v1.5 Ministral model run is not explicitly and exactly authorized")
    return auth


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    validate_runtime_binding_review()
    payload = v14._ORIGINAL_BUILD_DRY_RUN(model=model or RUNTIME_MODEL_ID, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_5"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["prompt_version"] = PROMPT_VERSION
    manifest["model_repository"] = MODEL_REPOSITORY
    manifest["runtime_model_id"] = RUNTIME_MODEL_ID
    manifest["required_loaded_context_length"] = REQUIRED_CONTEXT
    manifest["required_request_timeout_seconds"] = REQUIRED_TIMEOUT
    manifest["request_timeout_seconds"] = REQUIRED_TIMEOUT
    manifest["execution_authorized"] = False
    manifest["model_run_authorized"] = False
    manifest["model_contact_performed"] = False
    manifest["selected_candidate"] = MODEL_REPOSITORY
    manifest["selected_runtime_model_id"] = RUNTIME_MODEL_ID
    manifest["runtime_identity_binding_review_path"] = str(BINDING_REVIEW_PATH.relative_to(ROOT))
    manifest["required_preflight_version"] = REQUIRED_PREFLIGHT_VERSION
    manifest["required_preflight_type"] = REQUIRED_PREFLIGHT_TYPE
    manifest["required_preflight_authorization_path"] = REQUIRED_PREFLIGHT_AUTH_PATH
    manifest["preflight_pass_required"] = True
    manifest["preflight_pass_observed"] = False
    manifest["semantic_boundary_version"] = "semantic-boundary-v0.2"
    manifest["generic_system_composition_version"] = "semantic-system-composition-v0.1"
    manifest["qualified_completeness_pfs"] = ["PF2", "PF9", "PF12"]
    manifest["non_profile_cases_boundary_only"] = True
    manifest["authorization_path"] = str(AUTH_PATH.relative_to(ROOT))
    manifest["v14_failed_timeout_run_preserved"] = True
    return payload


def _configure() -> None:
    v14._configure()
    v14.v13.AUTH_PATH = AUTH_PATH
    v14.v13.RUN_TYPE = RUN_TYPE
    v14.v13.RUNNER_VERSION = RUNNER_VERSION
    v14.v13.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v14.v13.v11.AUTH_PATH = AUTH_PATH
    v14.v13.v11.RUN_TYPE = RUN_TYPE
    v14.v13.v11.RUNNER_VERSION = RUNNER_VERSION
    v14.v13.v11.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v14.v13.v11.v10.AUTH_PATH = AUTH_PATH
    v14.v13.v11.v10.RUN_TYPE = RUN_TYPE
    v14.v13.v11.v10.RUNNER_VERSION = RUNNER_VERSION
    v14.v13.v11.v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v14.v13.v11.v10.v09.AUTH_PATH = AUTH_PATH
    v14.v13.v11.v10.v09.RUN_TYPE = RUN_TYPE
    v14.v13.v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v14.v13.v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v14.v13.v11.v10.v09.base.AUTH_PATH = AUTH_PATH
    v14.v13.v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v14.v13.v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v14.v13.v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v14.v13.v11.v10.v09._persist = _persist
    v14.v13.v11.v10.v09.chat_completion_structured = _transport_with_required_timeout


def _install_bindings() -> None:
    _configure()
    v14.v13.v11.validate_execution_authorization = validate_execution_authorization
    v14.v13.v11.build_dry_run_manifest = build_dry_run_manifest
    v14.v13.v11.v10.validate_execution_authorization = validate_execution_authorization
    v14.v13.v11.v10.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    _install_bindings()
    return v14.v13.v11.main()


if __name__ == "__main__":
    raise SystemExit(main())
