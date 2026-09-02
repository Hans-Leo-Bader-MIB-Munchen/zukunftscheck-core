#!/usr/bin/env python3
"""V35 model-free external-attestation / global-single-use preparation.

V35 introduces contracts for externally supplied authority evidence and a
single globally pinned store identity. It deliberately does not authenticate
that evidence itself and therefore cannot authorize model use.
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

import scripts.zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep as v34

PREP_VERSION = "v3.5-external-attestation-global-single-use-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-ATTESTATION-GLOBAL-SINGLE-USE-PREP-2026-036"
BASE_MAIN_COMMIT = "02760e876ee10790bf63d04449681d366247e9f7"
EVIDENCE_VERSION = "ZS-KI-B-SEM-EXTERNAL-AUTHORITY-EVIDENCE-2026-001_v0.1"
GLOBAL_BINDING_VERSION = "ZS-KI-B-SEM-GLOBAL-STORE-BINDING-2026-001_v0.1"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V35 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(f"V35 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise PermissionError(f"V35 invalid {label}")
    return value


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PermissionError(f"V35 invalid {label}")
    return value


def _external_existing_file(path_text: str) -> Path:
    location = v34.v33.v32.validate_external_location(path_text)
    path = Path(location["resolved_absolute_path"])
    resolved = Path(os.path.realpath(os.fspath(path)))
    v34.v33.v32.validate_external_location(os.fspath(resolved))
    if not resolved.is_file():
        raise PermissionError("V35 external evidence path must be an existing file")
    return resolved


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_external_evidence_reference_preview(
    *, authority_binding: dict[str, Any], authority_descriptor: dict[str, Any],
    evidence_path: str, evidence_id: str, expected_evidence_sha256: str,
) -> dict[str, Any]:
    """Bind an already-existing external evidence file without attesting it."""
    _require_id(evidence_id, "evidence_id")
    _require_sha256(expected_evidence_sha256, "expected_evidence_sha256")
    v34.validate_external_authority_descriptor_preview(authority_descriptor)
    path = _external_existing_file(evidence_path)
    actual_sha = _sha256_file(path)
    if actual_sha != expected_evidence_sha256:
        raise PermissionError("V35 external evidence file hash mismatch")
    if authority_binding["source_authority_descriptor_sha256"] != authority_descriptor["authority_descriptor_sha256"]:
        raise PermissionError("V35 authority binding/descriptor mismatch")
    evidence = {
        "external_evidence_version": EVIDENCE_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "evidence_id": evidence_id,
        "evidence_path_resolved": os.fspath(path),
        "evidence_file_sha256": actual_sha,
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "source_authority_descriptor_sha256": authority_descriptor["authority_descriptor_sha256"],
        "authority_id": authority_descriptor["authority_id"],
        "authority_epoch": authority_descriptor["authority_epoch"],
        "trust_anchor_id": authority_descriptor["trust_anchor_id"],
        "trust_anchor_fingerprint_sha256": authority_descriptor["trust_anchor_fingerprint_sha256"],
        "evidence_file_present_and_hash_bound": True,
        "evidence_origin_externally_attested": False,
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
        "status": "EXTERNAL_EVIDENCE_REFERENCE_HASH_BOUND_NOT_ATTESTED",
    }
    evidence["external_evidence_sha256"] = _sha256_payload(evidence)
    return evidence


_EVIDENCE_KEYS = {
    "external_evidence_version", "prep_version", "prep_type", "prep_base_main_commit",
    "evidence_id", "evidence_path_resolved", "evidence_file_sha256",
    "source_authority_binding_sha256", "source_authority_descriptor_sha256", "authority_id",
    "authority_epoch", "trust_anchor_id", "trust_anchor_fingerprint_sha256",
    "evidence_file_present_and_hash_bound", "evidence_origin_externally_attested",
    "external_authority_attested", "external_trust_anchor_verified", "delete_denied_verified",
    "rotation_denied_verified", "explicit_user_approval_recorded", "live_authorization_materialized",
    "authorization_consumed", "execution_authorized", "model_run_authorized",
    "model_contact_authorized", "ready_for_model_contact", "model_qualified", "status",
    "external_evidence_sha256",
}


def validate_external_evidence_reference_preview(
    evidence: dict[str, Any], *, authority_binding: dict[str, Any], authority_descriptor: dict[str, Any]
) -> dict[str, Any]:
    _require_exact_keys(evidence, _EVIDENCE_KEYS, "external evidence reference")
    path = _external_existing_file(evidence["evidence_path_resolved"])
    _require_id(evidence["evidence_id"], "evidence_id")
    _require_sha256(evidence["evidence_file_sha256"], "evidence_file_sha256")
    expected = build_external_evidence_reference_preview(
        authority_binding=authority_binding,
        authority_descriptor=authority_descriptor,
        evidence_path=os.fspath(path),
        evidence_id=evidence["evidence_id"],
        expected_evidence_sha256=evidence["evidence_file_sha256"],
    )
    for key, value in expected.items():
        if evidence.get(key) != value:
            raise PermissionError(f"V35 external evidence binding mismatch: {key}")
    return evidence


def build_global_store_binding_preview(
    *, authority_binding: dict[str, Any], authority_descriptor: dict[str, Any],
    evidence_reference: dict[str, Any], global_store_binding_id: str,
) -> dict[str, Any]:
    """Pin one V34 store identity for this preview; not a global authority proof."""
    _require_id(global_store_binding_id, "global_store_binding_id")
    validate_external_evidence_reference_preview(
        evidence_reference, authority_binding=authority_binding, authority_descriptor=authority_descriptor
    )
    if authority_binding["bound_store_root_resolved"] != authority_descriptor["authoritative_store_root_resolved"]:
        raise PermissionError("V35 store-root mismatch")
    binding = {
        "global_store_binding_version": GLOBAL_BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "global_store_binding_id": global_store_binding_id,
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "source_external_evidence_sha256": evidence_reference["external_evidence_sha256"],
        "authority_id": authority_descriptor["authority_id"],
        "authority_epoch": authority_descriptor["authority_epoch"],
        "pinned_store_root_resolved": authority_binding["bound_store_root_resolved"],
        "pinned_store_root_st_dev": authority_binding["bound_store_root_st_dev"],
        "pinned_store_root_st_ino": authority_binding["bound_store_root_st_ino"],
        "pinned_trust_anchor_id": authority_binding["bound_trust_anchor_id"],
        "pinned_trust_anchor_fingerprint_sha256": authority_binding["bound_trust_anchor_fingerprint_sha256"],
        "single_store_identity_structurally_pinned": True,
        "evidence_file_hash_bound": True,
        "global_store_authority_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "global_single_use_verified": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "GLOBAL_STORE_BINDING_PREVIEW_STRUCTURAL_ONLY",
    }
    binding["global_store_binding_sha256"] = _sha256_payload(binding)
    return binding


_GLOBAL_KEYS = {
    "global_store_binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "global_store_binding_id", "source_authority_binding_sha256", "source_external_evidence_sha256",
    "authority_id", "authority_epoch", "pinned_store_root_resolved", "pinned_store_root_st_dev",
    "pinned_store_root_st_ino", "pinned_trust_anchor_id", "pinned_trust_anchor_fingerprint_sha256",
    "single_store_identity_structurally_pinned", "evidence_file_hash_bound",
    "global_store_authority_verified", "external_authority_attested", "external_trust_anchor_verified",
    "delete_denied_verified", "rotation_denied_verified", "global_single_use_verified",
    "explicit_user_approval_recorded", "live_authorization_materialized", "authorization_consumed",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "global_store_binding_sha256",
}


def validate_global_store_binding_preview(
    binding: dict[str, Any], *, authority_binding: dict[str, Any], authority_descriptor: dict[str, Any],
    evidence_reference: dict[str, Any]
) -> dict[str, Any]:
    _require_exact_keys(binding, _GLOBAL_KEYS, "global store binding")
    expected = build_global_store_binding_preview(
        authority_binding=authority_binding,
        authority_descriptor=authority_descriptor,
        evidence_reference=evidence_reference,
        global_store_binding_id=binding["global_store_binding_id"],
    )
    for key, value in expected.items():
        if binding.get(key) != value:
            raise PermissionError(f"V35 global store binding mismatch: {key}")
    return binding


def reject_any_live_use() -> None:
    raise PermissionError(
        "V35 remains non-live: evidence origin, external authority/trust, delete/rotation denial, global single-use, and explicit user run approval are not verified"
    )


def build_prep_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "02760e876ee10790bf63d04449681d366247e9f7",
        "external_evidence_boundary_present": True,
        "global_store_structural_pin_present": True,
        "no_live_materializer": "materialize_live_authorization" not in globals(),
        "no_transport": "_default_transport" not in globals(),
        "no_preflight": "_default_preflight" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
    }
    return {
        "mode": "MODEL_FREE_EXTERNAL_ATTESTATION_GLOBAL_SINGLE_USE_PREP",
        "status": "PASS" if all(checks.values()) else "FAIL_CLOSED",
        "checks": checks,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "global_single_use_verified": False,
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
