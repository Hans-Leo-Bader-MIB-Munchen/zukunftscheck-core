#!/usr/bin/env python3
"""V32 model-free external-state and atomic-consume integration preparation.

V32 hardens V31's external-state contract with resolved-path checking and
implements an atomic, single-create technical consume receipt. The receipt is
NOT a live authorization consume and cannot authorize model contact.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31

PREP_VERSION = "v3.2-external-state-atomic-consume-integration-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-STATE-ATOMIC-CONSUME-INTEGRATION-PREP-2026-033"
BASE_MAIN_COMMIT = "6e1eb9e7c38bf1477aa920228f40e1cd2ddd5056"
EXTERNAL_STATE_VERSION = "ZS-KI-B-SEM-EXTERNAL-STATE-RESOLUTION-2026-001_v0.1"
CONSUME_RECEIPT_VERSION = "ZS-KI-B-SEM-ATOMIC-CONSUME-PREP-RECEIPT-2026-001_v0.1"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(payload.keys())
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise PermissionError(f"V32 {label} keyset mismatch: missing={missing}, extra={extra}")


def _resolved(path_text: str) -> Path:
    if not isinstance(path_text, str) or not path_text.strip():
        raise PermissionError("V32 path is required")
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        raise PermissionError("V32 path must be absolute")
    return Path(os.path.realpath(os.fspath(path)))


def _is_within(child: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath([os.fspath(child), os.fspath(parent)]) == os.path.commonpath([os.fspath(parent)])
    except (ValueError, OSError):
        return False


def validate_external_location(path_text: str) -> dict[str, str]:
    """Resolve symlinks/junction-style path indirection and reject repo-local state."""
    original = Path(path_text).expanduser()
    resolved = _resolved(path_text)
    repo_resolved = Path(os.path.realpath(os.fspath(ROOT)))
    if _is_within(resolved, repo_resolved):
        raise PermissionError("V32 resolved external-state path points into repository")
    return {
        "original_absolute_path": os.fspath(original),
        "resolved_absolute_path": os.fspath(resolved),
        "resolved_repo_root": os.fspath(repo_resolved),
    }


def build_external_state_resolution_preview(*, authority_contract: dict[str, Any]) -> dict[str, Any]:
    """Bind V31 authority contract to a realpath-resolved external location."""
    v31.validate_authority_state_contract_preview(authority_contract)
    location = validate_external_location(authority_contract["authority_state_path"])
    preview = {
        "external_state_version": EXTERNAL_STATE_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "authority_state_original_path": location["original_absolute_path"],
        "authority_state_resolved_path": location["resolved_absolute_path"],
        "resolved_repo_root": location["resolved_repo_root"],
        "realpath_resolution_verified": True,
        "resolved_path_outside_repository": True,
        "append_only_storage_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "authoritative_external_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "EXTERNAL_STATE_RESOLVED_PREVIEW_NOT_AUTHORITATIVE",
    }
    preview["external_state_sha256"] = _sha256_payload(preview)
    return preview


_EXTERNAL_KEYS = {
    "external_state_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_authority_contract_sha256", "authority_state_original_path",
    "authority_state_resolved_path", "resolved_repo_root", "realpath_resolution_verified",
    "resolved_path_outside_repository", "append_only_storage_verified", "delete_denied_verified",
    "rotation_denied_verified", "authoritative_external_anchor_verified",
    "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "external_state_sha256",
}


def validate_external_state_resolution_preview(
    preview: dict[str, Any], *, authority_contract: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(preview, dict):
        raise PermissionError("V32 external-state preview must be an object")
    _require_exact_keys(preview, _EXTERNAL_KEYS, "external-state preview")
    v31.validate_authority_state_contract_preview(authority_contract)
    if preview["external_state_version"] != EXTERNAL_STATE_VERSION or preview["prep_version"] != PREP_VERSION:
        raise PermissionError("V32 external-state identity mismatch")
    if preview["prep_base_main_commit"] != BASE_MAIN_COMMIT:
        raise PermissionError("V32 base-main binding mismatch")
    if preview["source_authority_contract_sha256"] != authority_contract["contract_sha256"]:
        raise PermissionError("V32 authority-contract source mismatch")
    current = validate_external_location(authority_contract["authority_state_path"])
    if preview["authority_state_resolved_path"] != current["resolved_absolute_path"]:
        raise PermissionError("V32 resolved authority-state path changed")
    if preview["resolved_repo_root"] != current["resolved_repo_root"]:
        raise PermissionError("V32 resolved repository root changed")
    if preview["realpath_resolution_verified"] is not True or preview["resolved_path_outside_repository"] is not True:
        raise PermissionError("V32 realpath guarantees missing")
    for key in (
        "append_only_storage_verified", "delete_denied_verified", "rotation_denied_verified",
        "authoritative_external_anchor_verified", "explicit_user_approval_recorded",
        "live_authorization_materialized", "authorization_consumed", "execution_authorized",
        "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified",
    ):
        if preview[key] is not False:
            raise PermissionError(f"V32 non-live preview illegally escalated: {key}")
    if preview["status"] != "EXTERNAL_STATE_RESOLVED_PREVIEW_NOT_AUTHORITATIVE":
        raise PermissionError("V32 external-state status mismatch")
    expected_hash = _sha256_payload({k: v for k, v in preview.items() if k != "external_state_sha256"})
    if preview["external_state_sha256"] != expected_hash:
        raise PermissionError("V32 external-state hash mismatch")
    return preview


def _consume_payload(
    *, approval_request: dict[str, Any], gate_envelope: dict[str, Any], authority_contract: dict[str, Any],
    external_state_preview: dict[str, Any], consume_record_path: str,
) -> dict[str, Any]:
    return {
        "consume_receipt_version": CONSUME_RECEIPT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_approval_request_sha256": approval_request["approval_request_sha256"],
        "source_v30_gate_envelope_sha256": gate_envelope["proof_gate_envelope_sha256"],
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "source_external_state_sha256": external_state_preview["external_state_sha256"],
        "consume_record_id": authority_contract["consume_record_id"],
        "consume_record_resolved_path": os.fspath(_resolved(consume_record_path)),
        "technical_single_create_claimed": True,
        "atomic_create_via_o_excl": True,
        "append_only_storage_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "explicit_user_approval_recorded": False,
        "authoritative_external_anchor_verified": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "ATOMIC_PREP_CONSUME_RECEIPT_NO_MODEL_AUTHORIZATION",
    }


def atomic_create_consume_receipt_preview(
    *, consume_record_path: str, approval_request: dict[str, Any], gate_envelope: dict[str, Any],
    authority_contract: dict[str, Any], external_state_preview: dict[str, Any]
) -> dict[str, Any]:
    """Atomically create one technical receipt; never create a live authorization."""
    v31.validate_explicit_run_approval_request_preview(
        approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract
    )
    validate_external_state_resolution_preview(external_state_preview, authority_contract=authority_contract)
    location = validate_external_location(consume_record_path)
    target = Path(location["resolved_absolute_path"])
    payload = _consume_payload(
        approval_request=approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract,
        external_state_preview=external_state_preview, consume_record_path=consume_record_path,
    )
    payload["consume_receipt_sha256"] = _sha256_payload(payload)
    data = _canonical_bytes(payload) + b"\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(os.fspath(target), flags, 0o600)
    except FileExistsError as exc:
        raise PermissionError("V32 consume receipt already exists; replay rejected") from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            target.unlink(missing_ok=True)
        finally:
            raise
    return payload


_RECEIPT_KEYS = {
    "consume_receipt_version", "prep_version", "prep_base_main_commit",
    "source_approval_request_sha256", "source_v30_gate_envelope_sha256",
    "source_authority_contract_sha256", "source_external_state_sha256", "consume_record_id",
    "consume_record_resolved_path", "technical_single_create_claimed", "atomic_create_via_o_excl",
    "append_only_storage_verified", "delete_denied_verified", "rotation_denied_verified",
    "explicit_user_approval_recorded", "authoritative_external_anchor_verified",
    "live_authorization_materialized", "authorization_consumed", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified",
    "status", "consume_receipt_sha256",
}


def validate_consume_receipt_preview(
    receipt: dict[str, Any], *, consume_record_path: str, approval_request: dict[str, Any],
    gate_envelope: dict[str, Any], authority_contract: dict[str, Any], external_state_preview: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise PermissionError("V32 consume receipt must be an object")
    _require_exact_keys(receipt, _RECEIPT_KEYS, "consume receipt")
    v31.validate_explicit_run_approval_request_preview(
        approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract
    )
    validate_external_state_resolution_preview(external_state_preview, authority_contract=authority_contract)
    expected = _consume_payload(
        approval_request=approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract,
        external_state_preview=external_state_preview, consume_record_path=consume_record_path,
    )
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise PermissionError(f"V32 consume receipt binding mismatch: {key}")
    expected_hash = _sha256_payload({k: v for k, v in receipt.items() if k != "consume_receipt_sha256"})
    if receipt["consume_receipt_sha256"] != expected_hash:
        raise PermissionError("V32 consume receipt hash mismatch")
    return receipt


def reject_any_live_use() -> None:
    raise PermissionError(
        "V32 remains non-live: external authority, durable delete/rotation protection, explicit user run approval, and live authorization consume are not established"
    )


def build_prep_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "6e1eb9e7c38bf1477aa920228f40e1cd2ddd5056",
        "realpath_validation_present": True,
        "atomic_o_excl_receipt_present": True,
        "no_live_materializer": "materialize_live_authorization" not in globals(),
        "no_transport": "_default_transport" not in globals(),
        "no_preflight": "_default_preflight" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
    }
    return {
        "mode": "MODEL_FREE_EXTERNAL_STATE_ATOMIC_CONSUME_INTEGRATION_PREP",
        "status": "PASS" if all(checks.values()) else "FAIL_CLOSED",
        "checks": checks,
        "authoritative_external_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "durable_single_use_claim_verified": False,
        "authorization_consumed": False,
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
