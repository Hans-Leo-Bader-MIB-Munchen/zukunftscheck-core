#!/usr/bin/env python3
"""V29 model-free run-authorization transformation preparation.

This module proves that an exact V28 challenge/proof/claim chain can be
transformed into a V25-bound authorization preview without creating an
executable authorization. It performs no approval ceremony, preflight, model
contact, transport, retry, rerun, or output repair.
"""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25

TRANSFORM_VERSION = "v2.9-run-authorization-transform-prep"
TRANSFORM_TYPE = "ZS-KI-B-SEM-RUN-AUTHORIZATION-TRANSFORM-PREP-2026-030"
BASE_MAIN_COMMIT = "14a21889a2ab0192bbfea364b627ca24444bf143"
TRUST_ANCHOR_VERSION = "ZS-KI-B-SEM-TRUST-ANCHOR-PREVIEW-2026-001_v0.1"
RUN_AUTH_PREVIEW_VERSION = "ZS-KI-B-SEM-RUN-AUTHORIZATION-PREVIEW-2026-001_v0.1"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def build_candidate_snapshot() -> dict[str, Any]:
    candidate = v26.build_authorization_candidate()
    v26.validate_authorization_candidate(candidate)
    return candidate


def build_trust_anchor_preview(*, candidate: dict[str, Any], challenge: dict[str, Any]) -> dict[str, Any]:
    """Build a non-authoritative preview of the future external trust anchor."""
    v26.validate_authorization_candidate(candidate)
    if not isinstance(challenge, dict):
        raise PermissionError("V29 trust-anchor preview requires a gate challenge")
    if challenge.get("candidate_sha256") != candidate["authorization_candidate_sha256"]:
        raise PermissionError("trust-anchor preview candidate mismatch")
    return {
        "trust_anchor_version": TRUST_ANCHOR_VERSION,
        "transform_version": TRANSFORM_VERSION,
        "challenge_id": challenge.get("challenge_id"),
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "approval_secret_commitment_sha256": challenge.get("approval_secret_commitment_sha256"),
        "bound_main_commit": candidate["bound_main_commit"],
        "bound_v25_runner_blob_oid": candidate["bound_v25_runner_blob_oid"],
        "status": "TRUST_ANCHOR_PREVIEW_NOT_AUTHORITATIVE",
        "authoritative_external_anchor": False,
        "explicit_user_approval_recorded": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_qualified": False,
    }


def load_canonical_json(path: Path) -> dict[str, Any]:
    if not isinstance(path, Path) or not path.is_file():
        raise PermissionError("required persisted V29 input is missing")
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError("persisted V29 input is invalid") from exc
    if not isinstance(parsed, dict):
        raise PermissionError("persisted V29 input must be an object")
    if raw != _canonical_bytes(parsed) + b"\n":
        raise PermissionError("persisted V29 input must use exact canonical serialization")
    return parsed


