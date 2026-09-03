#!/usr/bin/env python3
"""V41 model-free external-signature / direct trust-anchor binding preparation.

V41 binds one signer identity to one directly pinned DER/SPKI public-key SHA-256
and uses the V40 cryptographic verifier to verify a supplied signature. A PASS
proves signature validity against the pinned key and exact signer-binding data.
It does not prove who established the pin, external authority control, a
certificate chain, execution authorization, or model authorization.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

PREP_VERSION = "v4.1-external-signature-trust-anchor-binding-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-SIGNATURE-TRUST-ANCHOR-BINDING-PREP-2026-001"
BASE_MAIN_COMMIT = "a5f943a56c8e5f8532db36a642f610e1914c2f6b"
BINDING_VERSION = "ZS-KI-B-SEM-DIRECT-SIGNER-TRUST-ANCHOR-BINDING-2026-001_v0.1"
RESULT_VERSION = "ZS-KI-B-SEM-EXTERNAL-SIGNATURE-DIRECT-ANCHOR-RESULT-2026-001_v0.1"
SOURCE_V40_SCRIPT_BLOB_SHA = "20ac072ba529f92fc72590ef7852547f162250f1"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_V40_PATH = _REPO_ROOT / "scripts" / "zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep.py"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SUPPORTED_ALGORITHMS = frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"})


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _git_text_blob_sha1(path: str | Path) -> str:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V41 cannot read bound V40 source") from exc
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise PermissionError("V41 V40 source contains non-canonical bare CR bytes")
    header = f"blob {len(canonical)}\0".encode("ascii")
    return hashlib.sha1(header + canonical).hexdigest()


def _validate_v40_source_before_import() -> str:
    observed = _git_text_blob_sha1(_V40_PATH)
    if observed != SOURCE_V40_SCRIPT_BLOB_SHA:
        raise PermissionError("V41 V40 source blob mismatch before import")
    return observed


_PREIMPORT_V40_BLOB = _validate_v40_source_before_import()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep as v40

if v40.BACKEND_REQUIREMENT != "cryptography==50.0.1" or v40.SUPPORTED_ALGORITHMS != SUPPORTED_ALGORITHMS:
    raise PermissionError("V41 imported V40 binding mismatch")


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V41 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(
            f"V41 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )


def _require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise PermissionError(f"V41 invalid {label}")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PermissionError(f"V41 invalid {label}")
    return value


def build_direct_signer_trust_binding_preview(*, authority_id: str, authority_epoch: str,
                                               verifier_id: str, verifier_key_id: str,
                                               trust_anchor_id: str,
                                               trust_anchor_public_key_sha256: str,
                                               signature_algorithm: str) -> dict[str, Any]:
    """Bind signer identity and one directly pinned public-key fingerprint.

    This is a local structural pin. Its external provenance/authority is not
    established by this function.
    """
    for value, label in (
        (authority_id, "authority_id"), (authority_epoch, "authority_epoch"),
        (verifier_id, "verifier_id"), (verifier_key_id, "verifier_key_id"),
        (trust_anchor_id, "trust_anchor_id"),
    ):
        _require_id(value, label)
    _require_sha256(trust_anchor_public_key_sha256, "trust_anchor_public_key_sha256")
    if signature_algorithm not in SUPPORTED_ALGORITHMS:
        raise PermissionError("V41 unsupported signature algorithm")

    binding = {
        "binding_version": BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_v40_script_blob_sha": _validate_v40_source_before_import(),
        "source_v40_verification_version": v40.VERIFICATION_VERSION,
        "authority_id": authority_id,
        "authority_epoch": authority_epoch,
        "verifier_id": verifier_id,
        "verifier_key_id": verifier_key_id,
        "trust_anchor_id": trust_anchor_id,
        "trust_anchor_mode": "DIRECT_PINNED_DER_SPKI_SHA256",
        "trust_anchor_public_key_sha256": trust_anchor_public_key_sha256,
        "signature_algorithm": signature_algorithm,
        "signer_identity_bound": True,
        "direct_trust_anchor_pin_bound": True,
        "pin_external_provenance_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "DIRECT_SIGNER_TRUST_ANCHOR_PIN_BOUND_EXTERNAL_PROVENANCE_UNVERIFIED",
    }
    binding["binding_sha256"] = _sha256_payload(binding)
    return binding


_BINDING_KEYS = {
    "binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_v40_script_blob_sha", "source_v40_verification_version", "authority_id",
    "authority_epoch", "verifier_id", "verifier_key_id", "trust_anchor_id",
    "trust_anchor_mode", "trust_anchor_public_key_sha256", "signature_algorithm",
    "signer_identity_bound", "direct_trust_anchor_pin_bound", "pin_external_provenance_verified",
    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact",
    "model_qualified", "status", "binding_sha256",
}


def validate_direct_signer_trust_binding_preview(binding: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(binding, _BINDING_KEYS, "direct signer/trust binding")
    expected = build_direct_signer_trust_binding_preview(
        authority_id=binding["authority_id"], authority_epoch=binding["authority_epoch"],
        verifier_id=binding["verifier_id"], verifier_key_id=binding["verifier_key_id"],
        trust_anchor_id=binding["trust_anchor_id"],
        trust_anchor_public_key_sha256=binding["trust_anchor_public_key_sha256"],
        signature_algorithm=binding["signature_algorithm"],
    )
    if binding != expected:
        raise PermissionError("V41 direct signer/trust binding mismatch")
    return binding


def verify_external_signature_against_direct_anchor(*, binding: dict[str, Any],
                                                    public_key_der: bytes, message: bytes,
                                                    signature: bytes) -> dict[str, Any]:
    """Verify signature and exact public-key pin without escalating external trust."""
    validate_direct_signer_trust_binding_preview(binding)
    if not isinstance(public_key_der, bytes) or not public_key_der:
        raise PermissionError("V41 public_key_der must be non-empty bytes")
    observed_key_sha = hashlib.sha256(public_key_der).hexdigest()
    if observed_key_sha != binding["trust_anchor_public_key_sha256"]:
        raise PermissionError("V41 supplied public key does not match direct trust-anchor pin")

    crypto_result = v40.verify_bound_signature(
        signature_algorithm=binding["signature_algorithm"],
        public_key_der=public_key_der,
        message=message,
        signature=signature,
    )
    if crypto_result.get("signature_valid") is not True:
        raise PermissionError("V41 V40 cryptographic verification did not return valid signature")

    result = {
        "result_version": RESULT_VERSION,
        "source_binding_sha256": binding["binding_sha256"],
        "source_v40_verification_version": crypto_result["verification_version"],
        "authority_id": binding["authority_id"],
        "authority_epoch": binding["authority_epoch"],
        "verifier_id": binding["verifier_id"],
        "verifier_key_id": binding["verifier_key_id"],
        "trust_anchor_id": binding["trust_anchor_id"],
        "signature_algorithm": binding["signature_algorithm"],
        "public_key_sha256_observed": observed_key_sha,
        "direct_trust_anchor_pin_match_verified": True,
        "signer_identity_binding_verified": True,
        "cryptographic_verification_performed": True,
        "external_signature_verified": True,
        "pin_external_provenance_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "EXTERNAL_SIGNATURE_VALID_AGAINST_DIRECT_PIN_EXTERNAL_PROVENANCE_UNVERIFIED",
    }
    result["result_sha256"] = _sha256_payload(result)
    return result


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_EXTERNAL_SIGNATURE_TRUST_ANCHOR_BINDING_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "source_v40_script_blob_sha": _validate_v40_source_before_import(),
        "supported_algorithms": sorted(SUPPORTED_ALGORITHMS),
        "direct_trust_anchor_binding_available": True,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "pin_external_provenance_verified": False,
        "external_verifier_identity_verified": False,
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
