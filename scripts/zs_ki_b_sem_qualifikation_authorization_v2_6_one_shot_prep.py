#!/usr/bin/env python3
"""V26 model-free one-shot authorization candidate preparation.

This module does not approve, persist, consume or execute an authorization. It
builds and validates an AWAITING_EXPLICIT_USER_APPROVAL candidate bound to the
current committed V25 runner and its exact qualification bindings.

The candidate is deliberately made incompatible with the V25 execution gate by
using candidate-only live runner identity sentinels while separately preserving
the exact bound V25 runner identity. A later approval step must therefore create
a distinct authorization artifact; changing only status/authorization flags on
this candidate cannot make it executable by V25.
"""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25

PREP_VERSION = "v2.6-one-shot-authorization-prep"
PREP_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-6-ONE-SHOT-AUTHORIZATION-PREP-2026-027"
BASE_MAIN_COMMIT = "a1d5e2d819fd5ce7b55e22adece5732fbba0dacc"
EXPECTED_V25_RUNNER_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"
EXPECTED_V25_RUNNER_BLOB = "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866"
AUTHORIZATION_CANDIDATE_VERSION = "ZS-KI-B-SEM-ONE-SHOT-AUTHORIZATION-CANDIDATE-2026-001_v0.1"
AUTHORIZATION_CANDIDATE_ID = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-ONE-SHOT-CANDIDATE-2026-001"
CANDIDATE_ONLY_LIVE_RUNNER_VERSION = f"{v25.RUNNER_VERSION}::CANDIDATE_ONLY_NON_EXECUTABLE"
CANDIDATE_ONLY_LIVE_RUN_TYPE = f"{v25.RUN_TYPE}::CANDIDATE_ONLY_NON_EXECUTABLE"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _candidate_hash_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(candidate)
    payload.pop("authorization_candidate_sha256", None)
    return payload


def candidate_sha256(candidate: dict[str, Any]) -> str:
    """Integrity checksum only; this is not a user signature or authentication proof."""
    return hashlib.sha256(_canonical_bytes(_candidate_hash_payload(candidate))).hexdigest()


def _current_v25_runner_blob() -> str:
    return v25.v24.v23._git("rev-parse", f"HEAD:{EXPECTED_V25_RUNNER_PATH}")


def _current_git_commit() -> str:
    return v25.v24.v23._git("rev-parse", "HEAD")


def build_authorization_candidate() -> dict[str, Any]:
    """Build a non-executable authorization candidate bound to current HEAD.

    The candidate must be regenerated after any commit change. It intentionally
    remains non-authorizing until a later explicit user-approval step. Its
    candidate-only live runner identity makes direct use at the V25 execution
    gate fail closed even if status and authorization flags are edited.
    """
    template = deepcopy(v25.build_live_authorization_template())
    bound_v25_live_runner_version = template["live_runner_version"]
    bound_v25_live_run_type = template["live_run_type"]
    candidate = template
    candidate.update(
        {
            "authorization_candidate_version": AUTHORIZATION_CANDIDATE_VERSION,
            "authorization_candidate_id": AUTHORIZATION_CANDIDATE_ID,
            "authorization_prep_version": PREP_VERSION,
            "authorization_prep_type": PREP_TYPE,
            "authorization_prep_base_main_commit": BASE_MAIN_COMMIT,
            "status": "AWAITING_EXPLICIT_USER_APPROVAL",
            "authorization_consumed": False,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "approval_required": True,
            "single_use_only": True,
            "no_execution_from_candidate": True,
            "automatic_retry_authorized": False,
            "automatic_rerun_authorized": False,
            "output_repair": False,
            "model_qualified": False,
            "candidate_created_model_free": True,
            "candidate_hash_is_integrity_checksum_not_authentication": True,
            "separate_approval_artifact_required": True,
            "live_runner_version": CANDIDATE_ONLY_LIVE_RUNNER_VERSION,
            "live_run_type": CANDIDATE_ONLY_LIVE_RUN_TYPE,
            "bound_v25_live_runner_version": bound_v25_live_runner_version,
            "bound_v25_live_run_type": bound_v25_live_run_type,
            "bound_main_commit": _current_git_commit(),
            "bound_v25_runner_path": EXPECTED_V25_RUNNER_PATH,
            "bound_v25_runner_blob_oid": _current_v25_runner_blob(),
        }
    )
    candidate["authorization_candidate_sha256"] = candidate_sha256(candidate)
    return candidate


