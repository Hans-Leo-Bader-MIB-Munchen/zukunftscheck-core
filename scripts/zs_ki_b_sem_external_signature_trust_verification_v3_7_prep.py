#!/usr/bin/env python3
"""V37 model-free external-signature / trust-verification preparation.

V37 binds exact signature-verification inputs and a fail-closed result envelope.
It intentionally does not ship a cryptographic backend and therefore cannot
set external_signature_verified or any authority/model authorization flag true.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any

import scripts.zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep as v36

PREP_VERSION = "v3.7-external-signature-trust-verification-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-SIGNATURE-TRUST-VERIFICATION-PREP-2026-038"
BASE_MAIN_COMMIT = "1702fe9da63386d27f6bca6be796aa1235597fc1"
REQUEST_VERSION = "ZS-KI-B-SEM-CRYPTO-VERIFICATION-REQUEST-2026-001_v0.1"
RESULT_VERSION = "ZS-KI-B-SEM-CRYPTO-VERIFICATION-RESULT-2026-001_v0.1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_B64_RE = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V37 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(f"V37 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PermissionError(f"V37 invalid {label}")
    return value


def _decode_b64(value: str, label: str, *, max_bytes: int) -> bytes:
    if not isinstance(value, str) or not value or not _B64_RE.fullmatch(value) or len(value) % 4:
        raise PermissionError(f"V37 invalid {label}")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise PermissionError(f"V37 invalid {label}") from exc
    if not decoded or len(decoded) > max_bytes:
        raise PermissionError(f"V37 invalid {label} length")
    return decoded


def _validate_v36_attestation_contract(contract: dict[str, Any], **sources: Any) -> None:
    v36.validate_attestation_verification_contract_preview(contract, **sources)


def build_crypto_verification_request_preview(*, attestation_contract: dict[str, Any],
                                              public_key_b64: str, signature_b64: str,
                                              signed_payload_b64: str, **sources: Any) -> dict[str, Any]:
    """Bind exact verification inputs without performing cryptographic verification."""
    _validate_v36_attestation_contract(attestation_contract, **sources)
    public_key = _decode_b64(public_key_b64, "public_key_b64", max_bytes=16384)
    signature = _decode_b64(signature_b64, "signature_b64", max_bytes=16384)
    signed_payload = _decode_b64(signed_payload_b64, "signed_payload_b64", max_bytes=16 * 1024 * 1024)

    public_key_sha = hashlib.sha256(public_key).hexdigest()
    signature_sha = hashlib.sha256(signature).hexdigest()
    payload_sha = hashlib.sha256(signed_payload).hexdigest()

    if public_key_sha != attestation_contract["verifier_key_fingerprint_sha256"]:
        raise PermissionError("V37 public key fingerprint mismatch")
    if payload_sha != attestation_contract["signed_payload_sha256_required"]:
        raise PermissionError("V37 signed payload hash mismatch")

    request = {
        "verification_request_version": REQUEST_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_attestation_contract_sha256": attestation_contract["attestation_contract_sha256"],
        "source_external_evidence_sha256": attestation_contract["source_external_evidence_sha256"],
        "authority_id": attestation_contract["authority_id"],
        "authority_epoch": attestation_contract["authority_epoch"],
        "verifier_id": attestation_contract["verifier_id"],
        "verifier_key_id": attestation_contract["verifier_key_id"],
        "signature_algorithm": attestation_contract["signature_algorithm"],
        "public_key_b64": public_key_b64,
        "public_key_sha256": public_key_sha,
        "signature_b64": signature_b64,
        "signature_sha256": signature_sha,
        "signed_payload_b64": signed_payload_b64,
        "signed_payload_sha256": payload_sha,
        "cryptographic_backend_required": True,
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
        "status": "CRYPTO_VERIFICATION_REQUEST_PREVIEW_INPUTS_BOUND_NOT_VERIFIED",
    }
    request["verification_request_sha256"] = _sha256_payload(request)
    return request


_REQUEST_KEYS = {
    "verification_request_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_attestation_contract_sha256", "source_external_evidence_sha256", "authority_id",
    "authority_epoch", "verifier_id", "verifier_key_id", "signature_algorithm", "public_key_b64",
    "public_key_sha256", "signature_b64", "signature_sha256", "signed_payload_b64",
    "signed_payload_sha256", "cryptographic_backend_required", "cryptographic_verification_performed",
    "external_signature_verified", "external_verifier_identity_verified", "external_authority_attested",
    "external_trust_anchor_verified", "execution_authorized", "model_run_authorized",
    "model_contact_authorized", "ready_for_model_contact", "model_qualified", "status",
    "verification_request_sha256",
}


def validate_crypto_verification_request_preview(request: dict[str, Any], *, attestation_contract: dict[str, Any],
                                                 **sources: Any) -> dict[str, Any]:
    _require_exact_keys(request, _REQUEST_KEYS, "verification request")
    expected = build_crypto_verification_request_preview(
        attestation_contract=attestation_contract,
        public_key_b64=request["public_key_b64"], signature_b64=request["signature_b64"],
        signed_payload_b64=request["signed_payload_b64"], **sources,
    )
    if request != expected:
        raise PermissionError("V37 verification request mismatch")
    return request


def build_unverified_crypto_result_preview(*, verification_request: dict[str, Any],
                                           attestation_contract: dict[str, Any], **sources: Any) -> dict[str, Any]:
    """Create a result envelope that remains unverified until a future crypto backend exists."""
    validate_crypto_verification_request_preview(
        verification_request, attestation_contract=attestation_contract, **sources
    )
    result = {
        "verification_result_version": RESULT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_verification_request_sha256": verification_request["verification_request_sha256"],
        "source_attestation_contract_sha256": attestation_contract["attestation_contract_sha256"],
        "signature_algorithm": verification_request["signature_algorithm"],
        "public_key_sha256": verification_request["public_key_sha256"],
        "signature_sha256": verification_request["signature_sha256"],
        "signed_payload_sha256": verification_request["signed_payload_sha256"],
        "cryptographic_backend_present": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "CRYPTO_VERIFICATION_RESULT_PREVIEW_NO_BACKEND_NOT_VERIFIED",
    }
    result["verification_result_sha256"] = _sha256_payload(result)
    return result


_RESULT_KEYS = {
    "verification_result_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_verification_request_sha256", "source_attestation_contract_sha256", "signature_algorithm",
    "public_key_sha256", "signature_sha256", "signed_payload_sha256", "cryptographic_backend_present",
    "cryptographic_verification_performed", "external_signature_verified",
    "external_verifier_identity_verified", "external_authority_attested", "external_trust_anchor_verified",
    "explicit_user_approval_recorded", "authorization_consumed", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified",
    "status", "verification_result_sha256",
}


def validate_unverified_crypto_result_preview(result: dict[str, Any], *, verification_request: dict[str, Any],
                                              attestation_contract: dict[str, Any], **sources: Any) -> dict[str, Any]:
    _require_exact_keys(result, _RESULT_KEYS, "verification result")
    expected = build_unverified_crypto_result_preview(
        verification_request=verification_request, attestation_contract=attestation_contract, **sources
    )
    if result != expected:
        raise PermissionError("V37 verification result mismatch")
    return result


def reject_any_live_use() -> None:
    raise PermissionError("V37 has no cryptographic backend and cannot authorize model contact or execution")


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_EXTERNAL_SIGNATURE_TRUST_VERIFICATION_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "cryptographic_backend_present": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_prep_report(), ensure_ascii=False, indent=2))
