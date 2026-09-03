#!/usr/bin/env python3
"""V42 model-free external trust-anchor provenance / authority-attestation prep.

V42 adds a distinct authority-root-key attestation over the verifier/trust-anchor
binding already established by V41. A successful verification proves only that
one supplied authority-root key signed the exact V41-bound signer identity and
key fingerprint under the bound algorithm profile. It does not establish the
external provenance or real-world authority of that root key.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PREP_VERSION = "v4.2-external-trust-anchor-provenance-authority-attestation-prep"
PREP_TYPE = "ZS-KI-B-SEM-EXTERNAL-TRUST-ANCHOR-PROVENANCE-AUTHORITY-ATTESTATION-PREP-2026-001"
BASE_MAIN_COMMIT = "422ca141e9c8ba42c9627e5c3928616fa33be41e"
CONTRACT_VERSION = "ZS-KI-B-SEM-AUTHORITY-KEY-ATTESTATION-CONTRACT-2026-001_v0.1"
RESULT_VERSION = "ZS-KI-B-SEM-AUTHORITY-KEY-ATTESTATION-RESULT-2026-001_v0.1"
ATTESTATION_DOMAIN = "ZS-KI-B-V42-AUTHORITY-KEY-ATTESTATION-v1"
SOURCE_V41_SCRIPT_BLOB_SHA = "a4fca4f0f97b422dcd8baa811c2a04fab38e2674"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_V41_PATH = _REPO_ROOT / "scripts" / "zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep.py"
SUPPORTED_ALGORITHMS = frozenset({"ED25519", "ECDSA-P256-SHA256", "RSA-PSS-SHA256"})


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _git_text_blob_sha1(path: str | Path) -> str:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V42 cannot read bound V41 source") from exc
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise PermissionError("V42 V41 source contains non-canonical bare CR bytes")
    return hashlib.sha1(f"blob {len(canonical)}\0".encode("ascii") + canonical).hexdigest()


def _validate_v41_source_before_import() -> str:
    observed = _git_text_blob_sha1(_V41_PATH)
    if observed != SOURCE_V41_SCRIPT_BLOB_SHA:
        raise PermissionError("V42 V41 source blob mismatch before import")
    return observed


_PREIMPORT_V41_BLOB = _validate_v41_source_before_import()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.zs_ki_b_sem_external_signature_trust_anchor_binding_v4_1_prep as v41

if v41.SUPPORTED_ALGORITHMS != SUPPORTED_ALGORITHMS:
    raise PermissionError("V42 imported V41 algorithm binding mismatch")


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V42 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(f"V42 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _require_id(value: Any, label: str) -> str:
    return v41.v34._require_id(value, f"V42 {label}")


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise PermissionError(f"V42 invalid {label}")
    return value


def _validate_v41_binding(*, v41_binding: dict[str, Any], attestation_contract: dict[str, Any],
                          authority_binding: dict[str, Any], **sources: Any) -> None:
    _validate_v41_source_before_import()
    v41.validate_direct_signer_trust_binding_preview(
        v41_binding, attestation_contract=attestation_contract,
        authority_binding=authority_binding, **sources,
    )


def _authority_attestation_payload(*, v41_binding: dict[str, Any], authority_root_key_id: str,
                                   authority_root_public_key_sha256: str,
                                   authority_signature_algorithm: str) -> dict[str, Any]:
    return {
        "domain": ATTESTATION_DOMAIN,
        "source_v41_binding_sha256": v41_binding["binding_sha256"],
        "authority_id": v41_binding["authority_id"],
        "authority_epoch": v41_binding["authority_epoch"],
        "authority_root_key_id": authority_root_key_id,
        "authority_root_public_key_sha256": authority_root_public_key_sha256,
        "authority_signature_algorithm": authority_signature_algorithm,
        "attested_verifier_id": v41_binding["verifier_id"],
        "attested_verifier_key_id": v41_binding["verifier_key_id"],
        "attested_trust_anchor_id": v41_binding["trust_anchor_id"],
        "attested_verifier_key_sha256": v41_binding["trust_anchor_public_key_sha256"],
    }


def build_authority_key_attestation_contract_preview(*, v41_binding: dict[str, Any],
                                                      attestation_contract: dict[str, Any],
                                                      authority_binding: dict[str, Any],
                                                      authority_root_key_id: str,
                                                      authority_root_public_key_sha256: str,
                                                      authority_signature_algorithm: str,
                                                      **sources: Any) -> dict[str, Any]:
    """Bind an independent authority-root key to the exact V41 signer binding."""
    _validate_v41_binding(
        v41_binding=v41_binding, attestation_contract=attestation_contract,
        authority_binding=authority_binding, **sources,
    )
    _require_id(authority_root_key_id, "authority_root_key_id")
    _require_sha256(authority_root_public_key_sha256, "authority_root_public_key_sha256")
    if authority_signature_algorithm not in SUPPORTED_ALGORITHMS:
        raise PermissionError("V42 unsupported authority signature algorithm")
    if authority_root_public_key_sha256 == v41_binding["trust_anchor_public_key_sha256"]:
        raise PermissionError("V42 authority root key must be distinct from attested verifier/trust-anchor key")

    payload = _authority_attestation_payload(
        v41_binding=v41_binding,
        authority_root_key_id=authority_root_key_id,
        authority_root_public_key_sha256=authority_root_public_key_sha256,
        authority_signature_algorithm=authority_signature_algorithm,
    )
    contract = {
        "contract_version": CONTRACT_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_v41_script_blob_sha": SOURCE_V41_SCRIPT_BLOB_SHA,
        "source_v41_binding_sha256": v41_binding["binding_sha256"],
        "source_attestation_contract_sha256": attestation_contract["attestation_contract_sha256"],
        "source_authority_binding_sha256": authority_binding["authority_binding_sha256"],
        "authority_id": v41_binding["authority_id"],
        "authority_epoch": v41_binding["authority_epoch"],
        "authority_root_key_id": authority_root_key_id,
        "authority_root_public_key_sha256": authority_root_public_key_sha256,
        "authority_signature_algorithm": authority_signature_algorithm,
        "attestation_domain": ATTESTATION_DOMAIN,
        "attestation_payload_sha256": hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
        "attested_verifier_id": v41_binding["verifier_id"],
        "attested_verifier_key_id": v41_binding["verifier_key_id"],
        "attested_trust_anchor_id": v41_binding["trust_anchor_id"],
        "attested_verifier_key_sha256": v41_binding["trust_anchor_public_key_sha256"],
        "separate_authority_root_key_required": True,
        "authority_root_external_provenance_required": True,
        "authority_key_attestation_signature_verified": False,
        "authority_root_external_provenance_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "AUTHORITY_KEY_ATTESTATION_CONTRACT_BOUND_ROOT_PROVENANCE_UNVERIFIED",
    }
    contract["contract_sha256"] = _sha256_payload(contract)
    return contract


_CONTRACT_KEYS = {
    "contract_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_v41_script_blob_sha", "source_v41_binding_sha256", "source_attestation_contract_sha256",
    "source_authority_binding_sha256", "authority_id", "authority_epoch", "authority_root_key_id",
    "authority_root_public_key_sha256", "authority_signature_algorithm", "attestation_domain",
    "attestation_payload_sha256", "attested_verifier_id", "attested_verifier_key_id",
    "attested_trust_anchor_id", "attested_verifier_key_sha256", "separate_authority_root_key_required",
    "authority_root_external_provenance_required", "authority_key_attestation_signature_verified",
    "authority_root_external_provenance_verified", "external_verifier_identity_verified",
    "external_authority_attested", "external_trust_anchor_verified", "execution_authorized",
    "model_run_authorized", "model_contact_authorized", "ready_for_model_contact", "model_qualified",
    "status", "contract_sha256",
}


def validate_authority_key_attestation_contract_preview(contract: dict[str, Any], *,
                                                        v41_binding: dict[str, Any],
                                                        attestation_contract: dict[str, Any],
                                                        authority_binding: dict[str, Any],
                                                        **sources: Any) -> dict[str, Any]:
    _require_exact_keys(contract, _CONTRACT_KEYS, "authority key attestation contract")
    expected = build_authority_key_attestation_contract_preview(
        v41_binding=v41_binding, attestation_contract=attestation_contract,
        authority_binding=authority_binding,
        authority_root_key_id=contract["authority_root_key_id"],
        authority_root_public_key_sha256=contract["authority_root_public_key_sha256"],
        authority_signature_algorithm=contract["authority_signature_algorithm"],
        **sources,
    )
    if contract != expected:
        raise PermissionError("V42 authority key attestation contract mismatch")
    return contract


def verify_authority_key_attestation_signature(*, contract: dict[str, Any],
                                               v41_binding: dict[str, Any],
                                               attestation_contract: dict[str, Any],
                                               authority_binding: dict[str, Any],
                                               authority_root_public_key_der: bytes,
                                               authority_signature: bytes,
                                               **sources: Any) -> dict[str, Any]:
    """Verify the root-key signature over the exact internally canonicalized attestation payload."""
    validate_authority_key_attestation_contract_preview(
        contract, v41_binding=v41_binding, attestation_contract=attestation_contract,
        authority_binding=authority_binding, **sources,
    )
    if not isinstance(authority_root_public_key_der, bytes) or not authority_root_public_key_der:
        raise PermissionError("V42 authority_root_public_key_der must be non-empty bytes")
    observed_root_sha = hashlib.sha256(authority_root_public_key_der).hexdigest()
    if observed_root_sha != contract["authority_root_public_key_sha256"]:
        raise PermissionError("V42 authority root public key fingerprint mismatch")

    payload = _authority_attestation_payload(
        v41_binding=v41_binding,
        authority_root_key_id=contract["authority_root_key_id"],
        authority_root_public_key_sha256=contract["authority_root_public_key_sha256"],
        authority_signature_algorithm=contract["authority_signature_algorithm"],
    )
    payload_bytes = _canonical_bytes(payload)
    if hashlib.sha256(payload_bytes).hexdigest() != contract["attestation_payload_sha256"]:
        raise PermissionError("V42 authority attestation payload hash mismatch")

    crypto_result = v41.v40.verify_bound_signature(
        signature_algorithm=contract["authority_signature_algorithm"],
        public_key_der=authority_root_public_key_der,
        message=payload_bytes,
        signature=authority_signature,
    )
    if crypto_result.get("signature_valid") is not True:
        raise PermissionError("V42 authority attestation signature invalid")

    result = {
        "result_version": RESULT_VERSION,
        "source_contract_sha256": contract["contract_sha256"],
        "source_v41_binding_sha256": v41_binding["binding_sha256"],
        "authority_id": contract["authority_id"],
        "authority_epoch": contract["authority_epoch"],
        "authority_root_key_id": contract["authority_root_key_id"],
        "authority_root_public_key_sha256_observed": observed_root_sha,
        "authority_signature_algorithm": contract["authority_signature_algorithm"],
        "attestation_payload_sha256": contract["attestation_payload_sha256"],
        "attested_verifier_id": contract["attested_verifier_id"],
        "attested_verifier_key_id": contract["attested_verifier_key_id"],
        "attested_trust_anchor_id": contract["attested_trust_anchor_id"],
        "attested_verifier_key_sha256": contract["attested_verifier_key_sha256"],
        "authority_key_attestation_signature_verified": True,
        "authority_root_key_distinct_from_verifier_key": True,
        "authority_root_external_provenance_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "AUTHORITY_KEY_ATTESTATION_SIGNATURE_VALID_ROOT_PROVENANCE_UNVERIFIED",
    }
    result["result_sha256"] = _sha256_payload(result)
    return result


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_EXTERNAL_TRUST_ANCHOR_PROVENANCE_AUTHORITY_ATTESTATION_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "source_v41_script_blob_sha": _validate_v41_source_before_import(),
        "authority_attestation_domain": ATTESTATION_DOMAIN,
        "separate_authority_root_key_required": True,
        "authority_key_attestation_signature_verified": False,
        "authority_root_external_provenance_verified": False,
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
