#!/usr/bin/env python3
"""Model-free approval/execution plan for one frozen synthetic Ministral run.

This module records no user approval, generates no approval secret, persists no
challenge/proof/claim, creates no live run authorization, consumes no
authorization and performs no model contact. It freezes the exact transition
sequence that a later explicitly approved single run must follow.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_MAIN_COMMIT = "06e286caaf396e17dc1b8ec44378883f4a17ffb1"
PLAN_VERSION = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-APPROVAL-EXECUTION-PLAN-2026-001_v0.2"
PLAN_TYPE = "ZS-DEV-KI-B-SEM-MINISTRAL-QUALIFICATION-APPROVAL-EXECUTION-PREP-2026-001"
CANDIDATE_PATH = "scripts/zs_ki_b_sem_ministral_qualification_authorization_candidate_v0_1.py"
CANDIDATE_BLOB_SHA = "edaad6ff363010af5da5103f314df9f336f9c045"
EXPECTED_RUNTIME_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
RESIDUAL_ARCHITECTURE_ISSUE = 130

SOURCE_PATHS: tuple[tuple[str, str], ...] = (
    ("v25_live_runner", "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"),
    ("v27_approval_ceremony", "scripts/zs_ki_b_sem_approval_ceremony_v2_7_architecture_prep.py"),
    ("v28_execution_gate", "scripts/zs_ki_b_sem_execution_gate_v2_8_integration_prep.py"),
    ("v29_run_authorization_transform", "scripts/zs_ki_b_sem_run_authorization_v2_9_transform_prep.py"),
    ("v30_proof_enforcing_live_gate", "scripts/zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep.py"),
    ("v31_authority_state_atomic_consume", "scripts/zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep.py"),
    ("v32_external_state_atomic_consume", "scripts/zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep.py"),
    ("v33_canonical_store_toctou", "scripts/zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep.py"),
    ("v42_authority_root_attestation", "scripts/zs_ki_b_sem_external_trust_anchor_provenance_authority_attestation_v4_2_prep.py"),
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("ascii").strip()


def _blob_at(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _text_blob_sha1(path: Path) -> str:
    try:
        data = path.read_bytes().replace(b"\r\n", b"\n")
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError(f"cannot read approval/execution source: {path}") from exc
    if b"\r" in data:
        raise PermissionError(f"bare CR in approval/execution source: {path}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _stable_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_all_sources_before_import() -> None:
    if _blob_at(BASE_MAIN_COMMIT, CANDIDATE_PATH) != CANDIDATE_BLOB_SHA:
        raise PermissionError("bound main candidate blob changed")
    if _text_blob_sha1(ROOT / CANDIDATE_PATH) != CANDIDATE_BLOB_SHA:
        raise PermissionError("worktree candidate blob changed")
    for role, path in SOURCE_PATHS:
        oid = _blob_at(BASE_MAIN_COMMIT, path)
        if not oid or len(oid) != 40:
            raise PermissionError(f"invalid Git blob for {role}")
        if _text_blob_sha1(ROOT / path) != oid:
            raise PermissionError(f"approval/execution source worktree mismatch before import: {role}")


_validate_all_sources_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_authorization_candidate_v0_1 as candidate_prep
import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29


def _source_bindings() -> list[dict[str, str]]:
    bindings: list[dict[str, str]] = []
    for role, path in SOURCE_PATHS:
        oid = _blob_at(BASE_MAIN_COMMIT, path)
        if not oid or len(oid) != 40:
            raise PermissionError(f"invalid Git blob for {role}")
        if _text_blob_sha1(ROOT / path) != oid:
            raise PermissionError(f"approval/execution source worktree mismatch: {role}")
        bindings.append({"role": role, "path": path, "git_blob_sha": oid})
    return bindings


def build_approval_execution_plan() -> dict[str, Any]:
    _validate_all_sources_before_import()
    candidate = candidate_prep.build_authorization_candidate()
    candidate_prep.validate_authorization_candidate(candidate)

    if candidate["status"] != "AWAITING_EXPLICIT_USER_APPROVAL":
        raise PermissionError("candidate is not awaiting explicit approval")
    if candidate["runtime_model_id"] != EXPECTED_RUNTIME_MODEL_ID:
        raise PermissionError("runtime model changed")
    if candidate["model_repository"] != EXPECTED_MODEL_REPOSITORY:
        raise PermissionError("model repository changed")
    if candidate["expected_model_request_count"] != 16:
        raise PermissionError("request count changed")
    if candidate["max_tokens"] != 2048:
        raise PermissionError("max_tokens changed")
    if candidate["automatic_retry_authorized"] is not False:
        raise PermissionError("retry unexpectedly authorized")
    if candidate["automatic_rerun_authorized"] is not False:
        raise PermissionError("rerun unexpectedly authorized")
    if candidate["output_repair"] is not False:
        raise PermissionError("output repair unexpectedly enabled")
    if not candidate_prep.direct_status_escalation_rejected_by_v25(candidate):
        raise PermissionError("candidate can be silently escalated")

    plan = {
        "plan_version": PLAN_VERSION,
        "plan_type": PLAN_TYPE,
        "status": "PREPARED_NOT_AUTHORIZED",
        "bound_main_commit": BASE_MAIN_COMMIT,
        "runtime_model_id": EXPECTED_RUNTIME_MODEL_ID,
        "model_repository": EXPECTED_MODEL_REPOSITORY,
        "data_class": "SYNTHETIC_ONLY",
        "expected_model_request_count": 16,
        "max_tokens": 2048,
        "retry_count": 0,
        "output_repair": False,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "bound_candidate": {
            "path": CANDIDATE_PATH,
            "git_blob_sha": CANDIDATE_BLOB_SHA,
            "candidate_version": candidate["authorization_candidate_version"],
            "candidate_id": candidate["authorization_candidate_id"],
            "candidate_sha256": candidate["authorization_candidate_sha256"],
            "prerun_package_sha256": candidate["bound_prerun_package"]["package_sha256"],
            "qualification_snapshot_sha256": candidate["bound_prerun_package"]["qualification_snapshot_sha256"],
            "ordered_case_ids_sha256": candidate["bound_prerun_package"]["ordered_case_ids_sha256"],
        },
        "source_bindings": _source_bindings(),
        "all_direct_import_sources_verified_before_import": True,
        "required_sequence": [
            "EXPLICIT_USER_SINGLE_RUN_APPROVAL",
            "GENERATE_EXTERNAL_APPROVAL_SECRET",
            "BUILD_AND_PERSIST_EXACT_GATE_CHALLENGE_ONCE",
            "MATERIALIZE_AND_VALIDATE_EXACT_APPROVAL_PROOF",
            "ATOMIC_SINGLE_USE_GATE_CLAIM",
            "RUN_AUTHORIZATION_TRANSFORM_AND_PROOF_ENFORCING_GATE",
            "ATOMIC_AUTHORIZATION_CONSUMPTION_BEFORE_FIRST_POSSIBLE_MODEL_CONTACT",
            "EXACTLY_16_MODEL_REQUESTS_OR_FAIL_CLOSED",
            "NO_RETRY_NO_REPAIR_NO_AUTOMATIC_RERUN",
            "HUMAN_GOLD_REVIEW_BEFORE_QUALIFICATION_DECISION",
        ],
        "approval_ceremony_state": "NOT_STARTED",
        "explicit_user_approval_recorded": False,
        "approval_secret_generated": False,
        "challenge_persisted": False,
        "approval_proof_materialized": False,
        "gate_claim_persisted": False,
        "run_authorization_materialized": False,
        "authorization_persisted": False,
        "authorization_consumed": False,
        "authorization_must_be_consumed_before_first_possible_model_contact": True,
        "single_use_only": True,
        "ready_for_model_contact": False,
        "no_execution_from_plan": True,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
        "benchmark_approved": False,
        "real_data": False,
        "pilot_approved": False,
        "production_approved": False,
        "residual_architecture_issue": RESIDUAL_ARCHITECTURE_ISSUE,
        "v28_atomic_claim_primitive_available": callable(v28.claim_gate_once_preview),
        "v29_transform_preview_available": callable(v29.build_run_authorization_preview),
    }
    if not plan["v28_atomic_claim_primitive_available"] or not plan["v29_transform_preview_available"]:
        raise PermissionError("required approval/execution primitives unavailable")
    plan["approval_execution_plan_sha256"] = _stable_sha256(plan)
    return plan


def validate_approval_execution_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise PermissionError("approval/execution plan must be an object")
    expected = build_approval_execution_plan()
    if plan != expected:
        raise PermissionError("approval/execution plan mismatch")
    return plan


def build_report() -> dict[str, Any]:
    plan = build_approval_execution_plan()
    return {
        "mode": "MODEL_FREE_MINISTRAL_QUALIFICATION_APPROVAL_EXECUTION_PREP",
        "status": "PASS",
        "governance_status": "PREPARED_NOT_AUTHORIZED",
        "approval_execution_plan_sha256": plan["approval_execution_plan_sha256"],
        "authorization_candidate_sha256": plan["bound_candidate"]["candidate_sha256"],
        "runtime_model_id": plan["runtime_model_id"],
        "expected_model_request_count": plan["expected_model_request_count"],
        "all_direct_import_sources_verified_before_import": plan["all_direct_import_sources_verified_before_import"],
        "explicit_user_approval_recorded": False,
        "approval_secret_generated": False,
        "challenge_persisted": False,
        "approval_proof_materialized": False,
        "gate_claim_persisted": False,
        "authorization_consumed": False,
        "ready_for_model_contact": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