def validate_claim_receipt(*, candidate: dict[str, Any], challenge: dict[str, Any], artifact: dict[str, Any], claim: dict[str, Any], approval_secret: str) -> dict[str, Any]:
    """Validate the exact V28 non-executable claim receipt in memory."""
    v28.validate_gate_approval_proof_preview(
        candidate=candidate,
        persisted_challenge=challenge,
        artifact=artifact,
        approval_secret=approval_secret,
    )
    if not isinstance(claim, dict):
        raise PermissionError("V28 claim receipt must be an object")
    expected = {
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
    if claim != expected:
        raise PermissionError("V28 claim receipt does not match exact challenge/proof binding")
    return claim


def build_run_authorization_preview(*, candidate: dict[str, Any], challenge: dict[str, Any], artifact: dict[str, Any], claim: dict[str, Any], trust_anchor_preview: dict[str, Any], approval_secret: str) -> dict[str, Any]:
    """Build a V25-bound but deliberately non-executable authorization preview."""
    v26.validate_authorization_candidate(candidate)
    v28.validate_gate_challenge_preview(candidate=candidate, challenge=challenge, approval_secret=approval_secret)
    validate_claim_receipt(
        candidate=candidate,
        challenge=challenge,
        artifact=artifact,
        claim=claim,
        approval_secret=approval_secret,
    )
    expected_anchor = build_trust_anchor_preview(candidate=candidate, challenge=challenge)
    if trust_anchor_preview != expected_anchor:
        raise PermissionError("trust-anchor preview mismatch")
    if trust_anchor_preview.get("authoritative_external_anchor") is not False:
        raise PermissionError("V29 must not create an authoritative trust anchor")
    if trust_anchor_preview.get("explicit_user_approval_recorded") is not False:
        raise PermissionError("V29 must not record explicit user approval")

    template = deepcopy(v25.build_live_authorization_template())
    preview = template
    preview.update(
        {
            "run_authorization_preview_version": RUN_AUTH_PREVIEW_VERSION,
            "transform_version": TRANSFORM_VERSION,
            "transform_type": TRANSFORM_TYPE,
            "transform_base_main_commit": BASE_MAIN_COMMIT,
            "source_candidate_sha256": candidate["authorization_candidate_sha256"],
            "source_challenge_id": challenge["challenge_id"],
            "source_claim_version": claim["claim_version"],
            "source_approval_proof_hmac_sha256": artifact["approval_proof_hmac_sha256"],
            "source_trust_anchor_preview_sha256": _sha256_payload(trust_anchor_preview),
            "status": "RUN_AUTHORIZATION_PREVIEW_NOT_APPROVED",
            "authorization_consumed": False,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "model_qualified": False,
            "explicit_user_approval_recorded": False,
            "authoritative_external_anchor_verified": False,
            "single_use_claim_verified": True,
            "ready_for_model_contact": False,
            "no_execution_from_transform_preview": True,
            "separate_explicit_approval_required": True,
        }
    )
    preview["run_authorization_preview_sha256"] = _sha256_payload(preview)
    return preview


def validate_run_authorization_preview(preview: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(preview, dict):
        raise PermissionError("run authorization preview must be an object")
    if preview.get("status") != "RUN_AUTHORIZATION_PREVIEW_NOT_APPROVED":
        raise PermissionError("V29 preview status mismatch")
    if any(preview.get(key) is not False for key in ("execution_authorized", "model_run_authorized", "model_contact_authorized", "ready_for_model_contact")):
        raise PermissionError("V29 preview must not authorize execution or model contact")
    if preview.get("explicit_user_approval_recorded") is not False:
        raise PermissionError("V29 preview must not record user approval")
    if preview.get("authoritative_external_anchor_verified") is not False:
        raise PermissionError("V29 preview must not claim authoritative anchor verification")
    if preview.get("no_execution_from_transform_preview") is not True:
        raise PermissionError("V29 preview must remain non-executable")
    expected_hash = _sha256_payload({k: v for k, v in preview.items() if k != "run_authorization_preview_sha256"})
    if preview.get("run_authorization_preview_sha256") != expected_hash:
        raise PermissionError("V29 run authorization preview hash mismatch")
    return preview


def v25_rejects_transform_preview(preview: dict[str, Any]) -> bool:
    try:
        v25.validate_live_execution_authorization(deepcopy(preview))
    except PermissionError:
        return True
    return False


def build_transform_report() -> dict[str, Any]:
    candidate = build_candidate_snapshot()
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "14a21889a2ab0192bbfea364b627ca24444bf143",
        "candidate_awaiting_explicit_user_approval": candidate["status"] == "AWAITING_EXPLICIT_USER_APPROVAL",
        "candidate_non_executable": candidate["no_execution_from_candidate"] is True,
        "v25_max_tokens_2048": v25.MAX_TOKENS == 2048,
        "no_transport_helper": "_default_transport" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
        "no_preflight_helper": "_default_preflight" not in globals(),
        "no_approval_action": "approve" not in globals(),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_RUN_AUTHORIZATION_TRANSFORM_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "transform_version": TRANSFORM_VERSION,
        "transform_type": TRANSFORM_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "trust_anchor_created": False,
        "explicit_user_approval_recorded": False,
        "run_authorization_created": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "model_qualified": False,
    }


def main() -> int:
    report = build_transform_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
