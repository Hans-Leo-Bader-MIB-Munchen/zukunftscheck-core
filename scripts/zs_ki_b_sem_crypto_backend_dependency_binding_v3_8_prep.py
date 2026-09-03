#!/usr/bin/env python3
"""V38 model-free crypto backend/dependency binding preparation.

This module selects and structurally binds the future cryptographic backend
without importing or executing that backend and without performing signature
verification, trust validation, authorization, or model contact.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import scripts.zs_ki_b_sem_external_signature_trust_verification_v3_7_prep as v37

PREP_VERSION = "v3.8-crypto-backend-dependency-binding-prep"
PREP_TYPE = "ZS-KI-B-SEM-CRYPTO-BACKEND-DEPENDENCY-BINDING-PREP-2026-001"
BASE_MAIN_COMMIT = "71d5a70420b4c976c0e822ba34514a63c6b7ac87"
BINDING_VERSION = "ZS-KI-B-SEM-CRYPTO-BACKEND-BINDING-2026-001_v0.2"
SOURCE_V37_SCRIPT_BLOB_SHA = "a7c2192983be9c580b3dd8b8e68ee3e80e7afb02"

BACKEND_PACKAGE = "cryptography"
BACKEND_VERSION = "50.0.1"
BACKEND_REQUIREMENT = "cryptography==50.0.1"
BACKEND_API_FAMILY = "cryptography.hazmat.primitives.asymmetric"
PUBLIC_KEY_SERIALIZATION = "DER_SUBJECT_PUBLIC_KEY_INFO"

ALGORITHM_PROFILES: dict[str, dict[str, Any]] = {
    "ED25519": {
        "public_key_type": "Ed25519PublicKey",
        "public_key_serialization": PUBLIC_KEY_SERIALIZATION,
        "message_mode": "DIRECT_MESSAGE_BYTES",
        "hash_algorithm": None,
        "signature_encoding": "RAW_64_BYTES",
        "curve": "ED25519",
        "rsa_padding": None,
        "mgf_hash": None,
        "pss_salt_length": None,
    },
    "ECDSA-P256-SHA256": {
        "public_key_type": "EllipticCurvePublicKey",
        "public_key_serialization": PUBLIC_KEY_SERIALIZATION,
        "message_mode": "DIRECT_MESSAGE_BYTES",
        "hash_algorithm": "SHA256",
        "signature_encoding": "ASN1_DER_ECDSA_R_S",
        "curve": "SECP256R1",
        "rsa_padding": None,
        "mgf_hash": None,
        "pss_salt_length": None,
    },
    "RSA-PSS-SHA256": {
        "public_key_type": "RSAPublicKey",
        "public_key_serialization": PUBLIC_KEY_SERIALIZATION,
        "message_mode": "DIRECT_MESSAGE_BYTES",
        "hash_algorithm": "SHA256",
        "signature_encoding": "RAW_RSA_SIGNATURE_BYTES",
        "curve": None,
        "rsa_padding": "PSS",
        "mgf_hash": "SHA256",
        "pss_salt_length": 32,
    },
}


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V38 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(
            f"V38 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )


def build_backend_binding_preview() -> dict[str, Any]:
    """Build the exact non-executing backend/dependency selection artifact."""
    binding = {
        "binding_version": BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_v37_prep_version": v37.PREP_VERSION,
        "source_v37_request_version": v37.REQUEST_VERSION,
        "source_v37_script_blob_sha": SOURCE_V37_SCRIPT_BLOB_SHA,
        "backend_package": BACKEND_PACKAGE,
        "backend_version": BACKEND_VERSION,
        "backend_requirement": BACKEND_REQUIREMENT,
        "backend_api_family": BACKEND_API_FAMILY,
        "public_key_serialization": PUBLIC_KEY_SERIALIZATION,
        "algorithm_profiles": ALGORITHM_PROFILES,
        "dependency_declared_in_project": False,
        "dependency_imported": False,
        "cryptographic_backend_present": False,
        "dependency_artifact_hash_required": True,
        "dependency_artifact_hash_verified": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "CRYPTO_BACKEND_DEPENDENCY_BOUND_ARTIFACT_HASH_NOT_VERIFIED_NOT_INSTALLED_NOT_VERIFIED",
    }
    binding["backend_binding_sha256"] = _sha256_payload(binding)
    return binding


_BINDING_KEYS = {
    "binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_v37_prep_version", "source_v37_request_version", "source_v37_script_blob_sha",
    "backend_package", "backend_version", "backend_requirement", "backend_api_family",
    "public_key_serialization", "algorithm_profiles", "dependency_declared_in_project",
    "dependency_imported", "cryptographic_backend_present", "dependency_artifact_hash_required",
    "dependency_artifact_hash_verified", "cryptographic_verification_performed",
    "external_signature_verified", "external_verifier_identity_verified",
    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact",
    "model_qualified", "status", "backend_binding_sha256",
}


def validate_backend_binding_preview(binding: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(binding, _BINDING_KEYS, "backend binding")
    expected = build_backend_binding_preview()
    if binding != expected:
        raise PermissionError("V38 backend binding mismatch")
    return binding


def validate_algorithm_request(signature_algorithm: str, binding: dict[str, Any]) -> dict[str, Any]:
    """Return the exact bound algorithm profile; unknown/mismatched algorithms fail closed."""
    validate_backend_binding_preview(binding)
    if not isinstance(signature_algorithm, str) or signature_algorithm not in ALGORITHM_PROFILES:
        raise PermissionError("V38 unsupported signature algorithm")
    return dict(ALGORITHM_PROFILES[signature_algorithm])


def reject_any_crypto_or_live_use() -> None:
    raise PermissionError("V38 binds a future crypto backend only; verification and live/model use remain forbidden")


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_CRYPTO_BACKEND_DEPENDENCY_BINDING_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "backend_requirement": BACKEND_REQUIREMENT,
        "source_v37_script_blob_sha": SOURCE_V37_SCRIPT_BLOB_SHA,
        "dependency_declared_in_project": False,
        "dependency_imported": False,
        "cryptographic_backend_present": False,
        "dependency_artifact_hash_required": True,
        "dependency_artifact_hash_verified": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_prep_report(), ensure_ascii=False, indent=2))
