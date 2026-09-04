#!/usr/bin/env python3
"""Synthetic-only live authorization/execution bridge for one frozen Ministral qualification run.

Development/reporting is model-free. A positive runtime path requires a new exact
user approval bound to the then-current main commit, builds and atomically claims
the V28 proof chain, validates V29/V30 provenance, then materializes one exact
V25 authorization in memory and immediately hands it to V25 execute_once(). V25
atomically consumes that authorization before preflight or model contact.

This bridge is SYNTHETIC_ONLY. It does not establish external authority or close
residual architecture issue #130 and must not be used for real data, pilot,
benchmark release, or production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_BASE_MAIN_COMMIT = "4cad196736fabd0a7baee85ba3930cec3d15a8c4"
BRIDGE_VERSION = "ZS-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001_v0.3"
BRIDGE_TYPE = "ZS-DEV-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001"
PLAN_PATH = "scripts/zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1.py"
PLAN_BLOB_SHA = "6ee75efa9949c0678b25aaa1b19fbd60d36f7493"
V25_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"
V25_BLOB_SHA = "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866"
PROVENANCE_SOURCE_PATHS = (
    "scripts/zs_ki_b_sem_approval_ceremony_v2_7_architecture_prep.py",
    "scripts/zs_ki_b_sem_execution_gate_v2_8_integration_prep.py",
    "scripts/zs_ki_b_sem_run_authorization_v2_9_transform_prep.py",
    "scripts/zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep.py",
)
EXPECTED_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
EXPECTED_REQUEST_COUNT = 16
EXPECTED_MAX_TOKENS = 2048
RESIDUAL_ARCHITECTURE_ISSUE = 130
APPROVAL_PREFIX = "Ich gebe exakt einen synthetischen Modelllauf für die 16 eingefrorenen Qualifikationsfälle mit `ministral-3-14b-instruct-2512` auf Basis des gesicherten Live-Authorization-/Execution-Bridges auf `main` `"
APPROVAL_SUFFIX = "` frei. Keine Retries, kein Output-Repair, kein automatischer Rerun."
SECRET_DOMAIN = "ZS-KI-B-MINISTRAL-LIVE-BRIDGE-APPROVAL-SECRET-v1"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("ascii").strip()


def current_git_commit() -> str:
    return _git("rev-parse", "HEAD")


def current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD")


def working_tree_clean() -> bool:
    return _git("status", "--porcelain") == ""


def _blob_at(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _text_blob_sha1(path: Path) -> str:
    try:
        data = path.read_bytes().replace(b"\r\n", b"\n")
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError(f"cannot read bridge source binding: {path}") from exc
    if b"\r" in data:
        raise PermissionError(f"bare CR in bridge source binding: {path}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _validate_bound_sources_before_import() -> None:
    for path, expected, label in (
        (PLAN_PATH, PLAN_BLOB_SHA, "approval/execution plan"),
        (V25_PATH, V25_BLOB_SHA, "V25 live runner"),
    ):
        if _blob_at(BRIDGE_BASE_MAIN_COMMIT, path) != expected:
            raise PermissionError(f"bound base {label} blob changed")
        if _text_blob_sha1(ROOT / path) != expected:
            raise PermissionError(f"worktree {label} blob changed before import")
    for path in PROVENANCE_SOURCE_PATHS:
        expected = _blob_at(BRIDGE_BASE_MAIN_COMMIT, path)
        if not isinstance(expected, str) or len(expected) != 40:
            raise PermissionError(f"invalid bound provenance source blob: {path}")
        if _text_blob_sha1(ROOT / path) != expected:
            raise PermissionError(f"worktree provenance source changed before import: {path}")


_validate_bound_sources_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1 as plan_prep
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25
import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30


def expected_approval_text(main_commit: str) -> str:
    if not isinstance(main_commit, str) or len(main_commit) != 40 or any(c not in "0123456789abcdef" for c in main_commit):
        raise PermissionError("approval main commit must be exact lowercase 40-hex Git object id")
    return f"{APPROVAL_PREFIX}{main_commit}{APPROVAL_SUFFIX}"


def approval_text_sha256(approval_text: str) -> str:
    if not isinstance(approval_text, str):
        raise PermissionError("approval text must be text")
    return hashlib.sha256(approval_text.encode("utf-8")).hexdigest()


def _approval_secret(approval_text: str, head: str) -> str:
    if approval_text != expected_approval_text(head):
        raise PermissionError("cannot derive proof secret from non-exact approval")
    # 64 lowercase hex chars = 64 UTF-8 bytes; V27 representation bounds are satisfied.
    return hashlib.sha256(f"{SECRET_DOMAIN}\n{head}\n{approval_text}".encode("utf-8")).hexdigest()


def _is_external_path(path: Path) -> bool:
    try:
        resolved_root = ROOT.resolve()
        resolved = path.resolve(strict=False)
        return resolved != resolved_root and resolved_root not in resolved.parents
    except (OSError, RuntimeError, ValueError):
        try:
            win_root = PureWindowsPath(str(ROOT))
            win_path = PureWindowsPath(str(path))
            return win_path.is_absolute() and win_root not in win_path.parents and win_path != win_root
        except Exception:
            return False


def _canonical_paths(root: Path, head: str) -> dict[str, Path]:
    return {
        "challenge": root / f"zs_ki_b_sem_ministral_{head}_gate_challenge.json",
        "proof_claim": root / f"zs_ki_b_sem_ministral_{head}_proof_claim.json",
        "consumption": root / f"zs_ki_b_sem_ministral_{head}_consumed.json",
        "result": root / f"zs_ki_b_sem_ministral_qualification_{head}_result.json",
    }


def _validate_runtime_boundary(*, approval_text: str, consumption_path: Path, result_path: Path) -> tuple[str, dict[str, Path]]:
    _validate_bound_sources_before_import()
    head = current_git_commit()
    if current_branch() != "main":
        raise PermissionError("live bridge may execute only from branch main")
    if not working_tree_clean():
        raise PermissionError("working tree must be clean before live authorization materialization")
    if approval_text != expected_approval_text(head):
        raise PermissionError("explicit user approval text does not match exact current main commit")
    for label, path in (("consumption", consumption_path), ("result", result_path)):
        if not isinstance(path, Path) or not path.is_absolute() or not _is_external_path(path):
            raise PermissionError(f"{label} path must be absolute and outside repository")
        if not path.parent.exists() or not path.parent.is_dir():
            raise PermissionError(f"{label} directory must already exist")
    if consumption_path.parent != result_path.parent:
        raise PermissionError("all live bridge state must use one external run-state directory")
    paths = _canonical_paths(consumption_path.parent, head)
    if consumption_path != paths["consumption"]:
        raise PermissionError("consumption filename must be canonical for exact approved main commit")
    if result_path != paths["result"]:
        raise PermissionError("result filename must be canonical for exact approved main commit")
    for label, path in paths.items():
        if path.exists():
            raise PermissionError(f"canonical {label} state already exists; replay/rerun rejected")
    return head, paths


def _validate_frozen_plan() -> dict[str, Any]:
    _validate_bound_sources_before_import()
    plan = plan_prep.build_approval_execution_plan()
    plan_prep.validate_approval_execution_plan(plan)
    if plan["status"] != "PREPARED_NOT_AUTHORIZED" or plan["data_class"] != "SYNTHETIC_ONLY":
        raise PermissionError("approval/execution plan boundary changed")
    if plan["runtime_model_id"] != EXPECTED_MODEL_ID or plan["model_repository"] != EXPECTED_MODEL_REPOSITORY:
        raise PermissionError("frozen model binding changed")
    if plan["expected_model_request_count"] != EXPECTED_REQUEST_COUNT:
        raise PermissionError("frozen request count changed")
    if plan["max_tokens"] != EXPECTED_MAX_TOKENS or plan["retry_count"] != 0 or plan["output_repair"] is not False:
        raise PermissionError("frozen request bounds changed")
    if plan["automatic_retry_authorized"] is not False or plan["automatic_rerun_authorized"] is not False:
        raise PermissionError("automatic retry/rerun unexpectedly authorized")
    return plan


def _build_and_claim_proof_chain(*, approval_text: str, head: str, paths: dict[str, Path]) -> dict[str, Any]:
    """Persist and atomically claim the V28 proof, then validate V29/V30 provenance."""
    secret = _approval_secret(approval_text, head)
    candidate = v28.build_candidate_snapshot()
    nonce = v28.generate_gate_nonce()
    challenge = v28.build_gate_challenge_preview(candidate=candidate, approval_secret=secret, nonce=nonce)
    v28.validate_gate_challenge_preview(candidate=candidate, challenge=challenge, approval_secret=secret)
    v28.persist_gate_challenge_once(paths["challenge"], challenge)
    persisted = v28.load_persisted_gate_challenge(paths["challenge"])
    v28.validate_gate_challenge_preview(candidate=candidate, challenge=persisted, approval_secret=secret)
    artifact = v28.build_gate_approval_proof_preview(candidate=candidate, persisted_challenge=persisted, approval_secret=secret)
    v28.validate_gate_approval_proof_preview(candidate=candidate, persisted_challenge=persisted, artifact=artifact, approval_secret=secret)
    claim = v28.claim_gate_once_preview(
        claim_path=paths["proof_claim"], candidate=candidate, persisted_challenge=persisted,
        artifact=artifact, approval_secret=secret,
    )
    trust_anchor_preview = v29.build_trust_anchor_preview(candidate=candidate, challenge=persisted)
    transform = v29.build_run_authorization_preview(
        candidate=candidate, challenge=persisted, artifact=artifact, claim=claim,
        trust_anchor_preview=trust_anchor_preview, approval_secret=secret,
    )
    v29.validate_run_authorization_preview(transform)
    envelope = v30.build_proof_gate_envelope_preview(
        candidate=candidate, challenge=persisted, artifact=artifact, claim=claim,
        v29_preview=transform, approval_secret=secret,
    )
    v30.validate_proof_gate_envelope_preview(envelope)
    if envelope["full_provenance_validated"] is not True:
        raise PermissionError("V30 full provenance was not validated")
    if envelope["proposed_v25_binding"] != v25.build_live_authorization_template():
        raise PermissionError("V30 proposed V25 binding differs from current exact V25 template")
    return {
        "challenge": persisted,
        "artifact": artifact,
        "claim": claim,
        "transform": transform,
        "envelope": envelope,
    }


def materialize_live_authorization(*, approval_text: str, consumption_path: Path, result_path: Path) -> dict[str, Any]:
    """Build V28-V30 proof chain, then materialize one exact V25 authorization in memory."""
    head, paths = _validate_runtime_boundary(
        approval_text=approval_text, consumption_path=consumption_path, result_path=result_path
    )
    _validate_frozen_plan()
    proof = _build_and_claim_proof_chain(approval_text=approval_text, head=head, paths=paths)
    template = deepcopy(proof["envelope"]["proposed_v25_binding"])
    if template != v25.build_live_authorization_template():
        raise PermissionError("proof-bound V25 template changed after provenance validation")
    if template.get("live_runner_git_commit") != head or template.get("live_runner_blob_oid") != V25_BLOB_SHA:
        raise PermissionError("V25 live runner binding differs from exact approved main")
    if template.get("max_tokens") != EXPECTED_MAX_TOKENS:
        raise PermissionError("V25 max_tokens changed")
    authorization = deepcopy(template)
    authorization.update({
        "status": "EXPLICIT_USER_APPROVED",
        "authorization_consumed": False,
        "execution_authorized": True,
        "model_run_authorized": True,
        "model_contact_authorized": True,
    })
    if set(authorization) != set(template):
        raise PermissionError("live authorization must use exact V25 keyset")
    v25.validate_live_execution_authorization(authorization)
    return authorization


def execute_approved_once(*, approval_text: str, consumption_path: Path, result_path: Path) -> dict[str, Any]:
    """Execute exactly once through V28-V30 provenance and V25 atomic consume."""
    authorization = materialize_live_authorization(
        approval_text=approval_text, consumption_path=consumption_path, result_path=result_path
    )
    return v25.execute_once(
        authorization=authorization, consumption_path=consumption_path, result_path=result_path
    )


def build_bridge_report() -> dict[str, Any]:
    plan = _validate_frozen_plan()
    return {
        "mode": "MODEL_FREE_MINISTRAL_LIVE_AUTHORIZATION_EXECUTION_BRIDGE_PREP",
        "status": "PASS",
        "bridge_version": BRIDGE_VERSION,
        "bridge_type": BRIDGE_TYPE,
        "bridge_base_main_commit": BRIDGE_BASE_MAIN_COMMIT,
        "runtime_model_id": EXPECTED_MODEL_ID,
        "model_repository": EXPECTED_MODEL_REPOSITORY,
        "data_class": "SYNTHETIC_ONLY",
        "expected_model_request_count": EXPECTED_REQUEST_COUNT,
        "max_tokens": EXPECTED_MAX_TOKENS,
        "retry_count": 0,
        "output_repair": False,
        "bound_plan_sha256": plan["approval_execution_plan_sha256"],
        "bound_plan_blob_sha": PLAN_BLOB_SHA,
        "bound_v25_blob_sha": V25_BLOB_SHA,
        "v28_v29_v30_provenance_required_before_materialization": True,
        "proof_claim_required_before_materialization": True,
        "v25_atomic_consume_required_before_model_contact": True,
        "positive_live_materializer_present": callable(materialize_live_authorization),
        "positive_execute_bridge_present": callable(execute_approved_once),
        "new_exact_current_main_user_approval_required": True,
        "authorization_materialized_by_report": False,
        "authorization_consumed_by_report": False,
        "model_contact_performed_by_report": False,
        "external_authority_claimed": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_qualified": False,
        "real_data": False,
        "pilot_approved": False,
        "production_approved": False,
        "residual_architecture_issue": RESIDUAL_ARCHITECTURE_ISSUE,
    }


def _read_approval_file(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PermissionError("cannot read approval file") from exc
    if raw.endswith("\r\n"):
        raw = raw[:-2]
    elif raw.endswith("\n"):
        raw = raw[:-1]
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--approval-file")
    parser.add_argument("--consumption-path")
    parser.add_argument("--result-path")
    args = parser.parse_args(argv)
    if args.report:
        print(json.dumps(build_bridge_report(), ensure_ascii=False, indent=2))
        return 0
    if not (args.approval_file and args.consumption_path and args.result_path):
        parser.error("execution requires --approval-file, --consumption-path and --result-path")
    approval = _read_approval_file(Path(args.approval_file))
    result = execute_approved_once(
        approval_text=approval, consumption_path=Path(args.consumption_path), result_path=Path(args.result_path)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "AWAITING_HUMAN_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
