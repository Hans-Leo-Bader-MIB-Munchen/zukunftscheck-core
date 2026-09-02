#!/usr/bin/env python3
"""V36 model-free external attestation / persistent global-single-use prep.

V36 defines the contracts a later external verifier and authoritative persistence
backend must satisfy. It does not verify a signature, trust anchor, persistence
backend, user approval, or authorize model use.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import scripts.zs_ki_b_sem_external_attestation_global_single_use_v3_5_prep as v35

PREP_VERSION = "v3.6-external-attestation-persistent-global-single-use-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-ATTESTATION-PERSISTENT-GLOBAL-SINGLE-USE-PREP-2026-037"
BASE_MAIN_COMMIT = "7113d336238fa48806dda219b4188a56a133c783"
ATTESTATION_CONTRACT_VERSION = "ZS-KI-B-SEM-ATTESTATION-VERIFICATION-CONTRACT-2026-001_v0.1"
PERSISTENCE_CONTRACT_VERSION = "ZS-KI-B-SEM-PERSISTENT-GLOBAL-STORE-CONTRACT-2026-001_v0.1"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_SIGNATURE_ALGORITHMS = {"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"}


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V36 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(f"V36 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise PermissionError(f"V36 invalid {label}")
    return value


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PermissionError(f"V36 invalid {label}")
    return value


def _validate_v35_sources(*, global_store_binding: dict[str, Any], authority_binding: dict[str, Any],
                          authority_descriptor: dict[str, Any], store_profile: dict[str, Any],
                          authority_contract: dict[str, Any], external_state_preview: dict[str, Any],
                          store_root: str, evidence_reference: dict[str, Any]) -> None:
    v35.validate_global_store_binding_preview(
        global_store_binding,
        authority_binding=authority_binding,
        authority_descriptor=authority_descriptor,
        store_profile=store_profile,
        authority_contract=authority_contract,
        external_state_preview=external_state_preview,
        store_root=store_root,
        evidence_reference=evidence_reference,
    )


def build_attestation_verification_contract_preview(*, global_store_binding: dict[str, Any],
                                                     evidence_reference: dict[str, Any],
                                                     authority_binding: dict[str, Any],
                                                     authority_descriptor: dict[str, Any],
                                                     store_profile: dict[str, Any],
                                                     authority_contract: dict[str, Any],
                                                     external_state_preview: dict[str, Any],
                                                     store_root: str, verifier_id: str,
                                                     verifier_key_id: str,
                                                     verifier_key_fingerprint_sha256: str,
                                                     signature_algorithm: str) -> dict[str, Any]:
    _validate_v35_sources(
        global_store_binding=global_store_binding, authority_binding=authority_binding,
        authority_descriptor=authority_descriptor, store_profile=store_profile,
        authority_contract=authority_contract, external_state_preview=external_state_preview,
        store_root=store_root, evidence_reference=evidence_reference,
    )
    _require_id(verifier_id, "verifier_id")
    _require_id(verifier_key_id, "verifier_key_id")
    _require_sha256(verifier_key_fingerprint_sha256, "verifier_key_fingerprint_sha256")
    if signature_algorithm not in _ALLOWED_SIGNATURE_ALGORITHMS:
        raise PermissionError("V36 unsupported signature algorithm")
    contract = {
        "attestation_contract_version": ATTESTATION_CONTRACT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_global_store_binding_sha256": global_store_binding["global_store_binding_sha256"],
        "source_external_evidence_sha256": evidence_reference["external_evidence_sha256"],
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "authority_id": authority_descriptor["authority_id"],
        "authority_epoch": authority_descriptor["authority_epoch"],
        "verifier_id": verifier_id,
        "verifier_key_id": verifier_key_id,
        "verifier_key_fingerprint_sha256": verifier_key_fingerprint_sha256,
        "signature_algorithm": signature_algorithm,
        "signed_payload_sha256_required": evidence_reference["evidence_file_sha256"],
        "external_signature_verification_required": True,
        "external_verifier_identity_verification_required": True,
        "trust_anchor_chain_verification_required": True,
        "external_signature_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "ATTESTATION_VERIFICATION_CONTRACT_PREVIEW_REQUIREMENTS_ONLY",
    }
    contract["attestation_contract_sha256"] = _sha256_payload(contract)
    return contract


_ATTESTATION_KEYS = {
    "attestation_contract_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_global_store_binding_sha256", "source_external_evidence_sha256",
    "source_authority_binding_sha256", "authority_id", "authority_epoch", "verifier_id",
    "verifier_key_id", "verifier_key_fingerprint_sha256", "signature_algorithm",
    "signed_payload_sha256_required", "external_signature_verification_required",
    "external_verifier_identity_verification_required", "trust_anchor_chain_verification_required",
    "external_signature_verified", "external_verifier_identity_verified",
    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact",
    "model_qualified", "status", "attestation_contract_sha256",
}


def validate_attestation_verification_contract_preview(contract: dict[str, Any], **sources: Any) -> dict[str, Any]:
    _require_exact_keys(contract, _ATTESTATION_KEYS, "attestation contract")
    expected = build_attestation_verification_contract_preview(
        verifier_id=contract["verifier_id"], verifier_key_id=contract["verifier_key_id"],
        verifier_key_fingerprint_sha256=contract["verifier_key_fingerprint_sha256"],
        signature_algorithm=contract["signature_algorithm"], **sources,
    )
    if contract != expected:
        raise PermissionError("V36 attestation contract mismatch")
    return contract


def build_persistent_global_store_contract_preview(*, global_store_binding: dict[str, Any],
                                                    evidence_reference: dict[str, Any],
                                                    authority_binding: dict[str, Any],
                                                    authority_descriptor: dict[str, Any],
                                                    store_profile: dict[str, Any],
                                                    authority_contract: dict[str, Any],
                                                    external_state_preview: dict[str, Any],
                                                    store_root: str, registry_id: str,
                                                    namespace_id: str,
                                                    persistence_policy_id: str) -> dict[str, Any]:
    _validate_v35_sources(
        global_store_binding=global_store_binding, authority_binding=authority_binding,
        authority_descriptor=authority_descriptor, store_profile=store_profile,
        authority_contract=authority_contract, external_state_preview=external_state_preview,
        store_root=store_root, evidence_reference=evidence_reference,
    )
    _require_id(registry_id, "registry_id")
    _require_id(namespace_id, "namespace_id")
    _require_id(persistence_policy_id, "persistence_policy_id")
    contract = {
        "persistence_contract_version": PERSISTENCE_CONTRACT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_global_store_binding_sha256": global_store_binding["global_store_binding_sha256"],
        "registry_id": registry_id,
        "namespace_id": namespace_id,
        "persistence_policy_id": persistence_policy_id,
        "pinned_store_root_resolved": global_store_binding["pinned_store_root_resolved"],
        "pinned_store_root_st_dev": global_store_binding["pinned_store_root_st_dev"],
        "pinned_store_root_st_ino": global_store_binding["pinned_store_root_st_ino"],
        "append_only_or_worm_required": True,
        "delete_denial_required": True,
        "alternate_root_rotation_denial_required": True,
        "global_record_uniqueness_required": True,
        "cross_process_atomic_claim_required": True,
        "crash_durable_commit_required": True,
        "registry_externally_authoritative_verified": False,
        "append_only_or_worm_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "global_single_use_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "PERSISTENT_GLOBAL_STORE_CONTRACT_PREVIEW_REQUIREMENTS_ONLY",
    }
    contract["persistence_contract_sha256"] = _sha256_payload(contract)
    return contract


_PERSISTENCE_KEYS = {
    "persistence_contract_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_global_store_binding_sha256", "registry_id", "namespace_id", "persistence_policy_id",
    "pinned_store_root_resolved", "pinned_store_root_st_dev", "pinned_store_root_st_ino",
    "append_only_or_worm_required", "delete_denial_required", "alternate_root_rotation_denial_required",
    "global_record_uniqueness_required", "cross_process_atomic_claim_required", "crash_durable_commit_required",
    "registry_externally_authoritative_verified", "append_only_or_worm_verified",
    "delete_denied_verified", "rotation_denied_verified", "global_single_use_verified",
    "execution_authorized", "model_run_authorized", "model_contact_authorized",
    "ready_for_model_contact", "model_qualified", "status", "persistence_contract_sha256",
}


def validate_persistent_global_store_contract_preview(contract: dict[str, Any], **sources: Any) -> dict[str, Any]:
    _require_exact_keys(contract, _PERSISTENCE_KEYS, "persistence contract")
    expected = build_persistent_global_store_contract_preview(
        registry_id=contract["registry_id"], namespace_id=contract["namespace_id"],
        persistence_policy_id=contract["persistence_policy_id"], **sources,
    )
    if contract != expected:
        raise PermissionError("V36 persistence contract mismatch")
    return contract


def reject_any_live_use() -> None:
    raise PermissionError("V36 is requirements-only and cannot authorize model contact or model execution")


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_EXTERNAL_ATTESTATION_PERSISTENT_GLOBAL_SINGLE_USE_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "external_signature_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "registry_externally_authoritative_verified": False,
        "delete_denied_verified": False,
        "rotation_denied_verified": False,
        "global_single_use_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_prep_report(), ensure_ascii=False, indent=2))
