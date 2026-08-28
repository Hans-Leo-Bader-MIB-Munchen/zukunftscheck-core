#!/usr/bin/env python3
"""Qualification runner v1.4: Ministral binding with independent closed authorization gate.

This model-free layer preserves the frozen 16-case qualification suite, Human Gold,
policy, Meaning Layer v0.7, prompt v0.6, Semantic Boundary v0.2 and Generic System
Composition v0.1 from runner v1.3. It separates repository provenance from the exact
LM Studio runtime/API model id observed by the authorized discovery step.

No model execution is authorized by this module. Execution must fail closed unless a
separately versioned v1.4 authorization artifact exactly matches the runner, runtime
model id, repository provenance, prompt and one-shot constraints.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as v13

RUNNER_VERSION = "v1.4"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015"
MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
RUNTIME_MODEL_ID = "ministral-3-14b-instruct-2512"
MODEL = RUNTIME_MODEL_ID
PROMPT_VERSION = v13.PROMPT_VERSION
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_v0_1.json"
BINDING_REVIEW_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v14_ministral_runtime_identity_binding_review_v0_1.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_4.json"
REQUIRED_CONTEXT = 32768
REQUIRED_TIMEOUT = 1800

_ORIGINAL_BUILD_DRY_RUN = v13.build_dry_run_manifest
_ORIGINAL_PERSIST = v13.v11.v10.v09._persist

_MODE_MAP = {
    "PRECONDITION_FAILED_SEM_QUALIFICATION_V0_9": "PRECONDITION_FAILED_SEM_QUALIFICATION_V1_4",
    "EXECUTING_SEM_QUALIFICATION_V0_9": "EXECUTING_SEM_QUALIFICATION_V1_4",
    "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_4",
    "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V1_4",
    "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V1_4",
}


def load(path: Path) -> dict[str, Any]:
    return v13.load(path)


def validate_runtime_binding_review() -> dict[str, Any]:
    review = load(BINDING_REVIEW_PATH)
    if review.get("status") != "MODEL_FREE_BINDING_REVIEW_PASSED":
        raise PermissionError("v1.4 runtime identity binding review is not passed")
    if review.get("model_repository") != MODEL_REPOSITORY:
        raise PermissionError("v1.4 repository identity does not match binding review")
    if review.get("runtime_model_id") != RUNTIME_MODEL_ID:
        raise PermissionError("v1.4 runtime model id does not match binding review")
    if review.get("runtime_identity_bound_for_runner_configuration") is not True:
        raise PermissionError("v1.4 runtime identity is not bound for runner configuration")
    if review.get("new_inventory_contact_performed") is not False:
        raise PermissionError("binding review must remain model-free")
    if review.get("generation_request_count") != 0:
        raise PermissionError("binding review must contain zero generation requests")
    return review


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
        observed = manifest.get("observed_model_request_count")
        manifest["model_contact_performed"] = isinstance(observed, int) and observed > 0
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
        and auth.get("authorization_consumed") is False
        and auth.get("execution_authorized") is True
        and auth.get("model_run_authorized") is True
        and auth.get("model_contact_authorized") is True
    )


def validate_execution_authorization(model: str) -> dict[str, Any]:
    validate_runtime_binding_review()
    auth = load(AUTH_PATH)
    if not _authorization_matches(auth, model):
        raise PermissionError("v1.4 Ministral model run is not explicitly and exactly authorized")
    return auth


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    validate_runtime_binding_review()
    payload = _ORIGINAL_BUILD_DRY_RUN(model=model or RUNTIME_MODEL_ID, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_4"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["prompt_version"] = PROMPT_VERSION
    manifest["model_repository"] = MODEL_REPOSITORY
    manifest["runtime_model_id"] = RUNTIME_MODEL_ID
    manifest["required_loaded_context_length"] = REQUIRED_CONTEXT
    manifest["required_request_timeout_seconds"] = REQUIRED_TIMEOUT
    manifest["execution_authorized"] = False
    manifest["model_run_authorized"] = False
    manifest["model_contact_performed"] = False
    manifest["selected_candidate"] = MODEL_REPOSITORY
    manifest["selected_runtime_model_id"] = RUNTIME_MODEL_ID
    manifest["runtime_identity_binding_review_path"] = str(BINDING_REVIEW_PATH.relative_to(ROOT))
    manifest["semantic_boundary_version"] = "semantic-boundary-v0.2"
    manifest["generic_system_composition_version"] = "semantic-system-composition-v0.1"
    manifest["qualified_completeness_pfs"] = ["PF2", "PF9", "PF12"]
    manifest["non_profile_cases_boundary_only"] = True
    manifest["authorization_path"] = str(AUTH_PATH.relative_to(ROOT))
    manifest["v13_authorization_reuse_forbidden"] = True
    return payload


def _configure() -> None:
    v13._configure()
    v13.AUTH_PATH = AUTH_PATH
    v13.RUN_TYPE = RUN_TYPE
    v13.RUNNER_VERSION = RUNNER_VERSION
    v13.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.AUTH_PATH = AUTH_PATH
    v13.v11.RUN_TYPE = RUN_TYPE
    v13.v11.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.v10.AUTH_PATH = AUTH_PATH
    v13.v11.v10.RUN_TYPE = RUN_TYPE
    v13.v11.v10.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.v10.v09.AUTH_PATH = AUTH_PATH
    v13.v11.v10.v09.RUN_TYPE = RUN_TYPE
    v13.v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.v10.v09.base.AUTH_PATH = AUTH_PATH
    v13.v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v13.v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.v10.v09._persist = _persist


def _install_bindings() -> None:
    _configure()
    v13.v11.validate_execution_authorization = validate_execution_authorization
    v13.v11.build_dry_run_manifest = build_dry_run_manifest
    v13.v11.v10.validate_execution_authorization = validate_execution_authorization
    v13.v11.v10.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    _install_bindings()
    return v13.v11.main()


if __name__ == "__main__":
    raise SystemExit(main())
