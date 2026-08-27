#!/usr/bin/env python3
"""Qualification runner v1.2: prompt v0.6 plus deterministic runtime guard.

This runner reuses v1.1 execution controls and installs a versioned post-parse
runtime-guard hook into the inherited qualification loop. The guard executes
formal semantic boundary validation first and, only after a formal PASS, the
narrow PF2 semantic-completeness audit. A completeness hit is fail-closed for
automatic downstream use and therefore stops qualification before Human-Gold.

Execution remains fail-closed and is permitted only when the separately versioned
v1.2 authorization artifact is EXPLICIT_USER_APPROVED for the exact model and run.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_1 as v11
from core.validation.semantic_runtime_guard_v0_1 import evaluate_semantic_runtime_guard

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-2-RUNTIME-GUARD-2026-012"
RUNNER_VERSION = "v1.2"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v12_model_run_authorization_v0_2.json"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_2.json"

_ORIGINAL_VALIDATE_AUTH = v11.validate_execution_authorization
_ORIGINAL_BUILD_DRY_RUN = v11.build_dry_run_manifest


def _target_source_text(case: dict[str, Any]) -> str:
    target = case.get("target_source_location_id")
    source_locations = case.get("source_locations")
    if not isinstance(source_locations, list):
        return ""
    for row in source_locations:
        if isinstance(row, dict) and row.get("source_location_id") == target:
            text = row.get("original_text")
            return text if isinstance(text, str) else ""
    return ""


def evaluate_runtime_guard(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Adapter matching the inherited evaluate_boundary(case, response) hook."""
    source_locations = case.get("source_locations") or []
    allowed_ids = {
        row.get("source_location_id")
        for row in source_locations
        if isinstance(row, dict) and isinstance(row.get("source_location_id"), str)
    }
    target = case.get("target_source_location_id")
    if not isinstance(target, str) or not target:
        return {
            "passed": False,
            "formal_boundary_passed": False,
            "runtime_guard_version": "semantic-runtime-guard-v0.1",
            "issues": [{"code": "MISSING_TARGET_SOURCE_LOCATION_ID"}],
            "completeness_audit": None,
            "automatic_downstream_use_allowed": False,
            "human_review_required": False,
            "decision_authority": "NONE",
        }

    guard = evaluate_semantic_runtime_guard(
        source_text=_target_source_text(case),
        model_response=response,
        allowed_source_location_ids=allowed_ids,
        target_source_location_id=target,
    )
    completeness = guard.get("completeness_audit")
    completeness_stop = bool(
        completeness and completeness.get("stop_automatic_downstream_use") is True
    )
    issues = list(guard.get("boundary_issues") or [])
    if completeness_stop:
        issues.append({
            "code": "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED",
            "rule_id": "B-SCA001",
            "message": "deterministic completeness audit requires human review before downstream use",
        })

    return {
        "passed": bool(guard.get("boundary_passed")) and not completeness_stop,
        "formal_boundary_passed": bool(guard.get("boundary_passed")),
        "runtime_guard_version": guard.get("runtime_guard_version"),
        "issues": issues,
        "completeness_audit": completeness,
        "automatic_downstream_use_allowed": bool(guard.get("automatic_downstream_use_allowed")),
        "human_review_required": bool(guard.get("human_review_required")),
        "model_output_mutated": bool(guard.get("model_output_mutated")),
        "decision_authority": guard.get("decision_authority"),
    }


def _configure() -> None:
    v11.RUN_TYPE = RUN_TYPE
    v11.RUNNER_VERSION = RUNNER_VERSION
    v11.AUTH_PATH = AUTH_PATH
    v11.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.RUN_TYPE = RUN_TYPE
    v11.v10.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.AUTH_PATH = AUTH_PATH
    v11.v10.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.RUN_TYPE = RUN_TYPE
    v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.AUTH_PATH = AUTH_PATH
    v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v11.v10.v09.base.AUTH_PATH = AUTH_PATH
    v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v11.v10.v09.base.evaluate_boundary = evaluate_runtime_guard


def _authorization_status() -> bool:
    try:
        auth = v11.v10.v09.base.load(AUTH_PATH)
    except (OSError, ValueError):
        return False
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED"
        and auth.get("run_type") == RUN_TYPE
        and auth.get("runner_version") == RUNNER_VERSION
        and auth.get("runtime_guard_required") is True
        and auth.get("runtime_guard_version") == "semantic-runtime-guard-v0.1"
    )


def validate_execution_authorization(model: str) -> dict[str, Any]:
    _configure()
    auth = v11.v10.v09.base.load(AUTH_PATH)
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("v1.2 model run is not explicitly authorized")
    if auth.get("run_type") != RUN_TYPE or auth.get("runner_version") != RUNNER_VERSION:
        raise PermissionError("v1.2 authorization does not match runner identity")
    if auth.get("model") != model:
        raise PermissionError("v1.2 authorization model mismatch")
    if auth.get("runtime_guard_required") is not True:
        raise PermissionError("v1.2 authorization requires the semantic runtime guard")
    if auth.get("runtime_guard_version") != "semantic-runtime-guard-v0.1":
        raise PermissionError("v1.2 authorization runtime guard version mismatch")
    return _ORIGINAL_VALIDATE_AUTH(model)


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _configure()
    payload = _ORIGINAL_BUILD_DRY_RUN(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_2"
    manifest = payload["manifest"]
    authorized = _authorization_status()
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["runtime_guard_version"] = "semantic-runtime-guard-v0.1"
    manifest["runtime_guard_bound"] = True
    manifest["execution_authorized"] = authorized
    manifest["model_run_authorized"] = authorized
    manifest["prompt_change_only"] = False
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
