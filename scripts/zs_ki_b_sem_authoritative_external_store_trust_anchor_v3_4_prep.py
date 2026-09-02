#!/usr/bin/env python3
"""V34 model-free authoritative external-store / trust-anchor binding preparation.

V34 binds an already-existing V33 canonical store profile to an externally
supplied authority descriptor and trust-anchor fingerprint. It does NOT create
that authority, does NOT record user approval, and cannot authorize model use.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep as v33

PREP_VERSION = "v3.4-authoritative-external-store-trust-anchor-binding-prep"
PREP_TYPE = "ZS-KI-B-SEM-AUTHORITATIVE-EXTERNAL-STORE-TRUST-ANCHOR-BINDING-PREP-2026-035"
BASE_MAIN_COMMIT = "21ec6cd12394ff27d46c718f36a50590cbbfdf20"
AUTHORITY_DESCRIPTOR_VERSION = "ZS-KI-B-SEM-EXTERNAL-AUTHORITY-DESCRIPTOR-2026-001_v0.1"
AUTHORITY_BINDING_VERSION = "ZS-KI-B-SEM-EXTERNAL-AUTHORITY-BINDING-2026-001_v0.1"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V34 {label} must be an object")
    actual = set(payload.keys())
    if actual != expected:
        raise PermissionError(
            f"V34 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise PermissionError(f"V34 invalid {label}")
    return value


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PermissionError(f"V34 invalid {label}")
    return value


def build_external_authority_descriptor_preview(
    *, authority_id: str, store_root: str, trust_anchor_id: str,
    trust_anchor_fingerprint_sha256: str, authority_epoch: str,
) -> dict[str, Any]:
    """Build a non-authoritative descriptor preview for an externally controlled authority.

    This helper intentionally does not prove control over the store or trust anchor.
    """
    _require_id(authority_id, "authority_id")
    _require_id(trust_anchor_id, "trust_anchor_id")
    _require_id(authority_epoch, "authority_epoch")
    _require_sha256(trust_anchor_fingerprint_sha256, "trust_anchor_fingerprint_sha256")
    root = v33._resolved_external_dir(store_root)
    root_dev, root_ino = v33._root_identity(root)
    descriptor = {
        "authority_descriptor_version": AUTHORITY_DESCRIPTOR_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "authority_id": authority_id,
        "authority_epoch": authority_epoch,
        "authoritative_store_root_resolved": os.fspath(root),
        "authoritative_store_root_st_dev": root_dev,
        "authoritative_store_root_st_ino": root_ino,
        "store_root_identity_persisted": True,
        "trust_anchor_id": trust_anchor_id,
        "trust_anchor_fingerprint_sha256": trust_anchor_fingerprint_sha256,
        "descriptor_externally_attested": False,
        "store_control_externally_verified": False,
        "trust_anchor_externally_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "EXTERNAL_AUTHORITY_DESCRIPTOR_PREVIEW_NOT_ATTESTED",
    }
    descriptor["authority_descriptor_sha256"] = _sha256_payload(descriptor)
    return descriptor


_DESCRIPTOR_KEYS = {
    "authority_descriptor_version", "prep_version", "prep_type", "prep_base_main_commit",
    "authority_id", "authority_epoch", "authoritative_store_root_resolved",
    "authoritative_store_root_st_dev", "authoritative_store_root_st_ino",
    "store_root_identity_persisted", "trust_anchor_id", "trust_anchor_fingerprint_sha256",
    "descriptor_externally_attested", "store_control_externally_verified",
    "trust_anchor_externally_verified", "delete_denied_verified", "rotation_denied_verified",
    "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "authority_descriptor_sha256",
}


def validate_external_authority_descriptor_preview(descriptor: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(descriptor, _DESCRIPTOR_KEYS, "authority descriptor")
    if descriptor["authority_descriptor_version"] != AUTHORITY_DESCRIPTOR_VERSION:
        raise PermissionError("V34 authority descriptor version mismatch")
    if descriptor["prep_version"] != PREP_VERSION or descriptor["prep_type"] != PREP_TYPE:
        raise PermissionError("V34 authority descriptor prep identity mismatch")
    if descriptor["prep_base_main_commit"] != BASE_MAIN_COMMIT:
        raise PermissionError("V34 authority descriptor base-main mismatch")
    _require_id(descriptor["authority_id"], "authority_id")
    _require_id(descriptor["authority_epoch"], "authority_epoch")
    _require_id(descriptor["trust_anchor_id"], "trust_anchor_id")
    _require_sha256(descriptor["trust_anchor_fingerprint_sha256"], "trust_anchor_fingerprint_sha256")
    root = v33._resolved_external_dir(descriptor["authoritative_store_root_resolved"])
    current_identity = v33._root_identity(root)
    if os.fspath(root) != descriptor["authoritative_store_root_resolved"]:
        raise PermissionError("V34 authoritative store root path changed")
    if current_identity != (
        descriptor["authoritative_store_root_st_dev"], descriptor["authoritative_store_root_st_ino"]
    ):
        raise PermissionError("V34 authoritative store root identity changed")
    if descriptor["store_root_identity_persisted"] is not True:
        raise PermissionError("V34 store-root identity persistence missing")
    for key in (
        "descriptor_externally_attested", "store_control_externally_verified",
        "trust_anchor_externally_verified", "delete_denied_verified", "rotation_denied_verified",
        "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
        "execution_authorized", "model_run_authorized", "model_contact_authorized",
        "ready_for_model_contact", "model_qualified",
    ):
        if descriptor[key] is not False:
            raise PermissionError(f"V34 descriptor illegally escalated: {key}")
    if descriptor["status"] != "EXTERNAL_AUTHORITY_DESCRIPTOR_PREVIEW_NOT_ATTESTED":
        raise PermissionError("V34 authority descriptor status mismatch")
    expected_hash = _sha256_payload({k: v for k, v in descriptor.items() if k != "authority_descriptor_sha256"})
    if descriptor["authority_descriptor_sha256"] != expected_hash:
        raise PermissionError("V34 authority descriptor hash mismatch")
    return descriptor


def build_authority_binding_preview(
    *, authority_descriptor: dict[str, Any], store_profile: dict[str, Any],
    authority_contract: dict[str, Any], external_state_preview: dict[str, Any], store_root: str,
) -> dict[str, Any]:
    validate_external_authority_descriptor_preview(authority_descriptor)
    v33.validate_canonical_store_profile_preview(
        store_profile, authority_contract=authority_contract,
        external_state_preview=external_state_preview, store_root=store_root,
    )
    if authority_descriptor["authoritative_store_root_resolved"] != store_profile["canonical_store_root_resolved"]:
        raise PermissionError("V34 authority/store-profile root mismatch")
    descriptor_identity = (
        authority_descriptor["authoritative_store_root_st_dev"],
        authority_descriptor["authoritative_store_root_st_ino"],
    )
    profile_identity = (
        store_profile["canonical_store_root_st_dev"], store_profile["canonical_store_root_st_ino"]
    )
    if descriptor_identity != profile_identity:
        raise PermissionError("V34 authority/store-profile root identity mismatch")
    if authority_descriptor["trust_anchor_id"] != authority_contract["trust_anchor_id"]:
        raise PermissionError("V34 trust-anchor id mismatch against authority contract")
    if authority_descriptor["trust_anchor_fingerprint_sha256"] != authority_contract["trust_anchor_fingerprint_sha256"]:
        raise PermissionError("V34 trust-anchor fingerprint mismatch against authority contract")
    binding = {
        "authority_binding_version": AUTHORITY_BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_authority_descriptor_sha256": authority_descriptor["authority_descriptor_sha256"],
        "source_store_profile_sha256": store_profile["store_profile_sha256"],
        "source_authority_contract_sha256": authority_contract["contract_sha256"],
        "source_external_state_sha256": external_state_preview["external_state_sha256"],
        "authority_id": authority_descriptor["authority_id"],
        "authority_epoch": authority_descriptor["authority_epoch"],
        "bound_store_root_resolved": store_profile["canonical_store_root_resolved"],
        "bound_store_root_st_dev": store_profile["canonical_store_root_st_dev"],
        "bound_store_root_st_ino": store_profile["canonical_store_root_st_ino"],
        "bound_trust_anchor_id": authority_descriptor["trust_anchor_id"],
        "bound_trust_anchor_fingerprint_sha256": authority_descriptor["trust_anchor_fingerprint_sha256"],
        "descriptor_store_profile_identity_match": True,
        "descriptor_contract_trust_anchor_match": True,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "AUTHORITY_BINDING_PREVIEW_STRUCTURAL_ONLY",
    }
    binding["authority_binding_sha256"] = _sha256_payload(binding)
    return binding


_BINDING_KEYS = {
    "authority_binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_authority_descriptor_sha256", "source_store_profile_sha256",
    "source_authority_contract_sha256", "source_external_state_sha256", "authority_id",
    "authority_epoch", "bound_store_root_resolved", "bound_store_root_st_dev",
    "bound_store_root_st_ino", "bound_trust_anchor_id", "bound_trust_anchor_fingerprint_sha256",
    "descriptor_store_profile_identity_match", "descriptor_contract_trust_anchor_match",
    "external_authority_attested", "external_trust_anchor_verified", "delete_denied_verified",
    "rotation_denied_verified", "explicit_user_approval_recorded", "live_authorization_materialized",
    "authorization_consumed", "execution_authorized", "model_run_authorized",
    "model_contact_authorized", "ready_for_model_contact", "model_qualified", "status",
    "authority_binding_sha256",
}


def validate_authority_binding_preview(
    binding: dict[str, Any], *, authority_descriptor: dict[str, Any], store_profile: dict[str, Any],
    authority_contract: dict[str, Any], external_state_preview: dict[str, Any], store_root: str,
) -> dict[str, Any]:
    _require_exact_keys(binding, _BINDING_KEYS, "authority binding")
    expected = build_authority_binding_preview(
        authority_descriptor=authority_descriptor, store_profile=store_profile,
        authority_contract=authority_contract, external_state_preview=external_state_preview,
        store_root=store_root,
    )
    for key, value in expected.items():
        if binding.get(key) != value:
            raise PermissionError(f"V34 authority binding mismatch: {key}")
    return binding


def reject_any_live_use() -> None:
    raise PermissionError(
        "V34 remains non-live: external authority attestation, trust-anchor verification, delete/rotation denial, and explicit user run approval are not established"
    )


def build_prep_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "21ec6cd12394ff27d46c718f36a50590cbbfdf20",
        "authority_descriptor_structural_binding_present": True,
        "store_identity_cross_binding_present": True,
        "trust_anchor_cross_binding_present": True,
        "no_live_materializer": "materialize_live_authorization" not in globals(),
        "no_transport": "_default_transport" not in globals(),
        "no_preflight": "_default_preflight" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
    }
    return {
        "mode": "MODEL_FREE_AUTHORITATIVE_EXTERNAL_STORE_TRUST_ANCHOR_BINDING_PREP",
        "status": "PASS" if all(checks.values()) else "FAIL_CLOSED",
        "checks": checks,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "explicit_user_approval_recorded": False,
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
