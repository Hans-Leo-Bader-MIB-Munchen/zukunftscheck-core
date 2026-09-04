#!/usr/bin/env python3
"""Model-free authorization candidate for one frozen synthetic Ministral run.

This module records no user approval, creates no executable authorization,
consumes no authorization and performs no model contact. It binds the frozen
pre-run package to a non-executable candidate in state
AWAITING_EXPLICIT_USER_APPROVAL.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREP_BASE_MAIN_COMMIT = "5dd6054ec30a531d9e53dfb1a1697bfd41c0edfc"
PREP_VERSION = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-AUTHORIZATION-CANDIDATE-PREP-2026-001_v0.1"
PREP_TYPE = "ZS-DEV-KI-B-SEM-MINISTRAL-QUALIFICATION-AUTHORIZATION-CANDIDATE-PREP-2026-001"
CANDIDATE_VERSION = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-AUTHORIZATION-CANDIDATE-2026-001_v0.1"
CANDIDATE_ID = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-SYNTHETIC-ONE-RUN-CANDIDATE-2026-001"
PRERUN_PATH = "scripts/zs_ki_b_sem_ministral_qualification_prerun_package_v0_1.py"
PRERUN_BLOB_SHA = "0a958fb7abba8d6421f1fb4c58b547a2afff8012"
V26_PATH = "scripts/zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep.py"
V26_BLOB_SHA = "f37da460593eec98c56a847188c13308a86c769d"
EXPECTED_RUNTIME_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
RESIDUAL_ARCHITECTURE_ISSUE = 130


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("ascii").strip()


def _blob_at(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _text_blob_sha1(path: Path) -> str:
    try:
        data = path.read_bytes().replace(b"\r\n", b"\n")
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError(f"cannot read authorization-candidate source: {path}") from exc
    if b"\r" in data:
        raise PermissionError(f"bare CR in authorization-candidate source: {path}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _validate_sources_before_import() -> None:
    for path, expected, label in (
        (PRERUN_PATH, PRERUN_BLOB_SHA, "pre-run"),
        (V26_PATH, V26_BLOB_SHA, "V26"),
    ):
        if _blob_at(PREP_BASE_MAIN_COMMIT, path) != expected:
            raise PermissionError(f"bound main {label} blob changed")
        if _text_blob_sha1(ROOT / path) != expected:
            raise PermissionError(f"worktree {label} blob changed")


_validate_sources_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_prerun_package_v0_1 as prerun
import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def candidate_sha256(candidate: dict[str, Any]) -> str:
    payload = deepcopy(candidate)
    payload.pop("authorization_candidate_sha256", None)
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def build_authorization_candidate() -> dict[str, Any]:
    _validate_sources_before_import()
    package = prerun.build_prerun_package()
    if package["status"] != "PREPARED_NOT_AUTHORIZED":
        raise PermissionError("pre-run package is not non-authorized")
    if package["runtime_model_id"] != EXPECTED_RUNTIME_MODEL_ID:
        raise PermissionError("pre-run runtime model changed")
    if package["model_repository"] != EXPECTED_MODEL_REPOSITORY:
        raise PermissionError("pre-run model repository changed")
    if package["expected_model_request_count"] != 16:
        raise PermissionError("pre-run request count changed")
    if package["max_tokens"] != 2048 or package["retry_count"] != 0:
        raise PermissionError("pre-run request bounds changed")
    if package["output_repair"] is not False:
        raise PermissionError("pre-run output repair changed")
    if package["authorization_gate"]["state"] != "CLOSED":
        raise PermissionError("pre-run authorization gate must remain closed")

    template = deepcopy(v26.v25.build_live_authorization_template())
    candidate = template
    candidate.update(
        {
            "authorization_candidate_version": CANDIDATE_VERSION,
            "authorization_candidate_id": CANDIDATE_ID,
            "authorization_prep_version": PREP_VERSION,
            "authorization_prep_type": PREP_TYPE,
            "authorization_prep_base_main_commit": PREP_BASE_MAIN_COMMIT,
            "status": "AWAITING_EXPLICIT_USER_APPROVAL",
            "authorization_consumed": False,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "approval_required": True,
            "explicit_user_single_run_approval_required": True,
            "single_use_only": True,
            "no_execution_from_candidate": True,
            "separate_approval_artifact_required": True,
            "approval_artifact_materialized": False,
            "approval_proof_present": False,
            "authorization_persisted": False,
            "automatic_retry_authorized": False,
            "automatic_rerun_authorized": False,
            "output_repair": False,
            "candidate_created_model_free": True,
            "candidate_hash_is_integrity_checksum_not_authentication": True,
            "model_contact_performed": False,
            "model_qualified": False,
            "benchmark_approved": False,
            "real_data": False,
            "pilot_approved": False,
            "production_approved": False,
            "live_runner_version": v26.CANDIDATE_ONLY_LIVE_RUNNER_VERSION,
            "live_run_type": v26.CANDIDATE_ONLY_LIVE_RUN_TYPE,
            "bound_v25_live_runner_version": v26.v25.RUNNER_VERSION,
            "bound_v25_live_run_type": v26.v25.RUN_TYPE,
            "runtime_model_id": package["runtime_model_id"],
            "model_repository": package["model_repository"],
            "bound_prerun_package": {
                "path": PRERUN_PATH,
                "git_blob_sha": PRERUN_BLOB_SHA,
                "package_version": package["prerun_package_version"],
                "package_sha256": package["prerun_package_sha256"],
                "run_type": package["run_type"],
                "bound_main_commit": package["bound_main_commit"],
                "qualification_snapshot_sha256": package["qualification_snapshot_sha256"],
                "ordered_case_ids_sha256": package["ordered_case_ids_sha256"],
            },
            "residual_architecture_issue": RESIDUAL_ARCHITECTURE_ISSUE,
        }
    )
    candidate["authorization_candidate_sha256"] = candidate_sha256(candidate)
    return candidate


def validate_authorization_candidate(candidate: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise PermissionError("authorization candidate must be an object")
    expected = build_authorization_candidate()
    if candidate != expected:
        raise PermissionError("authorization candidate does not match exact frozen binding")
    if candidate["authorization_candidate_sha256"] != candidate_sha256(candidate):
        raise PermissionError("authorization candidate hash mismatch")
    if candidate["status"] != "AWAITING_EXPLICIT_USER_APPROVAL":
        raise PermissionError("candidate must await explicit user approval")
    for key in ("execution_authorized", "model_run_authorized", "model_contact_authorized"):
        if candidate[key] is not False:
            raise PermissionError(f"candidate must not authorize {key}")
    if candidate["authorization_consumed"] is not False:
        raise PermissionError("candidate must not be consumed")
    if candidate["no_execution_from_candidate"] is not True:
        raise PermissionError("candidate must remain non-executable")
    if candidate["separate_approval_artifact_required"] is not True:
        raise PermissionError("candidate requires separate approval artifact")
    if candidate["approval_artifact_materialized"] is not False or candidate["approval_proof_present"] is not False:
        raise PermissionError("candidate must not contain materialized approval")
    if candidate["live_runner_version"] != v26.CANDIDATE_ONLY_LIVE_RUNNER_VERSION:
        raise PermissionError("candidate-only runner sentinel changed")
    if candidate["live_run_type"] != v26.CANDIDATE_ONLY_LIVE_RUN_TYPE:
        raise PermissionError("candidate-only run type sentinel changed")
    return candidate


def direct_status_escalation_rejected_by_v25(candidate: dict[str, Any]) -> bool:
    escalated = deepcopy(candidate)
    escalated.update(
        {
            "status": "EXPLICIT_USER_APPROVED",
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        }
    )
    try:
        v26.v25.validate_live_execution_authorization(escalated)
    except PermissionError:
        return True
    return False


def build_report() -> dict[str, Any]:
    candidate = build_authorization_candidate()
    validate_authorization_candidate(candidate)
    direct_escalation_rejected = direct_status_escalation_rejected_by_v25(candidate)
    if not direct_escalation_rejected:
        raise PermissionError("candidate can be silently escalated into V25 execution")
    return {
        "mode": "MODEL_FREE_MINISTRAL_QUALIFICATION_AUTHORIZATION_CANDIDATE_PREP",
        "status": "PASS",
        "governance_status": "AWAITING_EXPLICIT_USER_APPROVAL",
        "authorization_candidate_sha256": candidate["authorization_candidate_sha256"],
        "prerun_package_sha256": candidate["bound_prerun_package"]["package_sha256"],
        "runtime_model_id": candidate["runtime_model_id"],
        "expected_model_request_count": candidate["expected_model_request_count"],
        "direct_status_escalation_rejected_by_v25": True,
        "ready_for_explicit_user_approval": False,
        "approval_artifact_materialized": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "authorization_consumed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
