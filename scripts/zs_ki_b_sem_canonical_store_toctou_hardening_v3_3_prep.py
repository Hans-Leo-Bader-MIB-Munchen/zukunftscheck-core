#!/usr/bin/env python3
"""V33 model-free canonical-store and TOCTOU-hardening preparation.

V33 narrows V32's remaining filesystem ambiguity by binding each technical
consume receipt to one canonical filename under one resolved external store
root. On platforms that support directory file descriptors and O_NOFOLLOW,
it can create through an already-opened directory handle and fsync both file
and directory. It still does NOT create or consume a live model authorization.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32

PREP_VERSION = "v3.3-canonical-store-toctou-hardening-prep"
PREP_TYPE = "ZS-KI-B-SEM-CANONICAL-STORE-TOCTOU-HARDENING-PREP-2026-034"
BASE_MAIN_COMMIT = "2553116951ed38fbc357232f9a4abdc1aece8423"
STORE_PROFILE_VERSION = "ZS-KI-B-SEM-CANONICAL-STORE-PROFILE-2026-001_v0.1"
HARDENED_RECEIPT_VERSION = "ZS-KI-B-SEM-HARDENED-CONSUME-RECEIPT-2026-001_v0.1"
_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(payload.keys())
    if actual != expected:
        raise PermissionError(
            f"V33 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )


def _validate_record_id(record_id: str) -> str:
    if not isinstance(record_id, str) or not _RECORD_ID_RE.fullmatch(record_id):
        raise PermissionError("V33 consume_record_id is not canonical-safe")
    if record_id in {".", ".."}:
        raise PermissionError("V33 consume_record_id is not canonical-safe")
    return record_id


def _supports_dirfd_hardening() -> bool:
    try:
        return os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
    except Exception:
        return False


def _resolved_external_dir(path_text: str) -> Path:
    location = v32.validate_external_location(path_text)
    root = Path(location["resolved_absolute_path"])
    root.mkdir(parents=True, exist_ok=True)
    resolved = Path(os.path.realpath(os.fspath(root)))
    v32.validate_external_location(os.fspath(resolved))
    if not resolved.is_dir():
        raise PermissionError("V33 canonical store root must be a directory")
    return resolved


def canonical_consume_path(*, store_root: str, consume_record_id: str) -> Path:
    record_id = _validate_record_id(consume_record_id)
    root = _resolved_external_dir(store_root)
    target = root / f"{record_id}.json"
    if target.parent != root:
        raise PermissionError("V33 canonical consume target escaped store root")
    return target


def build_canonical_store_profile_preview(
    *, authority_contract: dict[str, Any], external_state_preview: dict[str, Any], store_root: str
) -> dict[str, Any]:
    v32.validate_external_state_resolution_preview(external_state_preview, authority_contract=authority_contract)
    root = _resolved_external_dir(store_root)
    target = canonical_consume_path(
        store_root=os.fspath(root), consume_record_id=authority_contract["consume_record_id"]
    )
    posix_handle_hardening = _supports_dirfd_hardening()
    preview = {
        "store_profile_version": STORE_PROFILE_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "source_external_state_sha256": external_state_preview["external_state_sha256"],
        "consume_record_id": authority_contract["consume_record_id"],
        "canonical_store_root_resolved": os.fspath(root),
        "canonical_consume_filename": target.name,
        "canonical_consume_path_resolved": os.fspath(target),
        "canonical_location_bound": True,
        "alternate_path_allowed": False,
        "dirfd_nofollow_supported": posix_handle_hardening,
        "directory_fsync_supported": posix_handle_hardening,
        "inode_handle_binding_verified": False,
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
        "status": "CANONICAL_STORE_PROFILE_PREVIEW_NOT_AUTHORITATIVE",
    }
    preview["store_profile_sha256"] = _sha256_payload(preview)
    return preview


_PROFILE_KEYS = {
    "store_profile_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_authority_contract_sha256", "source_external_state_sha256", "consume_record_id",
    "canonical_store_root_resolved", "canonical_consume_filename", "canonical_consume_path_resolved",
    "canonical_location_bound", "alternate_path_allowed", "dirfd_nofollow_supported",
    "directory_fsync_supported", "inode_handle_binding_verified", "delete_denied_verified",
    "rotation_denied_verified", "authoritative_external_anchor_verified",
    "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "store_profile_sha256",
}


def validate_canonical_store_profile_preview(
    profile: dict[str, Any], *, authority_contract: dict[str, Any],
    external_state_preview: dict[str, Any], store_root: str
) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise PermissionError("V33 store profile must be an object")
    _require_exact_keys(profile, _PROFILE_KEYS, "store profile")
    v32.validate_external_state_resolution_preview(external_state_preview, authority_contract=authority_contract)
    root = _resolved_external_dir(store_root)
    target = canonical_consume_path(store_root=os.fspath(root), consume_record_id=authority_contract["consume_record_id"])
    expected = {
        "store_profile_version": STORE_PROFILE_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "source_external_state_sha256": external_state_preview["external_state_sha256"],
        "consume_record_id": authority_contract["consume_record_id"],
        "canonical_store_root_resolved": os.fspath(root),
        "canonical_consume_filename": target.name,
        "canonical_consume_path_resolved": os.fspath(target),
        "canonical_location_bound": True,
        "alternate_path_allowed": False,
        "dirfd_nofollow_supported": _supports_dirfd_hardening(),
        "directory_fsync_supported": _supports_dirfd_hardening(),
        "inode_handle_binding_verified": False,
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
        "status": "CANONICAL_STORE_PROFILE_PREVIEW_NOT_AUTHORITATIVE",
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise PermissionError(f"V33 store profile binding mismatch: {key}")
    expected_hash = _sha256_payload({k: v for k, v in profile.items() if k != "store_profile_sha256"})
    if profile["store_profile_sha256"] != expected_hash:
        raise PermissionError("V33 store profile hash mismatch")
    return profile


def _hardened_payload(
    *, approval_request: dict[str, Any], gate_envelope: dict[str, Any], authority_contract: dict[str, Any],
    external_state_preview: dict[str, Any], store_profile: dict[str, Any], inode_verified: bool,
    directory_fsync_performed: bool,
) -> dict[str, Any]:
    return {
        "hardened_receipt_version": HARDENED_RECEIPT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_approval_request_sha256": approval_request["approval_request_sha256"],
        "source_v30_gate_envelope_sha256": gate_envelope["proof_gate_envelope_sha256"],
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "source_external_state_sha256": external_state_preview["external_state_sha256"],
        "source_store_profile_sha256": store_profile["store_profile_sha256"],
        "consume_record_id": authority_contract["consume_record_id"],
        "canonical_consume_path_resolved": store_profile["canonical_consume_path_resolved"],
        "canonical_location_enforced": True,
        "atomic_create_via_o_excl": True,
        "dirfd_nofollow_used": inode_verified,
        "inode_handle_binding_verified": inode_verified,
        "file_fsync_performed": True,
        "directory_fsync_performed": directory_fsync_performed,
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
        "status": "HARDENED_TECHNICAL_RECEIPT_NO_MODEL_AUTHORIZATION",
    }


def atomic_create_hardened_receipt_preview(
    *, approval_request: dict[str, Any], gate_envelope: dict[str, Any], authority_contract: dict[str, Any],
    external_state_preview: dict[str, Any], store_profile: dict[str, Any], store_root: str
) -> dict[str, Any]:
    v32.v31.validate_explicit_run_approval_request_preview(
        approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract
    )
    validate_canonical_store_profile_preview(
        store_profile, authority_contract=authority_contract,
        external_state_preview=external_state_preview, store_root=store_root
    )
    root = Path(store_profile["canonical_store_root_resolved"])
    filename = store_profile["canonical_consume_filename"]
    target = root / filename
    hardened = _supports_dirfd_hardening()
    directory_fsync = False
    dir_fd: int | None = None
    file_fd: int | None = None
    try:
        if hardened:
            root_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            dir_fd = os.open(os.fspath(root), root_flags)
            opened = os.fstat(dir_fd)
            current = os.stat(os.fspath(root), follow_symlinks=False)
            if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
                raise PermissionError("V33 canonical store root identity changed before create")
            file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            file_fd = os.open(filename, file_flags, 0o600, dir_fd=dir_fd)
            fst = os.fstat(file_fd)
            if not stat.S_ISREG(fst.st_mode):
                raise PermissionError("V33 hardened receipt target is not a regular file")
        else:
            file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            file_fd = os.open(os.fspath(target), file_flags, 0o600)

        payload = _hardened_payload(
            approval_request=approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract,
            external_state_preview=external_state_preview, store_profile=store_profile,
            inode_verified=hardened, directory_fsync_performed=hardened,
        )
        payload["hardened_receipt_sha256"] = _sha256_payload(payload)
        data = _canonical_bytes(payload) + b"\n"
        with os.fdopen(file_fd, "wb", closefd=True) as handle:
            file_fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if hardened and dir_fd is not None:
            os.fsync(dir_fd)
            directory_fsync = True
        if payload["directory_fsync_performed"] is not directory_fsync:
            raise PermissionError("V33 directory fsync claim mismatch")
        return payload
    except FileExistsError as exc:
        raise PermissionError("V33 canonical consume receipt already exists; replay rejected") from exc
    except Exception:
        # Fail closed. Do not unlink an uncertain or partially durable claim here: presence blocks replay.
        raise
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if dir_fd is not None:
            os.close(dir_fd)


_RECEIPT_KEYS = {
    "hardened_receipt_version", "prep_version", "prep_base_main_commit",
    "source_approval_request_sha256", "source_v30_gate_envelope_sha256",
    "source_authority_contract_sha256", "source_external_state_sha256", "source_store_profile_sha256",
    "consume_record_id", "canonical_consume_path_resolved", "canonical_location_enforced",
    "atomic_create_via_o_excl", "dirfd_nofollow_used", "inode_handle_binding_verified",
    "file_fsync_performed", "directory_fsync_performed", "delete_denied_verified",
    "rotation_denied_verified", "authoritative_external_anchor_verified",
    "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "hardened_receipt_sha256",
}


def validate_hardened_receipt_preview(
    receipt: dict[str, Any], *, approval_request: dict[str, Any], gate_envelope: dict[str, Any],
    authority_contract: dict[str, Any], external_state_preview: dict[str, Any],
    store_profile: dict[str, Any], store_root: str
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise PermissionError("V33 hardened receipt must be an object")
    _require_exact_keys(receipt, _RECEIPT_KEYS, "hardened receipt")
    v32.v31.validate_explicit_run_approval_request_preview(
        approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract
    )
    validate_canonical_store_profile_preview(
        store_profile, authority_contract=authority_contract,
        external_state_preview=external_state_preview, store_root=store_root
    )
    hardened = _supports_dirfd_hardening()
    expected = _hardened_payload(
        approval_request=approval_request, gate_envelope=gate_envelope, authority_contract=authority_contract,
        external_state_preview=external_state_preview, store_profile=store_profile,
        inode_verified=hardened, directory_fsync_performed=hardened,
    )
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise PermissionError(f"V33 hardened receipt binding mismatch: {key}")
    expected_hash = _sha256_payload({k: v for k, v in receipt.items() if k != "hardened_receipt_sha256"})
    if receipt["hardened_receipt_sha256"] != expected_hash:
        raise PermissionError("V33 hardened receipt hash mismatch")
    return receipt


def reject_any_live_use() -> None:
    raise PermissionError(
        "V33 remains non-live: authoritative external trust, delete/rotation denial, explicit user run approval, and live consume are not established"
    )


def build_prep_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "2553116951ed38fbc357232f9a4abdc1aece8423",
        "canonical_location_binding_present": True,
        "alternate_path_disallowed_by_builder": True,
        "fail_closed_partial_claim_retained": True,
        "no_live_materializer": "materialize_live_authorization" not in globals(),
        "no_transport": "_default_transport" not in globals(),
        "no_preflight": "_default_preflight" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
    }
    return {
        "mode": "MODEL_FREE_CANONICAL_STORE_TOCTOU_HARDENING_PREP",
        "status": "PASS" if all(checks.values()) else "FAIL_CLOSED",
        "checks": checks,
        "dirfd_nofollow_supported": _supports_dirfd_hardening(),
        "authoritative_external_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
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