def validate_authorization_candidate(candidate: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise PermissionError("V26 authorization candidate must be an object")
    expected = build_authorization_candidate()
    if candidate != expected:
        raise PermissionError("V26 authorization candidate does not match exact current binding")
    if candidate.get("authorization_candidate_sha256") != candidate_sha256(candidate):
        raise PermissionError("V26 authorization candidate hash mismatch")
    if candidate.get("status") != "AWAITING_EXPLICIT_USER_APPROVAL":
        raise PermissionError("V26 candidate status is not awaiting explicit user approval")
    if any(
        candidate.get(key) is not False
        for key in ("execution_authorized", "model_run_authorized", "model_contact_authorized")
    ):
        raise PermissionError("V26 candidate must not authorize execution or model contact")
    if candidate.get("authorization_consumed") is not False:
        raise PermissionError("V26 candidate must not be consumed")
    if candidate.get("no_execution_from_candidate") is not True:
        raise PermissionError("V26 candidate must remain non-executable")
    if candidate.get("separate_approval_artifact_required") is not True:
        raise PermissionError("V26 candidate requires a separate later approval artifact")
    if candidate.get("live_runner_version") != CANDIDATE_ONLY_LIVE_RUNNER_VERSION:
        raise PermissionError("V26 candidate must retain candidate-only runner identity")
    if candidate.get("live_run_type") != CANDIDATE_ONLY_LIVE_RUN_TYPE:
        raise PermissionError("V26 candidate must retain candidate-only run type")
    if candidate.get("bound_v25_live_runner_version") != v25.RUNNER_VERSION:
        raise PermissionError("V26 bound V25 runner version mismatch")
    if candidate.get("bound_v25_live_run_type") != v25.RUN_TYPE:
        raise PermissionError("V26 bound V25 run type mismatch")
    return candidate


def _status_escalated_candidate_rejected_by_v25(candidate: dict[str, Any]) -> bool:
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
        v25.validate_live_execution_authorization(escalated)
    except PermissionError:
        return True
    return False


def build_prep_report() -> dict[str, Any]:
    candidate = build_authorization_candidate()
    try:
        validate_authorization_candidate(candidate)
        candidate_valid = True
    except PermissionError:
        candidate_valid = False

    direct_gate_rejection = _status_escalated_candidate_rejected_by_v25(candidate)
    checks = {
        "candidate_exact_current_binding": candidate_valid,
        "v25_runner_path_exact": candidate["bound_v25_runner_path"] == EXPECTED_V25_RUNNER_PATH,
        "v25_runner_blob_exact": candidate["bound_v25_runner_blob_oid"] == EXPECTED_V25_RUNNER_BLOB,
        "v25_runner_version_bound_exact": candidate["bound_v25_live_runner_version"] == v25.RUNNER_VERSION,
        "v25_run_type_bound_exact": candidate["bound_v25_live_run_type"] == v25.RUN_TYPE,
        "candidate_live_runner_identity_non_executable": candidate["live_runner_version"] == CANDIDATE_ONLY_LIVE_RUNNER_VERSION,
        "candidate_live_run_type_non_executable": candidate["live_run_type"] == CANDIDATE_ONLY_LIVE_RUN_TYPE,
        "status_escalation_rejected_by_actual_v25_gate": direct_gate_rejection,
        "max_tokens_2048_exact": candidate["max_tokens"] == 2048 == v25.MAX_TOKENS,
        "expected_request_count_16": candidate["expected_model_request_count"] == 16,
        "status_awaiting_explicit_user_approval": candidate["status"] == "AWAITING_EXPLICIT_USER_APPROVAL",
        "execution_not_authorized": candidate["execution_authorized"] is False,
        "model_run_not_authorized": candidate["model_run_authorized"] is False,
        "model_contact_not_authorized": candidate["model_contact_authorized"] is False,
        "authorization_not_consumed": candidate["authorization_consumed"] is False,
        "single_use_only": candidate["single_use_only"] is True,
        "no_execution_from_candidate": candidate["no_execution_from_candidate"] is True,
        "separate_approval_artifact_required": candidate["separate_approval_artifact_required"] is True,
        "hash_explicitly_not_authentication": candidate["candidate_hash_is_integrity_checksum_not_authentication"] is True,
        "retry_forbidden": candidate["automatic_retry_authorized"] is False and v25.RETRY_COUNT == 0,
        "automatic_rerun_forbidden": candidate["automatic_rerun_authorized"] is False,
        "output_repair_false": candidate["output_repair"] is False,
        "model_not_qualified": candidate["model_qualified"] is False,
        "candidate_hash_exact": candidate["authorization_candidate_sha256"] == candidate_sha256(candidate),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_ONE_SHOT_AUTHORIZATION_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "governance_status": "AWAITING_EXPLICIT_USER_APPROVAL" if passed else "FAIL_CLOSED",
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "authorization_candidate": candidate,
        "ready_for_explicit_user_approval": False,
        "separate_approval_artifact_required": True,
        "approval_ceremony_implemented": False,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "authorization_artifact_persisted": False,
        "authorization_consumed": False,
        "model_qualified": False,
    }


def main() -> int:
    report = build_prep_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
