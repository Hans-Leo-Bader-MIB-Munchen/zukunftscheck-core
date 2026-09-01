#!/usr/bin/env python3
"""V31 model-free authority-state and atomic-consume preparation.

V31 defines the contract that a later real run-authorization ceremony must
satisfy. It does not create or verify an authoritative trust anchor, does not
record explicit user approval, does not materialize or consume a live
authorization, and does not contact a model.
"""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30

PREP_VERSION = "v3.1-authority-state-atomic-consume-prep"
PREP_TYPE = "ZS-KI-B-SEM-AUTHORITY-STATE-ATOMIC-CONSUME-PREP-2026-032"
BASE_MAIN_COMMIT = "3935a5bd514e9fe159bc217214a90a61c5eebcf0"
CONTRACT_VERSION = "ZS-KI-B-SEM-AUTHORITY-STATE-CONTRACT-2026-001_v0.1"
APPROVAL_REQUEST_VERSION = "ZS-KI-B-SEM-EXPLICIT-RUN-APPROVAL-REQUEST-2026-001_v0.1"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_git_oid(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_absolute_path_text(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _looks_repo_local(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    root_name = ROOT.name.lower()
    return f"/{root_name}/" in normalized or normalized.endswith(f"/{root_name}")


def build_authority_state_contract_preview(
    *,
    authority_state_path: str,
    trust_anchor_id: str,
    trust_anchor_fingerprint_sha256: str,
    durable_claim_record_id: str,
    consume_record_id: str,
    final_main_commit: str,
    final_runner_blob_oid: str,
) -> dict[str, Any]:
    """Build a non-authoritative contract preview for later external state."""
    if not isinstance(authority_state_path, str) or not authority_state_path.strip():
        raise PermissionError("V31 authority-state path is required")
    if not _is_absolute_path_text(authority_state_path):
        raise PermissionError("V31 authority-state path must be absolute and external")
    if _looks_repo_local(authority_state_path):
        raise PermissionError("V31 authority-state path must not point into the repository")
    for label, value in (
        ("trust_anchor_id", trust_anchor_id),
        ("durable_claim_record_id", durable_claim_record_id),
        ("consume_record_id", consume_record_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise PermissionError(f"V31 {label} is required")
    if not _is_sha256(trust_anchor_fingerprint_sha256):
        raise PermissionError("V31 trust-anchor fingerprint must be SHA-256")
    if not _is_git_oid(final_main_commit) or not _is_git_oid(final_runner_blob_oid):
        raise PermissionError("V31 final git bindings must be 40-hex object ids")

    contract = {
        "contract_version": CONTRACT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "authority_state_path": authority_state_path,
        "trust_anchor_id": trust_anchor_id,
        "trust_anchor_fingerprint_sha256": trust_anchor_fingerprint_sha256.lower(),
        "durable_claim_record_id": durable_claim_record_id,
        "consume_record_id": consume_record_id,
        "final_main_commit": final_main_commit.lower(),
        "final_runner_blob_oid": final_runner_blob_oid.lower(),
        "required_storage_semantics": "APPEND_ONLY_DELETE_DENIED_ROTATION_DENIED",
        "status": "AUTHORITY_STATE_CONTRACT_PREVIEW_NOT_VERIFIED",
        "authoritative_external_anchor_verified": False,
        "authority_state_persistence_verified": False,
        "durable_single_use_claim_verified": False,
        "atomic_consume_implemented": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
    }
    contract["contract_sha256"] = _sha256_payload(contract)
    return contract


def validate_authority_state_contract_preview(contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise PermissionError("V31 authority-state contract must be an object")
    if contract.get("contract_version") != CONTRACT_VERSION or contract.get("prep_version") != PREP_VERSION:
        raise PermissionError("V31 authority-state contract identity mismatch")
    if contract.get("prep_base_main_commit") != BASE_MAIN_COMMIT:
        raise PermissionError("V31 base-main binding mismatch")
    path = contract.get("authority_state_path")
    if not isinstance(path, str) or not _is_absolute_path_text(path) or _looks_repo_local(path):
        raise PermissionError("V31 authority-state path is not external")
    if contract.get("required_storage_semantics") != "APPEND_ONLY_DELETE_DENIED_ROTATION_DENIED":
        raise PermissionError("V31 durable-store semantics mismatch")
    if not _is_sha256(contract.get("trust_anchor_fingerprint_sha256")):
        raise PermissionError("V31 trust-anchor fingerprint invalid")
    if not _is_git_oid(contract.get("final_main_commit")) or not _is_git_oid(contract.get("final_runner_blob_oid")):
        raise PermissionError("V31 final git binding invalid")
    if contract.get("status") != "AUTHORITY_STATE_CONTRACT_PREVIEW_NOT_VERIFIED":
        raise PermissionError("V31 contract must remain unverified")
    for key in (
        "authoritative_external_anchor_verified",
        "authority_state_persistence_verified",
        "durable_single_use_claim_verified",
        "atomic_consume_implemented",
        "explicit_user_approval_recorded",
        "live_authorization_materialized",
        "authorization_consumed",
        "execution_authorized",
        "model_run_authorized",
        "model_contact_authorized",
        "ready_for_model_contact",
        "model_qualified",
    ):
        if contract.get(key) is not False:
            raise PermissionError(f"V31 preview illegally escalated: {key}")
    expected = _sha256_payload({k: v for k, v in contract.items() if k != "contract_sha256"})
    if contract.get("contract_sha256") != expected:
        raise PermissionError("V31 authority-state contract hash mismatch")
    return contract


def build_explicit_run_approval_request_preview(
    *,
    gate_envelope: dict[str, Any],
    authority_contract: dict[str, Any],
) -> dict[str, Any]:
    """Freeze what a later explicit approval must refer to, without approving it."""
    v30.validate_proof_gate_envelope_preview(gate_envelope)
    validate_authority_state_contract_preview(authority_contract)
    proposed = deepcopy(gate_envelope["proposed_v25_binding"])
    request = {
        "approval_request_version": APPROVAL_REQUEST_VERSION,
        "prep_version": PREP_VERSION,
        "source_v30_gate_envelope_sha256": gate_envelope["proof_gate_envelope_sha256"],
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "requested_final_main_commit": authority_contract["final_main_commit"],
        "requested_final_runner_blob_oid": authority_contract["final_runner_blob_oid"],
        "requested_v25_binding": proposed,
        "requested_v25_binding_sha256": _sha256_payload(proposed),
        "approval_scope": "EXACTLY_ONE_SYNTHETIC_MODEL_RUN_NO_RETRY_NO_RERUN_NO_REPAIR",
        "status": "AWAITING_SEPARATE_EXPLICIT_USER_RUN_APPROVAL",
        "explicit_user_approval_recorded": False,
        "authoritative_external_anchor_verified": False,
        "durable_single_use_claim_verified": False,
        "atomic_consume_ready": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
    }
    request["approval_request_sha256"] = _sha256_payload(request)
    return request


def validate_explicit_run_approval_request_preview(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise PermissionError("V31 approval request must be an object")
    if request.get("approval_request_version") != APPROVAL_REQUEST_VERSION:
        raise PermissionError("V31 approval-request identity mismatch")
    if request.get("status") != "AWAITING_SEPARATE_EXPLICIT_USER_RUN_APPROVAL":
        raise PermissionError("V31 approval request must remain awaiting approval")
    if request.get("approval_scope") != "EXACTLY_ONE_SYNTHETIC_MODEL_RUN_NO_RETRY_NO_RERUN_NO_REPAIR":
        raise PermissionError("V31 approval scope mismatch")
    proposed = request.get("requested_v25_binding")
    if not isinstance(proposed, dict) or request.get("requested_v25_binding_sha256") != _sha256_payload(proposed):
        raise PermissionError("V31 requested V25 binding mismatch")
    for key in (
        "explicit_user_approval_recorded",
        "authoritative_external_anchor_verified",
        "durable_single_use_claim_verified",
        "atomic_consume_ready",
        "execution_authorized",
        "model_run_authorized",
        "model_contact_authorized",
        "ready_for_model_contact",
        "model_qualified",
    ):
        if request.get(key) is not False:
            raise PermissionError(f"V31 approval request illegally escalated: {key}")
    expected = _sha256_payload({k: v for k, v in request.items() if k != "approval_request_sha256"})
    if request.get("approval_request_sha256") != expected:
        raise PermissionError("V31 approval request hash mismatch")
    return request


def reject_any_live_use(*, authority_contract: dict[str, Any], approval_request: dict[str, Any]) -> None:
    validate_authority_state_contract_preview(authority_contract)
    validate_explicit_run_approval_request_preview(approval_request)
    raise PermissionError(
        "V31 remains non-live: external authority verification, separate explicit user approval, durable claim verification, and atomic consume are not implemented"
    )


def build_prep_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "3935a5bd514e9fe159bc217214a90a61c5eebcf0",
        "no_live_materializer": "materialize_live_authorization" not in globals(),
        "no_transport": "_default_transport" not in globals(),
        "no_preflight": "_default_preflight" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
        "no_approval_action": "approve" not in globals(),
    }
    return {
        "mode": "MODEL_FREE_AUTHORITY_STATE_ATOMIC_CONSUME_PREP",
        "status": "PASS" if all(checks.values()) else "FAIL_CLOSED",
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "authoritative_external_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "durable_single_use_claim_verified": False,
        "atomic_consume_implemented": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


def main() -> int:
    report = build_prep_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
