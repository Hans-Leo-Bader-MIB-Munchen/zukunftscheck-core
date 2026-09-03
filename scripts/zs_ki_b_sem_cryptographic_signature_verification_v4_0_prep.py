#!/usr/bin/env python3
"""V40 model-free cryptographic signature verification preparation.

This module performs mathematical signature verification only for the exact
backend/version and algorithm profiles bound by V38/V39. It does not establish
external authority, trust-anchor validity, execution authorization, model
contact authorization, or model qualification.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.zs_ki_b_sem_crypto_backend_dependency_binding_v3_8_prep as v38
import scripts.zs_ki_b_sem_crypto_artifact_runtime_binding_v3_9_prep as v39

PREP_VERSION = "v4.0-cryptographic-signature-verification-prep"
PREP_TYPE = "ZS-KI-B-SEM-CRYPTOGRAPHIC-SIGNATURE-VERIFICATION-PREP-2026-001"
BASE_MAIN_COMMIT = "53bb1deaeda70466b82d666fa32e727b8c30d16d"
VERIFICATION_VERSION = "ZS-KI-B-SEM-CRYPTOGRAPHIC-SIGNATURE-VERIFICATION-2026-001_v0.1"
SOURCE_V38_SCRIPT_BLOB_SHA = "5c6ccdeeb94e086dfea48361279461c0d5cad2f8"
SOURCE_V39_SCRIPT_BLOB_SHA = "071f4d5d8ee7fa91f28a38b8cd8804be2c53b584"

BACKEND_PACKAGE = v39.BACKEND_PACKAGE
BACKEND_VERSION = v39.BACKEND_VERSION
BACKEND_REQUIREMENT = v39.BACKEND_REQUIREMENT
SUPPORTED_ALGORITHMS = frozenset(v38.ALGORITHM_PROFILES)


def _git_text_blob_sha1(path: str | Path) -> str:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V40 cannot read bound source for blob verification") from exc
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise PermissionError("V40 bound source contains non-canonical bare CR bytes")
    header = f"blob {len(canonical)}\0".encode("ascii")
    return hashlib.sha1(header + canonical).hexdigest()


def _validate_source(module: Any, expected_blob: str, label: str) -> str:
    path = getattr(module, "__file__", None)
    if not isinstance(path, str) or not path:
        raise PermissionError(f"V40 loaded {label} module has no source path")
    observed = _git_text_blob_sha1(path)
    if observed != expected_blob:
        raise PermissionError(f"V40 loaded {label} implementation blob mismatch")
    return observed


def _require_bytes(value: Any, label: str) -> bytes:
    if not isinstance(value, bytes):
        raise PermissionError(f"V40 {label} must be bytes")
    if not value:
        raise PermissionError(f"V40 {label} must not be empty")
    return value


def _load_crypto() -> dict[str, Any]:
    try:
        installed = importlib.metadata.version(BACKEND_PACKAGE)
    except importlib.metadata.PackageNotFoundError as exc:
        raise PermissionError("V40 bound cryptography dependency is not installed") from exc
    if installed != BACKEND_VERSION:
        raise PermissionError(
            f"V40 cryptography version mismatch: required={BACKEND_VERSION}, observed={installed}"
        )
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature
    except Exception as exc:
        raise PermissionError("V40 cannot import bound cryptography backend") from exc
    return {
        "InvalidSignature": InvalidSignature,
        "hashes": hashes,
        "serialization": serialization,
        "ec": ec,
        "ed25519": ed25519,
        "padding": padding,
        "rsa": rsa,
        "decode_dss_signature": decode_dss_signature,
        "encode_dss_signature": encode_dss_signature,
    }


def _load_bound_public_key(public_key_der: bytes, crypto: dict[str, Any]) -> Any:
    serialization = crypto["serialization"]
    try:
        key = serialization.load_der_public_key(public_key_der)
    except Exception as exc:
        raise PermissionError("V40 public key is not valid DER SubjectPublicKeyInfo") from exc
    try:
        canonical = key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    except Exception as exc:
        raise PermissionError("V40 cannot serialize loaded public key as DER SubjectPublicKeyInfo") from exc
    if canonical != public_key_der:
        raise PermissionError("V40 public key DER/SPKI is not canonical")
    return key


def _validate_profile(signature_algorithm: str) -> dict[str, Any]:
    if not isinstance(signature_algorithm, str) or signature_algorithm not in SUPPORTED_ALGORITHMS:
        raise PermissionError("V40 unsupported signature algorithm")
    binding = v38.build_backend_binding_preview()
    return v38.validate_algorithm_request(signature_algorithm, binding)


def verify_bound_signature(*, signature_algorithm: str, public_key_der: bytes,
                           message: bytes, signature: bytes) -> dict[str, Any]:
    """Verify one signature mathematically against the exact V38 profile.

    A successful result proves only that the supplied signature matches the
    supplied public key and message under the bound algorithm parameters.
    Authority, signer identity, trust anchors and model/execution authorization
    remain explicitly unverified/false.
    """
    _validate_source(v38, SOURCE_V38_SCRIPT_BLOB_SHA, "V38")
    _validate_source(v39, SOURCE_V39_SCRIPT_BLOB_SHA, "V39")
    profile = _validate_profile(signature_algorithm)
    public_key_der = _require_bytes(public_key_der, "public_key_der")
    message = _require_bytes(message, "message")
    signature = _require_bytes(signature, "signature")
    crypto = _load_crypto()
    key = _load_bound_public_key(public_key_der, crypto)

    InvalidSignature = crypto["InvalidSignature"]
    hashes = crypto["hashes"]
    ec = crypto["ec"]
    ed25519 = crypto["ed25519"]
    padding = crypto["padding"]
    rsa = crypto["rsa"]

    try:
        if signature_algorithm == "ED25519":
            if profile != v38.ALGORITHM_PROFILES["ED25519"]:
                raise PermissionError("V40 ED25519 profile mismatch")
            if not isinstance(key, ed25519.Ed25519PublicKey):
                raise PermissionError("V40 ED25519 public key type mismatch")
            if len(signature) != 64:
                raise PermissionError("V40 ED25519 signature must be exactly 64 bytes")
            key.verify(signature, message)

        elif signature_algorithm == "ECDSA-P256-SHA256":
            if profile != v38.ALGORITHM_PROFILES["ECDSA-P256-SHA256"]:
                raise PermissionError("V40 ECDSA profile mismatch")
            if not isinstance(key, ec.EllipticCurvePublicKey):
                raise PermissionError("V40 ECDSA public key type mismatch")
            if not isinstance(key.curve, ec.SECP256R1):
                raise PermissionError("V40 ECDSA curve must be SECP256R1")
            try:
                r, s = crypto["decode_dss_signature"](signature)
                canonical_sig = crypto["encode_dss_signature"](r, s)
            except Exception as exc:
                raise PermissionError("V40 ECDSA signature must be canonical ASN.1 DER r/s") from exc
            if canonical_sig != signature:
                raise PermissionError("V40 ECDSA signature DER is not canonical")
            key.verify(signature, message, ec.ECDSA(hashes.SHA256()))

        elif signature_algorithm == "RSA-PSS-SHA256":
            if profile != v38.ALGORITHM_PROFILES["RSA-PSS-SHA256"]:
                raise PermissionError("V40 RSA-PSS profile mismatch")
            if not isinstance(key, rsa.RSAPublicKey):
                raise PermissionError("V40 RSA public key type mismatch")
            expected_len = (key.key_size + 7) // 8
            if len(signature) != expected_len:
                raise PermissionError("V40 RSA signature length does not match public key size")
            key.verify(
                signature,
                message,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
        else:  # defensive: SUPPORTED_ALGORITHMS is already checked above
            raise PermissionError("V40 unsupported signature algorithm")
    except PermissionError:
        raise
    except InvalidSignature as exc:
        raise PermissionError("V40 cryptographic signature verification failed") from exc
    except Exception as exc:
        raise PermissionError("V40 cryptographic verification failed closed") from exc

    return {
        "verification_version": VERIFICATION_VERSION,
        "signature_algorithm": signature_algorithm,
        "backend_requirement": BACKEND_REQUIREMENT,
        "dependency_imported": True,
        "cryptographic_backend_present": True,
        "cryptographic_verification_performed": True,
        "signature_valid": True,
        "external_signature_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "CRYPTOGRAPHIC_SIGNATURE_VALID_TRUST_AND_AUTHORITY_UNVERIFIED",
    }


def build_prep_report() -> dict[str, Any]:
    v38_blob = _validate_source(v38, SOURCE_V38_SCRIPT_BLOB_SHA, "V38")
    v39_blob = _validate_source(v39, SOURCE_V39_SCRIPT_BLOB_SHA, "V39")
    return {
        "mode": "MODEL_FREE_CRYPTOGRAPHIC_SIGNATURE_VERIFICATION_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "backend_requirement": BACKEND_REQUIREMENT,
        "source_v38_script_blob_sha": v38_blob,
        "source_v39_script_blob_sha": v39_blob,
        "supported_algorithms": sorted(SUPPORTED_ALGORITHMS),
        "dependency_imported": False,
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
