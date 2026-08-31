#!/usr/bin/env python3
"""V30 model-free proof-enforcing live-gate preparation.

This module introduces the replacement validation boundary that a later live
execution path must use instead of treating V25 validation alone as sufficient.
V30 deliberately has no positive live-authorization materialization path: it
validates the complete V28/V29 provenance into a non-executable gate envelope
and fails closed on every attempt to use a bare or self-escalated V25 object.

No approval ceremony, authoritative trust anchor creation, preflight, model
contact, transport, retry, rerun, or output repair is performed here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from typing import Any
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25

GATE_VERSION = "v3.0-proof-enforcing-live-gate-prep"
GATE_TYPE = "ZS-KI-B-SEM-PROOF-ENFORCING-LIVE-GATE-PREP-2026-031"
BASE_MAIN_COMMIT = "3cae4c6251f1f931221892f14066fe7eb201e9fa"
GATE_ENVELOPE_VERSION = "ZS-KI-B-SEM-PROOF-GATE-ENVELOPE-2026-001_v0.1"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _expected_claim(*, candidate: dict[str, Any], challenge: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_version": v28.CLAIM_VERSION,
        "gate_version": v28.GATE_VERSION,
        "challenge_id": challenge["challenge_id"],
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "approval_proof_hmac_sha256": artifact["approval_proof_hmac_sha256"],
        "status": "CLAIMED_ONCE_MODEL_CONTACT_STILL_NOT_AUTHORIZED",
        "challenge_claimed": True,
        "approval_proof_validated": True,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_qualified": False,
        "ready_for_model_contact": False,
        "requires_separate_run_authorization_transform": True,
    }


def validate_full_provenance(
    *,
    candidate: dict[str, Any],
    challenge: dict[str, Any],
    artifact: dict[str, Any],
    claim: dict[str, Any],
    v29_preview: dict[str, Any],
    approval_secret: str,
) -> None:
    """Validate the complete non-live provenance chain through V29."""
    v26.validate_authorization_candidate(candidate)
    v28.validate_gate_challenge_preview(
        candidate=candidate,
        challenge=challenge,
        approval_secret=approval_secret,
    )
    v28.validate_gate_approval_proof_preview(
        candidate=candidate,
        persisted_challenge=challenge,
        artifact=artifact,
        approval_secret=approval_secret,
    )
    if claim != _expected_claim(candidate=candidate, challenge=challenge, artifact=artifact):
        raise PermissionError("V30 claim receipt mismatch")
    v29.validate_run_authorization_preview(v29_preview)
    if v29_preview.get("source_candidate_sha256") != candidate["authorization_candidate_sha256"]:
        raise PermissionError("V30 V29-preview candidate binding mismatch")
    if v29_preview.get("source_challenge_id") != challenge["challenge_id"]:
        raise PermissionError("V30 V29-preview challenge binding mismatch")
    if v29_preview.get("source_claim_version") != claim["claim_version"]:
        raise PermissionError("V30 V29-preview claim binding mismatch")
    if v29_preview.get("source_approval_proof_hmac_sha256") != artifact["approval_proof_hmac_sha256"]:
        raise PermissionError("V30 V29-preview proof binding mismatch")


def build_proof_gate_envelope_preview(
    *,
    candidate: dict[str, Any],
    challenge: dict[str, Any],
    artifact: dict[str, Any],
    claim: dict[str, Any],
    v29_preview: dict[str, Any],
    approval_secret: str,
) -> dict[str, Any]:
    """Build a non-executable envelope proving V28/V29 provenance is present."""
    validate_full_provenance(
        candidate=candidate,
        challenge=challenge,
        artifact=artifact,
        claim=claim,
        v29_preview=v29_preview,
        approval_secret=approval_secret,
    )
    proposed = deepcopy(v29_preview["proposed_v25_binding"])
    envelope = {
        "gate_envelope_version": GATE_ENVELOPE_VERSION,
        "gate_version": GATE_VERSION,
        "gate_type": GATE_TYPE,
        "gate_base_main_commit": BASE_MAIN_COMMIT,
        "source_candidate_sha256": candidate["authorization_candidate_sha256"],
        "source_challenge_id": challenge["challenge_id"],
        "source_approval_proof_hmac_sha256": artifact["approval_proof_hmac_sha256"],
        "source_claim_sha256": _sha256_payload(claim),
        "source_v29_preview_sha256": v29_preview["run_authorization_preview_sha256"],
        "proposed_v25_binding": proposed,
        "proposed_v25_binding_sha256": _sha256_payload(proposed),
        "status": "PROOF_GATE_PREVIEW_NOT_LIVE_AUTHORIZED",
        "full_provenance_validated": True,
        "authoritative_external_anchor_verified": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "requires_authoritative_trust_anchor": True,
        "requires_separate_explicit_user_approval": True,
        "requires_atomic_live_authorization_consume_before_contact": True,
        "v25_validation_alone_is_insufficient": True,
    }
    envelope["proof_gate_envelope_sha256"] = _sha256_payload(envelope)
    return envelope


def validate_proof_gate_envelope_preview(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise PermissionError("V30 proof-gate envelope must be an object")
    if envelope.get("status") != "PROOF_GATE_PREVIEW_NOT_LIVE_AUTHORIZED":
        raise PermissionError("V30 proof-gate envelope status mismatch")
    if envelope.get("gate_version") != GATE_VERSION or envelope.get("gate_type") != GATE_TYPE:
        raise PermissionError("V30 proof-gate identity mismatch")
    if envelope.get("gate_base_main_commit") != BASE_MAIN_COMMIT:
        raise PermissionError("V30 proof-gate base binding mismatch")
    if envelope.get("full_provenance_validated") is not True:
        raise PermissionError("V30 full provenance must be validated")
    for key in (
        "authoritative_external_anchor_verified",
        "explicit_user_approval_recorded",
        "live_authorization_materialized",
        "authorization_consumed",
        "execution_authorized",
        "model_run_authorized",
        "model_contact_authorized",
        "ready_for_model_contact",
        "model_qualified",
    ):
        if envelope.get(key) is not False:
            raise PermissionError(f"V30 non-live envelope illegally escalated: {key}")
    for key in (
        "requires_authoritative_trust_anchor",
        "requires_separate_explicit_user_approval",
        "requires_atomic_live_authorization_consume_before_contact",
        "v25_validation_alone_is_insufficient",
    ):
        if envelope.get(key) is not True:
            raise PermissionError(f"V30 required gate invariant missing: {key}")
    proposed = envelope.get("proposed_v25_binding")
    expected_proposed = v29._build_proposed_v25_binding()
    if proposed != expected_proposed:
        raise PermissionError("V30 proposed V25 binding mismatch")
    if envelope.get("proposed_v25_binding_sha256") != _sha256_payload(proposed):
        raise PermissionError("V30 proposed V25 binding hash mismatch")
    expected_hash = _sha256_payload({k: v for k, v in envelope.items() if k != "proof_gate_envelope_sha256"})
    if envelope.get("proof_gate_envelope_sha256") != expected_hash:
        raise PermissionError("V30 proof-gate envelope hash mismatch")
    return envelope


def validate_live_authorization_through_proof_gate(
    *,
    authorization: dict[str, Any],
    gate_envelope: dict[str, Any] | None,
) -> None:
    """Fail closed until a later block adds authoritative approval materialization.

    This is intentionally the replacement boundary for future live execution.
    A bare V25 authorization is never sufficient. In V30 even a structurally
    valid V25 authorization plus a valid non-live envelope is rejected because
    authoritative trust-anchor verification and explicit user approval do not
    yet exist.
    """
    if gate_envelope is None:
        raise PermissionError("V30 proof-enforcing gate requires provenance envelope")
    validate_proof_gate_envelope_preview(gate_envelope)
    if not isinstance(authorization, dict):
        raise PermissionError("V30 live authorization candidate must be an object")
    proposed = gate_envelope["proposed_v25_binding"]
    runtime_keys = tuple(proposed.keys())
    for key in runtime_keys:
        if key in ("status", "execution_authorized", "model_run_authorized", "model_contact_authorized"):
            continue
        if authorization.get(key) != proposed.get(key):
            raise PermissionError(f"V30 live authorization runtime binding mismatch: {key}")
    try:
        v25.validate_live_execution_authorization(deepcopy(authorization))
    except PermissionError as exc:
        raise PermissionError("V30 underlying V25 authorization is invalid") from exc
    raise PermissionError(
        "V30 live authorization remains blocked: authoritative trust anchor and separate explicit user approval are not implemented"
    )


def v30_rejects_bare_or_self_escalated_v25(authorization: dict[str, Any]) -> bool:
    try:
        validate_live_authorization_through_proof_gate(authorization=authorization, gate_envelope=None)
    except PermissionError:
        return True
    return False


def build_gate_report() -> dict[str, Any]:
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "3cae4c6251f1f931221892f14066fe7eb201e9fa",
        "v25_validation_alone_rejected_as_final_boundary": True,
        "positive_live_materialization_absent": "materialize_live_authorization" not in globals(),
        "no_transport_helper": "_default_transport" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
        "no_preflight_helper": "_default_preflight" not in globals(),
        "no_approval_action": "approve" not in globals(),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_PROOF_ENFORCING_LIVE_GATE_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "gate_version": GATE_VERSION,
        "gate_type": GATE_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "authoritative_trust_anchor_created": False,
        "explicit_user_approval_recorded": False,
        "live_authorization_materialized": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "model_qualified": False,
    }


def main() -> int:
    report = build_gate_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
