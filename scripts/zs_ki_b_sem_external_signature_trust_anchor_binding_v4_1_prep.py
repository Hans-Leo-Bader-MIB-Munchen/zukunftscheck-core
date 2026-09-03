#!/usr/bin/env python3
"""V41 model-free external-signature / direct trust-anchor binding preparation.

V41 closes the self-chosen-pin gap by requiring a fully revalidated V36
attestation contract and V34 authority binding. In direct-pin mode, the V36
verifier-key fingerprint, V34 trust-anchor fingerprint, supplied DER/SPKI key,
and signed-payload hash must all agree before V40 cryptographic verification.

A successful result proves a signature is valid against that already-bound
contract chain. It still does not prove who externally established the trust
anchor, external authority control, execution authorization, or model use.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PREP_VERSION = "v4.1-external-signature-trust-anchor-binding-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-SIGNATURE-TRUST-ANCHOR-BINDING-PREP-2026-001"
BASE_MAIN_COMMIT = "a5f943a56c8e5f8532db36a642f610e1914c2f6b"
BINDING_VERSION = "ZS-KI-B-SEM-DIRECT-SIGNER-TRUST-ANCHOR-BINDING-2026-001_v0.2"
RESULT_VERSION = "ZS-KI-B-SEM-EXTERNAL-SIGNATURE-DIRECT-ANCHOR-RESULT-2026-001_v0.2"
SOURCE_V34_SCRIPT_BLOB_SHA = "02fc1ffe52b05ee46d5a7933c5b5e7e308c92cfe"
SOURCE_V35_SCRIPT_BLOB_SHA = "4e40f078585ef67b28aa55e923f5d76c05d4e93b"
SOURCE_V36_SCRIPT_BLOB_SHA = "a794a179f0d83bd1cde9823cdee535ce4ba01ccb"
SOURCE_V40_SCRIPT_BLOB_SHA = "20ac072ba529f92fc72590ef7852547f162250f1"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_PATHS = {
    "V34": (_REPO_ROOT / "scripts" / "zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep.py", SOURCE_V34_SCRIPT_BLOB_SHA),
    "V35": (_REPO_ROOT / "scripts" / "zs_ki_b_sem_external_attestation_global_single_use_v3_5_prep.py", SOURCE_V35_SCRIPT_BLOB_SHA),
    "V36": (_REPO_ROOT / "scripts" / "zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep.py", SOURCE_V36_SCRIPT_BLOB_SHA),
    "V40": (_REPO_ROOT / "scripts" / "zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep.py", SOURCE_V40_SCRIPT_BLOB_SHA),
}
SUPPORTED_ALGORITHMS = frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"})


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _git_text_blob_sha1(path: str | Path) -> str:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V41 cannot read bound predecessor source") from exc
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise PermissionError("V41 predecessor source contains non-canonical bare CR bytes")
    return hashlib.sha1(f"blob {len(canonical)}\0".encode("ascii") + canonical).hexdigest()


def _validate_sources_before_import() -> dict[str, str]:
    observed: dict[str, str] = {}
    for label, (path, expected) in _SOURCE_PATHS.items():
        actual = _git_text_blob_sha1(path)
        if actual != expected:
            raise PermissionError(f"V41 {label} source blob mismatch before import")
        observed[label] = actual
    return observed


_PREIMPORT_BLOBS = _validate_sources_before_import()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep as v34
import scripts.zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep as v36
import scripts.zs_ki_b_sem_cryptographic_signature_verification_v4_0_prep as v40

if v40.BACKEND_REQUIREMENT != "cryptography==50.0.1" or v40.SUPPORTED_ALGORITHMS != SUPPORTED_ALGORITHMS:
    raise PermissionError("V41 imported V40 binding mismatch")


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V41 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(f"V41 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _validate_contract_chain(*, attestation_contract: dict[str, Any], authority_binding: dict[str, Any],
                             **sources: Any) -> None:
    required = {
        "global_store_binding", "evidence_reference", "authority_descriptor", "store_profile",
        "authority_contract", "external_state_preview", "store_root",
    }
    if set(sources) != required:
        raise PermissionError("V41 source bundle keyset mismatch")
    v34.validate_authority_binding_preview(
        authority_binding,
        authority_descriptor=sources["authority_descriptor"], store_profile=sources["store_profile"],
        authority_contract=sources["authority_contract"], external_state_preview=sources["external_state_preview"],
        store_root=sources["store_root"],
    )
    v36.validate_attestation_verification_contract_preview(
        attestation_contract, authority_binding=authority_binding, **sources
    )
    if sources["global_store_binding"]["source_authority_binding_sha256"] != authority_binding["authority_binding_sha256"]:
        raise PermissionError("V41 global-store/authority-binding mismatch")
    if attestation_contract["source_authority_binding_sha256"] != authority_binding["authority_binding_sha256"]:
        raise PermissionError("V41 attestation/authority-binding mismatch")
    if attestation_contract["authority_id"] != authority_binding["authority_id"]:
        raise PermissionError("V41 authority id mismatch")
    if attestation_contract["authority_epoch"] != authority_binding["authority_epoch"]:
        raise PermissionError("V41 authority epoch mismatch")
    if attestation_contract["signature_algorithm"] not in SUPPORTED_ALGORITHMS:
        raise PermissionError("V41 unsupported signature algorithm")
    if attestation_contract["verifier_key_fingerprint_sha256"] != authority_binding["bound_trust_anchor_fingerprint_sha256"]:
        raise PermissionError("V41 direct-pin requires verifier key fingerprint to equal V34 trust-anchor fingerprint")


def build_direct_signer_trust_binding_preview(*, attestation_contract: dict[str, Any],
                                               authority_binding: dict[str, Any], **sources: Any) -> dict[str, Any]:
    """Bind the already-validated V36 signer contract to the V34 direct anchor."""
    _validate_sources_before_import()
    _validate_contract_chain(attestation_contract=attestation_contract, authority_binding=authority_binding, **sources)
    binding = {
        "binding_version": BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_v34_script_blob_sha": SOURCE_V34_SCRIPT_BLOB_SHA,
        "source_v35_script_blob_sha": SOURCE_V35_SCRIPT_BLOB_SHA,
        "source_v36_script_blob_sha": SOURCE_V36_SCRIPT_BLOB_SHA,
        "source_v40_script_blob_sha": SOURCE_V40_SCRIPT_BLOB_SHA,
        "source_attestation_contract_sha256": attestation_contract["attestation_contract_sha256"],
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "source_external_evidence_sha256": attestation_contract["source_external_evidence_sha256"],
        "authority_id": attestation_contract["authority_id"],
        "authority_epoch": attestation_contract["authority_epoch"],
        "verifier_id": attestation_contract["verifier_id"],
        "verifier_key_id": attestation_contract["verifier_key_id"],
        "trust_anchor_id": authority_binding["bound_trust_anchor_id"],
        "trust_anchor_mode": "V34_DIRECT_PINNED_DER_SPKI_SHA256",
        "trust_anchor_public_key_sha256": authority_binding["bound_trust_anchor_fingerprint_sha256"],
        "signed_payload_sha256_required": attestation_contract["signed_payload_sha256_required"],
        "signature_algorithm": attestation_contract["signature_algorithm"],
        "v36_attestation_contract_revalidated": True,
        "v34_authority_binding_revalidated": True,
        "verifier_key_equals_trust_anchor_pin": True,
        "pin_external_provenance_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "V36_SIGNER_BOUND_TO_V34_DIRECT_PIN_EXTERNAL_PROVENANCE_UNVERIFIED",
    }
    binding["binding_sha256"] = _sha256_payload(binding)
    return binding


_BINDING_KEYS = {
    "binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_v34_script_blob_sha", "source_v35_script_blob_sha", "source_v36_script_blob_sha",
    "source_v40_script_blob_sha", "source_attestation_contract_sha256", "source_authority_binding_sha256",
    "source_external_evidence_sha256", "authority_id", "authority_epoch", "verifier_id", "verifier_key_id",
    "trust_anchor_id", "trust_anchor_mode", "trust_anchor_public_key_sha256", "signed_payload_sha256_required",
    "signature_algorithm", "v36_attestation_contract_revalidated", "v34_authority_binding_revalidated",
    "verifier_key_equals_trust_anchor_pin", "pin_external_provenance_verified", "external_authority_attested",
    "external_trust_anchor_verified", "execution_authorized", "model_run_authorized",
    "model_contact_authorized", "ready_for_model_contact", "model_qualified", "status", "binding_sha256",
}


def validate_direct_signer_trust_binding_preview(binding: dict[str, Any], *,
                                                 attestation_contract: dict[str, Any],
                                                 authority_binding: dict[str, Any], **sources: Any) -> dict[str, Any]:
    _require_exact_keys(binding, _BINDING_KEYS, "direct signer/trust binding")
    expected = build_direct_signer_trust_binding_preview(
        attestation_contract=attestation_contract, authority_binding=authority_binding, **sources
    )
    if binding != expected:
        raise PermissionError("V41 direct signer/trust binding mismatch")
    return binding


def verify_external_signature_against_direct_anchor(*, binding: dict[str, Any],
                                                    attestation_contract: dict[str, Any],
                                                    authority_binding: dict[str, Any],
                                                    public_key_der: bytes, message: bytes,
                                                    signature: bytes, **sources: Any) -> dict[str, Any]:
    """Verify the contracted evidence signature against the V34/V36 direct pin."""
    validate_direct_signer_trust_binding_preview(
        binding, attestation_contract=attestation_contract, authority_binding=authority_binding, **sources
    )
    if not isinstance(public_key_der, bytes) or not public_key_der:
        raise PermissionError("V41 public_key_der must be non-empty bytes")
    if not isinstance(message, bytes) or not message:
        raise PermissionError("V41 message must be non-empty bytes")
    observed_key_sha = hashlib.sha256(public_key_der).hexdigest()
    if observed_key_sha != binding["trust_anchor_public_key_sha256"]:
        raise PermissionError("V41 supplied public key does not match V34/V36 direct pin")
    observed_payload_sha = hashlib.sha256(message).hexdigest()
    if observed_payload_sha != binding["signed_payload_sha256_required"]:
        raise PermissionError("V41 message does not match V36 required signed payload")

    crypto_result = v40.verify_bound_signature(
        signature_algorithm=binding["signature_algorithm"], public_key_der=public_key_der,
        message=message, signature=signature,
    )
    if crypto_result.get("signature_valid") is not True:
        raise PermissionError("V41 V40 cryptographic verification did not return valid signature")

    result = {
        "result_version": RESULT_VERSION,
        "source_binding_sha256": binding["binding_sha256"],
        "source_attestation_contract_sha256": attestation_contract["attestation_contract_sha256"],
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "authority_id": binding["authority_id"],
        "authority_epoch": binding["authority_epoch"],
        "verifier_id": binding["verifier_id"],
        "verifier_key_id": binding["verifier_key_id"],
        "trust_anchor_id": binding["trust_anchor_id"],
        "signature_algorithm": binding["signature_algorithm"],
        "public_key_sha256_observed": observed_key_sha,
        "signed_payload_sha256_observed": observed_payload_sha,
        "v36_attestation_contract_revalidated": True,
        "v34_authority_binding_revalidated": True,
        "direct_trust_anchor_pin_match_verified": True,
        "signed_payload_contract_match_verified": True,
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
        "status": "CONTRACTED_EXTERNAL_SIGNATURE_VALID_AGAINST_V34_V36_DIRECT_PIN_EXTERNAL_PROVENANCE_UNVERIFIED",
    }
    result["result_sha256"] = _sha256_payload(result)
    return result


def build_prep_report() -> dict[str, Any]:
    blobs = _validate_sources_before_import()
    return {
        "mode": "MODEL_FREE_EXTERNAL_SIGNATURE_TRUST_ANCHOR_BINDING_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "source_blobs": blobs,
        "supported_algorithms": sorted(SUPPORTED_ALGORITHMS),
        "contract_chain_binding_required": True,
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
