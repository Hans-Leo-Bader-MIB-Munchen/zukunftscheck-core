#!/usr/bin/env python3
"""V27 model-free approval-ceremony architecture preparation.

This module does not authorize, persist, consume, execute, preflight, or contact a
model. It specifies and tests a split approval-proof design in which the secret
used to prove explicit approval is not stored in the V26 candidate or approval
artifact.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26

ARCH_VERSION = "v2.7-approval-ceremony-architecture-prep"
ARCH_TYPE = "ZS-KI-B-SEM-APPROVAL-CEREMONY-ARCHITECTURE-PREP-2026-028"
BASE_MAIN_COMMIT = "b6bd223005911f930901a4918c333dc53c66204f"
CHALLENGE_VERSION = "ZS-KI-B-SEM-APPROVAL-CHALLENGE-2026-001_v0.1"
APPROVAL_ARTIFACT_VERSION = "ZS-KI-B-SEM-APPROVAL-ARTIFACT-PREVIEW-2026-001_v0.1"
MIN_SECRET_BYTES = 32
MAX_SECRET_BYTES = 4096


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _normalize_secret_text(value: str) -> str:
    if not isinstance(value, str):
        raise PermissionError("approval secret must be text")
    return unicodedata.normalize("NFC", value)


def _sha256_text(value: str) -> str:
    normalized = _normalize_secret_text(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _require_secret(secret: str) -> bytes:
    """Validate representation bounds only; length is not an entropy guarantee."""
    normalized = _normalize_secret_text(secret)
    raw = normalized.encode("utf-8")
    if len(raw) < MIN_SECRET_BYTES:
        raise PermissionError("approval secret is too short")
    if len(raw) > MAX_SECRET_BYTES:
        raise PermissionError("approval secret is too long")
    return raw


def build_candidate_snapshot() -> dict[str, Any]:
    candidate = v26.build_authorization_candidate()
    v26.validate_authorization_candidate(candidate)
    return candidate


def build_challenge_preview(*, candidate: dict[str, Any], approval_secret: str) -> dict[str, Any]:
    """Build a non-executable challenge commitment without storing the secret."""
    v26.validate_authorization_candidate(candidate)
    _require_secret(approval_secret)
    return {
        "challenge_version": CHALLENGE_VERSION,
        "architecture_version": ARCH_VERSION,
        "architecture_type": ARCH_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "candidate_id": candidate["authorization_candidate_id"],
        "bound_main_commit": candidate["bound_main_commit"],
        "bound_v25_runner_blob_oid": candidate["bound_v25_runner_blob_oid"],
        "max_tokens": candidate["max_tokens"],
        "approval_secret_commitment_sha256": _sha256_text(approval_secret),
        "status": "CHALLENGE_PREVIEW_NOT_AUTHORIZED",
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_qualified": False,
        "secret_stored_in_artifact": False,
        "no_execution_from_challenge": True,
    }


def _approval_payload(*, candidate: dict[str, Any], challenge: dict[str, Any]) -> dict[str, Any]:
    return {
        "approval_artifact_version": APPROVAL_ARTIFACT_VERSION,
        "architecture_version": ARCH_VERSION,
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "candidate_id": candidate["authorization_candidate_id"],
        "challenge_version": challenge["challenge_version"],
        "approval_secret_commitment_sha256": challenge["approval_secret_commitment_sha256"],
        "bound_main_commit": candidate["bound_main_commit"],
        "bound_v25_runner_blob_oid": candidate["bound_v25_runner_blob_oid"],
        "max_tokens": candidate["max_tokens"],
    }


def build_approval_artifact_preview(
    *, candidate: dict[str, Any], challenge: dict[str, Any], approval_secret: str
) -> dict[str, Any]:
    """Build a non-executable proof preview; never returns or stores the secret."""
    v26.validate_authorization_candidate(candidate)
    secret = _require_secret(approval_secret)
    expected_challenge = build_challenge_preview(candidate=candidate, approval_secret=approval_secret)
    if challenge != expected_challenge:
        raise PermissionError("challenge does not match candidate and supplied secret")
    payload = _approval_payload(candidate=candidate, challenge=challenge)
    proof = hmac.new(secret, _canonical_bytes(payload), hashlib.sha256).hexdigest()
    artifact = deepcopy(payload)
    artifact.update(
        {
            "approval_proof_hmac_sha256": proof,
            "status": "EXPLICIT_USER_APPROVAL_PROOF_PREVIEW_NOT_EXECUTABLE",
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "authorization_consumed": False,
            "model_qualified": False,
            "secret_stored_in_artifact": False,
            "separate_gate_integration_required": True,
            "no_execution_from_approval_preview": True,
        }
    )
    return artifact


def validate_approval_artifact_preview(
    *, candidate: dict[str, Any], challenge: dict[str, Any], artifact: dict[str, Any], approval_secret: str
) -> dict[str, Any]:
    v26.validate_authorization_candidate(candidate)
    secret = _require_secret(approval_secret)
    expected_challenge = build_challenge_preview(candidate=candidate, approval_secret=approval_secret)
    if challenge != expected_challenge:
        raise PermissionError("challenge mismatch")
    expected = build_approval_artifact_preview(
        candidate=candidate, challenge=challenge, approval_secret=approval_secret
    )
    if artifact != expected:
        raise PermissionError("approval artifact preview does not match exact proof binding")
    payload = _approval_payload(candidate=candidate, challenge=challenge)
    expected_proof = hmac.new(secret, _canonical_bytes(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(artifact.get("approval_proof_hmac_sha256", "")), expected_proof):
        raise PermissionError("approval proof mismatch")
    if any(
        artifact.get(key) is not False
        for key in ("execution_authorized", "model_run_authorized", "model_contact_authorized")
    ):
        raise PermissionError("V27 preview must not authorize execution or model contact")
    if artifact.get("no_execution_from_approval_preview") is not True:
        raise PermissionError("V27 approval preview must remain non-executable")
    return artifact


def build_architecture_report() -> dict[str, Any]:
    candidate = build_candidate_snapshot()
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "b6bd223005911f930901a4918c333dc53c66204f",
        "candidate_awaits_explicit_user_approval": candidate["status"] == "AWAITING_EXPLICIT_USER_APPROVAL",
        "candidate_not_executable": candidate["no_execution_from_candidate"] is True,
        "max_tokens_2048": candidate["max_tokens"] == 2048,
        "approval_secret_not_present_in_candidate": "approval_secret" not in candidate,
        "architecture_has_no_execute_helper": "execute_once" not in globals(),
        "architecture_has_no_model_contact_helper": "_default_transport" not in globals(),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_APPROVAL_CEREMONY_ARCHITECTURE_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "architecture_version": ARCH_VERSION,
        "architecture_type": ARCH_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "approval_ceremony_implemented_for_execution": False,
        "approval_gate_integrated": False,
        "approval_artifact_persisted": False,
        "approval_secret_generated": False,
        "approval_secret_stored": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "model_qualified": False,
    }


def main() -> int:
    report = build_architecture_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
