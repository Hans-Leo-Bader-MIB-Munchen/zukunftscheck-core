#!/usr/bin/env python3
"""V28 model-free execution-gate integration preparation.

This module integrates the V27 external-secret proof concept with a persisted,
nonce-bound challenge and an atomic single-use claim primitive. It does not
contact a model, run preflight, or create an executable model authorization.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_approval_ceremony_v2_7_architecture_prep as v27
import scripts.zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep as v26

GATE_VERSION = "v2.8-execution-gate-integration-prep"
GATE_TYPE = "ZS-KI-B-SEM-EXECUTION-GATE-INTEGRATION-PREP-2026-029"
BASE_MAIN_COMMIT = "f39072022b4dd0db6e9bb2f4a63152662802b5cb"
CHALLENGE_VERSION = "ZS-KI-B-SEM-GATE-CHALLENGE-2026-001_v0.1"
APPROVAL_PROOF_VERSION = "ZS-KI-B-SEM-GATE-APPROVAL-PROOF-2026-001_v0.1"
CLAIM_VERSION = "ZS-KI-B-SEM-GATE-CLAIM-2026-001_v0.1"
NONCE_HEX_LENGTH = 64


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_nonce(nonce: str) -> str:
    if not isinstance(nonce, str) or len(nonce) != NONCE_HEX_LENGTH:
        raise PermissionError("gate nonce must be exactly 64 lowercase hex characters")
    if nonce.lower() != nonce:
        raise PermissionError("gate nonce must be lowercase hex")
    try:
        bytes.fromhex(nonce)
    except ValueError as exc:
        raise PermissionError("gate nonce must be valid hex") from exc
    return nonce


def generate_gate_nonce() -> str:
    """Generate a 256-bit nonce. The caller decides whether/where to persist it."""
    return secrets.token_hex(32)


def build_candidate_snapshot() -> dict[str, Any]:
    candidate = v26.build_authorization_candidate()
    v26.validate_authorization_candidate(candidate)
    return candidate


def _challenge_core(*, candidate: dict[str, Any], approval_secret: str, nonce: str) -> dict[str, Any]:
    v26.validate_authorization_candidate(candidate)
    _require_nonce(nonce)
    v27._require_secret(approval_secret)
    return {
        "challenge_version": CHALLENGE_VERSION,
        "gate_version": GATE_VERSION,
        "gate_type": GATE_TYPE,
        "gate_base_main_commit": BASE_MAIN_COMMIT,
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "candidate_id": candidate["authorization_candidate_id"],
        "bound_main_commit": candidate["bound_main_commit"],
        "bound_v25_runner_blob_oid": candidate["bound_v25_runner_blob_oid"],
        "model": candidate["model"],
        "required_base_url": candidate["required_base_url"],
        "max_tokens": candidate["max_tokens"],
        "prompt_sha256": candidate["prompt_sha256"],
        "response_format_sha256": candidate["response_format_sha256"],
        "qualification_snapshot_sha256": candidate["qualification_snapshot_sha256"],
        "ordered_case_ids_sha256": candidate["ordered_case_ids_sha256"],
        "gate_nonce": nonce,
        "approval_secret_commitment_sha256": v27._sha256_text(approval_secret),
    }


def build_gate_challenge_preview(
    *, candidate: dict[str, Any], approval_secret: str, nonce: str | None = None
) -> dict[str, Any]:
    """Build one non-executable challenge; no persistence is performed here."""
    chosen_nonce = generate_gate_nonce() if nonce is None else nonce
    core = _challenge_core(candidate=candidate, approval_secret=approval_secret, nonce=chosen_nonce)
    challenge = dict(core)
    challenge.update(
        {
            "challenge_id": _sha256_payload(core),
            "status": "PERSIST_BEFORE_APPROVAL_NOT_AUTHORIZED",
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "model_qualified": False,
            "authorization_consumed": False,
            "secret_stored_in_artifact": False,
            "no_execution_from_challenge": True,
        }
    )
    return challenge


def validate_gate_challenge_preview(
    *, candidate: dict[str, Any], challenge: dict[str, Any], approval_secret: str
) -> dict[str, Any]:
    if not isinstance(challenge, dict):
        raise PermissionError("gate challenge must be an object")
    nonce = challenge.get("gate_nonce")
    expected = build_gate_challenge_preview(
        candidate=candidate,
        approval_secret=approval_secret,
        nonce=_require_nonce(nonce),
    )
    if challenge != expected:
        raise PermissionError("gate challenge does not match exact candidate/secret/nonce binding")
    return challenge


def persist_gate_challenge_once(path: Path, challenge: dict[str, Any]) -> None:
    """Persist an already validated challenge with create-if-absent semantics."""
    if not isinstance(path, Path):
        raise PermissionError("challenge path must be pathlib.Path")
    if not isinstance(challenge, dict):
        raise PermissionError("gate challenge must be an object")
    payload = _canonical_bytes(challenge) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise PermissionError("gate challenge already exists") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise


def load_persisted_gate_challenge(path: Path) -> dict[str, Any]:
    if not isinstance(path, Path) or not path.is_file():
        raise PermissionError("persisted gate challenge is missing")
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError("persisted gate challenge is invalid") from exc
    if not isinstance(parsed, dict):
        raise PermissionError("persisted gate challenge must be an object")
    if raw != _canonical_bytes(parsed) + b"\n":
        raise PermissionError("persisted gate challenge must use exact canonical serialization")
    return parsed


def _approval_payload(*, candidate: dict[str, Any], challenge: dict[str, Any]) -> dict[str, Any]:
    return {
        "approval_proof_version": APPROVAL_PROOF_VERSION,
        "gate_version": GATE_VERSION,
        "challenge_id": challenge["challenge_id"],
        "gate_nonce": challenge["gate_nonce"],
        "candidate_sha256": candidate["authorization_candidate_sha256"],
        "candidate_id": candidate["authorization_candidate_id"],
        "bound_main_commit": candidate["bound_main_commit"],
        "bound_v25_runner_blob_oid": candidate["bound_v25_runner_blob_oid"],
        "model": candidate["model"],
        "required_base_url": candidate["required_base_url"],
        "max_tokens": candidate["max_tokens"],
        "prompt_sha256": candidate["prompt_sha256"],
        "response_format_sha256": candidate["response_format_sha256"],
        "qualification_snapshot_sha256": candidate["qualification_snapshot_sha256"],
        "ordered_case_ids_sha256": candidate["ordered_case_ids_sha256"],
        "approval_secret_commitment_sha256": challenge["approval_secret_commitment_sha256"],
    }


def build_gate_approval_proof_preview(
    *, candidate: dict[str, Any], persisted_challenge: dict[str, Any], approval_secret: str
) -> dict[str, Any]:
    validate_gate_challenge_preview(
        candidate=candidate,
        challenge=persisted_challenge,
        approval_secret=approval_secret,
    )
    secret = v27._require_secret(approval_secret)
    payload = _approval_payload(candidate=candidate, challenge=persisted_challenge)
    proof = hmac.new(secret, _canonical_bytes(payload), hashlib.sha256).hexdigest()
    artifact = dict(payload)
    artifact.update(
        {
            "approval_proof_hmac_sha256": proof,
            "status": "APPROVAL_PROOF_VALIDATED_ONLY_NOT_EXECUTABLE",
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "authorization_consumed": False,
            "model_qualified": False,
            "secret_stored_in_artifact": False,
            "requires_atomic_gate_claim": True,
            "no_execution_from_approval_proof": True,
        }
    )
    return artifact


def validate_gate_approval_proof_preview(
    *, candidate: dict[str, Any], persisted_challenge: dict[str, Any], artifact: dict[str, Any], approval_secret: str
) -> dict[str, Any]:
    expected = build_gate_approval_proof_preview(
        candidate=candidate,
        persisted_challenge=persisted_challenge,
        approval_secret=approval_secret,
    )
    if artifact != expected:
        raise PermissionError("approval proof artifact does not match exact gate binding")
    secret = v27._require_secret(approval_secret)
    payload = _approval_payload(candidate=candidate, challenge=persisted_challenge)
    expected_proof = hmac.new(secret, _canonical_bytes(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(artifact.get("approval_proof_hmac_sha256", "")), expected_proof):
        raise PermissionError("approval proof mismatch")
    return artifact


def claim_gate_once_preview(
    *,
    claim_path: Path,
    candidate: dict[str, Any],
    persisted_challenge: dict[str, Any],
    artifact: dict[str, Any],
    approval_secret: str,
) -> dict[str, Any]:
    """Atomically claim the validated proof once; still returns no executable authorization."""
    validate_gate_approval_proof_preview(
        candidate=candidate,
        persisted_challenge=persisted_challenge,
        artifact=artifact,
        approval_secret=approval_secret,
    )
    if not isinstance(claim_path, Path):
        raise PermissionError("claim path must be pathlib.Path")
    claim = {
        "claim_version": CLAIM_VERSION,
        "gate_version": GATE_VERSION,
        "challenge_id": persisted_challenge["challenge_id"],
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
    payload = _canonical_bytes(claim) + b"\n"
    try:
        fd = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PermissionError("gate approval proof already claimed") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            claim_path.unlink(missing_ok=True)
        finally:
            raise
    return claim


def build_gate_report() -> dict[str, Any]:
    candidate = build_candidate_snapshot()
    checks = {
        "base_main_commit_exact": BASE_MAIN_COMMIT == "f39072022b4dd0db6e9bb2f4a63152662802b5cb",
        "candidate_valid": candidate["status"] == "AWAITING_EXPLICIT_USER_APPROVAL",
        "candidate_non_executable": candidate["no_execution_from_candidate"] is True,
        "max_tokens_2048": candidate["max_tokens"] == 2048,
        "canonical_base_url_bound": candidate["required_base_url"] == v26.v25.BASE_URL,
        "canonical_response_format_bound": len(candidate["response_format_sha256"]) == 64,
        "canonical_qualification_snapshot_bound": len(candidate["qualification_snapshot_sha256"]) == 64,
        "canonical_case_order_bound": len(candidate["ordered_case_ids_sha256"]) == 64,
        "nonce_generation_available": callable(generate_gate_nonce),
        "challenge_persistence_is_explicit": callable(persist_gate_challenge_once),
        "atomic_claim_is_explicit": callable(claim_gate_once_preview),
        "no_transport_helper": "_default_transport" not in globals(),
        "no_execute_once": "execute_once" not in globals(),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_EXECUTION_GATE_INTEGRATION_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "gate_version": GATE_VERSION,
        "gate_type": GATE_TYPE,
        "base_main_commit": BASE_MAIN_COMMIT,
        "checks": checks,
        "challenge_persisted_by_report": False,
        "approval_proof_persisted_by_report": False,
        "gate_claim_persisted_by_report": False,
        "approval_secret_generated_by_report": False,
        "approval_secret_stored": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "model_qualified": False,
        "separate_run_authorization_transform_required": True,
    }


def main() -> int:
    report = build_gate_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
