#!/usr/bin/env python3
"""V26 model-free one-shot authorization candidate preparation.

This module does not approve, persist, consume or execute an authorization. It
builds and validates an AWAITING_EXPLICIT_USER_APPROVAL candidate bound to the
current committed V25 runner and its exact qualification bindings.
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


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _candidate_hash_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(candidate)
    payload.pop("authorization_candidate_sha256", None)
    return payload


def candidate_sha256(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(_candidate_hash_payload(candidate))).hexdigest()


def _current_v25_runner_blob() -> str:
    return v25.v24.v23._git("rev-parse", f"HEAD:{EXPECTED_V25_RUNNER_PATH}")


def _current_git_commit() -> str:
    return v25.v24.v23._git("rev-parse", "HEAD")


def build_authorization_candidate() -> dict[str, Any]:
    """Build a non-executable authorization candidate bound to current HEAD.

    The candidate must be regenerated after any commit change. It intentionally
    remains non-authorizing until a later explicit user-approval step.
    """
    template = deepcopy(v25.build_live_authorization_template())
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
    return candidate


def build_prep_report() -> dict[str, Any]:
    candidate = build_authorization_candidate()
    try:
        validate_authorization_candidate(candidate)
        candidate_valid = True
    except PermissionError:
        candidate_valid = False

    checks = {
        "candidate_exact_current_binding": candidate_valid,
        "v25_runner_path_exact": candidate["bound_v25_runner_path"] == EXPECTED_V25_RUNNER_PATH,
        "v25_runner_blob_exact": candidate["bound_v25_runner_blob_oid"] == EXPECTED_V25_RUNNER_BLOB,
        "max_tokens_2048_exact": candidate["max_tokens"] == 2048 == v25.MAX_TOKENS,
        "expected_request_count_16": candidate["expected_model_request_count"] == 16,
        "status_awaiting_explicit_user_approval": candidate["status"] == "AWAITING_EXPLICIT_USER_APPROVAL",
        "execution_not_authorized": candidate["execution_authorized"] is False,
        "model_run_not_authorized": candidate["model_run_authorized"] is False,
        "model_contact_not_authorized": candidate["model_contact_authorized"] is False,
        "authorization_not_consumed": candidate["authorization_consumed"] is False,
        "single_use_only": candidate["single_use_only"] is True,
        "no_execution_from_candidate": candidate["no_execution_from_candidate"] is True,
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
        "ready_for_explicit_user_approval": passed,
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
