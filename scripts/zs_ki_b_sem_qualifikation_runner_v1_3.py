#!/usr/bin/env python3
"""Qualification runner v1.3: prompt v0.6 plus qualified generic system composition.

This model-free alignment layer preserves the frozen 16-case suite, Human Gold,
policy, Meaning Layer, semantic contract and prompt v0.6. It replaces the legacy
v1.2 PF2-specific runtime-guard binding with:
- Semantic Boundary v0.2 for every case;
- Generic System Composition v0.1 with ACTIVE completeness triggers only for
  PF2, PF9 and PF12, using the qualified declarative profile set;
- no completeness trigger for PF1/PF3-PF8/PF10/PF11 or challenge cases.

Execution is fail-closed and remains blocked until a separately versioned v1.3
model-run authorization artifact is explicitly approved. This file itself does
not contact a model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_1 as v11
from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2
from core.validation.semantic_system_composition_v0_1 import (
    NO_COMPLETENESS_STOP,
    evaluate_semantic_system_composition,
)

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-3-GENERIC-COMPOSITION-2026-013"
RUNNER_VERSION = "v1.3"
PROMPT_VERSION = v11.PROMPT_VERSION
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v13_model_run_authorization_v0_1.json"
PROFILE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_generic_system_composition_profiles_v0_1.json"
PREVIOUS_FAILURE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v12_model_run_authorization_v0_2.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_3.json"
QUALIFIED_COMPLETENESS_PFS = {"PF2", "PF9", "PF12"}

_ORIGINAL_BUILD_DRY_RUN = v11.build_dry_run_manifest


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pf_id(case: dict[str, Any]) -> str | None:
    case_id = case.get("case_id")
    if not isinstance(case_id, str):
        return None
    for pf in QUALIFIED_COMPLETENESS_PFS:
        if f"-Q-{pf}-" in case_id:
            return pf
    return None


def _allowed_ids(case: dict[str, Any]) -> set[str]:
    source_locations = case.get("source_locations")
    if not isinstance(source_locations, list):
        return set()
    return {
        row.get("source_location_id")
        for row in source_locations
        if isinstance(row, dict) and isinstance(row.get("source_location_id"), str)
    }


def _boundary_only(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    issues = validate_semantic_response_v0_2(
        response,
        allowed_source_location_ids=_allowed_ids(case),
        target_source_location_id=case.get("target_source_location_id"),
    )
    rows = [issue.to_dict() if hasattr(issue, "to_dict") else dict(getattr(issue, "__dict__", {})) for issue in issues]
    return {
        "passed": not bool(rows),
        "formal_boundary_passed": not bool(rows),
        "runtime_guard_version": "semantic-boundary-v0.2",
        "composition_version": None,
        "completeness_profile_applied": False,
        "issues": rows,
        "automatic_downstream_use_allowed": False,
        "human_review_required": bool(rows),
        "model_output_mutated": False,
        "decision_authority": "NONE",
        "global_downstream_authority": "NONE",
    }


def evaluate_runtime_guard(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    pf_id = _pf_id(case)
    if pf_id is None:
        return _boundary_only(case, response)

    result = evaluate_semantic_system_composition(
        model_response=response,
        allowed_source_location_ids=_allowed_ids(case),
        target_source_location_id=case.get("target_source_location_id"),
        pf_id=pf_id,
        trigger_state="ACTIVE",
        profile_set=load(PROFILE_PATH),
    )
    return {
        "passed": result.get("behavior") == NO_COMPLETENESS_STOP,
        "formal_boundary_passed": bool(result.get("boundary_passed")),
        "runtime_guard_version": "semantic-system-composition-v0.1",
        "composition_version": result.get("composition_version"),
        "completeness_profile_applied": True,
        "pf_id": pf_id,
        "behavior": result.get("behavior"),
        "stop_class": result.get("stop_class"),
        "stop_code": result.get("stop_code"),
        "issues": result.get("boundary_issues") or [],
        "completeness_result": result.get("completeness_result"),
        "automatic_downstream_use_allowed": False,
        "human_review_required": bool(result.get("human_review_required")),
        "model_output_mutated": bool(result.get("model_output_mutated")),
        "decision_authority": result.get("decision_authority"),
        "global_downstream_authority": result.get("global_downstream_authority"),
    }


def _configure() -> None:
    v11.RUN_TYPE = RUN_TYPE
    v11.RUNNER_VERSION = RUNNER_VERSION
    v11.AUTH_PATH = AUTH_PATH
    v11.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH
    v11.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.RUN_TYPE = RUN_TYPE
    v11.v10.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.AUTH_PATH = AUTH_PATH
    v11.v10.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH
    v11.v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.RUN_TYPE = RUN_TYPE
    v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.AUTH_PATH = AUTH_PATH
    v11.v10.v09.PREVIOUS_FAILURE_PATH = PREVIOUS_FAILURE_PATH
    v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.base.AUTH_PATH = AUTH_PATH
    v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.base.evaluate_boundary = evaluate_runtime_guard


def _authorization_status() -> bool:
    try:
        auth = load(AUTH_PATH)
    except (OSError, ValueError):
        return False
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED"
        and auth.get("run_type") == RUN_TYPE
        and auth.get("runner_version") == RUNNER_VERSION
        and auth.get("model") == "qwen3-14b"
        and auth.get("generic_system_composition_required") is True
        and auth.get("generic_system_composition_version") == "semantic-system-composition-v0.1"
    )


def validate_execution_authorization(model: str) -> dict[str, Any]:
    _configure()
    auth = load(AUTH_PATH)
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("v1.3 model run is not explicitly authorized")
    if auth.get("run_type") != RUN_TYPE or auth.get("runner_version") != RUNNER_VERSION:
        raise PermissionError("v1.3 authorization does not match runner identity")
    if auth.get("model") != model:
        raise PermissionError("v1.3 authorization model mismatch")
    if auth.get("prompt_version") != PROMPT_VERSION:
        raise PermissionError("v1.3 authorization prompt version mismatch")
    if auth.get("generic_system_composition_required") is not True:
        raise PermissionError("v1.3 authorization must require generic system composition")
    if auth.get("generic_system_composition_version") != "semantic-system-composition-v0.1":
        raise PermissionError("v1.3 authorization composition version mismatch")
    if auth.get("qualified_completeness_pfs") != ["PF2", "PF9", "PF12"]:
        raise PermissionError("v1.3 authorization completeness PF scope mismatch")
    if auth.get("synthetic_only") is not True or auth.get("local_loopback_only") is not True:
        raise PermissionError("v1.3 authorization must remain synthetic-only and loopback-only")
    if auth.get("single_run_only") is not True or auth.get("retry_count") != 0 or auth.get("output_repair") is not False:
        raise PermissionError("v1.3 authorization violates one-shot constraints")
    if auth.get("remote_cloud") is not False or auth.get("real_data") is not False:
        raise PermissionError("v1.3 authorization must prohibit cloud and real-data execution")
    return auth


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _configure()
    payload = _ORIGINAL_BUILD_DRY_RUN(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_3"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["prompt_version"] = PROMPT_VERSION
    manifest["execution_authorized"] = _authorization_status()
    manifest["model_run_authorized"] = _authorization_status()
    manifest["semantic_boundary_version"] = "semantic-boundary-v0.2"
    manifest["generic_system_composition_version"] = "semantic-system-composition-v0.1"
    manifest["qualified_completeness_pfs"] = ["PF2", "PF9", "PF12"]
    manifest["non_profile_cases_boundary_only"] = True
    manifest["prompt_change_only"] = False
    manifest["model_contact_performed"] = False
    return payload


def _install_bindings() -> None:
    _configure()
    v11.validate_execution_authorization = validate_execution_authorization
    v11.build_dry_run_manifest = build_dry_run_manifest
    v11.v10.validate_execution_authorization = validate_execution_authorization
    v11.v10.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    _install_bindings()
    return v11.main()


if __name__ == "__main__":
    raise SystemExit(main())
