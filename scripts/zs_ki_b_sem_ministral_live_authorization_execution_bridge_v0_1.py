#!/usr/bin/env python3
"""Synthetic-only live authorization/execution bridge for one frozen Ministral qualification run.

Development of this module does not itself record approval or contact a model.
At runtime, the positive path requires a new exact user approval bound to the
then-current main commit. It materializes only an in-memory exact V25 live
authorization and immediately passes it to V25 execute_once(), whose first
execution-side mutation atomically consumes the authorization before preflight
or any possible model contact.

This bridge is SYNTHETIC_ONLY. It does not close residual architecture issue #130
and must not be used for real data, pilot, benchmark release, or production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_BASE_MAIN_COMMIT = "4cad196736fabd0a7baee85ba3930cec3d15a8c4"
BRIDGE_VERSION = "ZS-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001_v0.1"
BRIDGE_TYPE = "ZS-DEV-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001"
PLAN_PATH = "scripts/zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1.py"
PLAN_BLOB_SHA = "6ee75efa9949c0678b25aaa1b19fbd60d36f7493"
V25_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"
V25_BLOB_SHA = "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866"
EXPECTED_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
EXPECTED_REQUEST_COUNT = 16
EXPECTED_MAX_TOKENS = 2048
RESIDUAL_ARCHITECTURE_ISSUE = 130
APPROVAL_PREFIX = "Ich gebe exakt einen synthetischen Modelllauf für die 16 eingefrorenen Qualifikationsfälle mit `ministral-3-14b-instruct-2512` auf Basis des gesicherten Live-Authorization-/Execution-Bridges auf `main` `"
APPROVAL_SUFFIX = "` frei. Keine Retries, kein Output-Repair, kein automatischer Rerun."


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


_validate_bound_sources_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1 as plan_prep
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25


def expected_approval_text(main_commit: str) -> str:
    if not isinstance(main_commit, str) or len(main_commit) != 40 or any(c not in "0123456789abcdef" for c in main_commit):
        raise PermissionError("approval main commit must be exact lowercase 40-hex Git object id")
    return f"{APPROVAL_PREFIX}{main_commit}{APPROVAL_SUFFIX}"


def approval_text_sha256(approval_text: str) -> str:
    if not isinstance(approval_text, str):
        raise PermissionError("approval text must be text")
    return hashlib.sha256(approval_text.encode("utf-8")).hexdigest()


def _is_external_path(path: Path) -> bool:
    try:
        resolved_root = ROOT.resolve()
        resolved = path.resolve(strict=False)
        return resolved != resolved_root and resolved_root not in resolved.parents
    except (OSError, RuntimeError, ValueError):
        # Windows paths can be evaluated syntactically when tests run elsewhere.
        try:
            win_root = PureWindowsPath(str(ROOT))
            win_path = PureWindowsPath(str(path))
            return win_path.is_absolute() and win_root not in win_path.parents and win_path != win_root
        except Exception:
            return False


def _validate_runtime_boundary(*, approval_text: str, consumption_path: Path, result_path: Path) -> str:
    _validate_bound_sources_before_import()
    head = current_git_commit()
    if current_branch() != "main":
        raise PermissionError("live bridge may execute only from branch main")
    if not working_tree_clean():
        raise PermissionError("working tree must be clean before live authorization materialization")
    if approval_text != expected_approval_text(head):
        raise PermissionError("explicit user approval text does not match exact current main commit")
    if not isinstance(consumption_path, Path) or not consumption_path.is_absolute():
        raise PermissionError("consumption path must be an absolute external path")
    if not _is_external_path(consumption_path):
        raise PermissionError("consumption path must be outside repository")
    expected_name = f"zs_ki_b_sem_ministral_{head}_consumed.json"
    if consumption_path.name != expected_name:
        raise PermissionError("consumption filename must be canonical for exact approved main commit")
    if not consumption_path.parent.exists() or not consumption_path.parent.is_dir():
        raise PermissionError("external consumption directory must already exist")
    if consumption_path.exists():
        raise PermissionError("authorization already consumed or canonical receipt already exists")
    if not isinstance(result_path, Path) or not result_path.is_absolute():
        raise PermissionError("result path must be absolute")
    if not _is_external_path(result_path):
        raise PermissionError("result path must be outside repository")
    expected_result_name = f"zs_ki_b_sem_ministral_qualification_{head}_result.json"
    if result_path.name != expected_result_name:
        raise PermissionError("result filename must be canonical for exact approved main commit")
    if not result_path.parent.exists() or not result_path.parent.is_dir():
        raise PermissionError("result directory must already exist")
    if result_path.exists():
        raise PermissionError("result already exists; automatic rerun forbidden")
    return head


def _validate_frozen_plan() -> dict[str, Any]:
    plan = plan_prep.build_approval_execution_plan()
    plan_prep.validate_approval_execution_plan(plan)
    if plan["status"] != "PREPARED_NOT_AUTHORIZED":
        raise PermissionError("approval/execution plan unexpectedly authorized")
    if plan["data_class"] != "SYNTHETIC_ONLY":
        raise PermissionError("live bridge is synthetic-only")
    if plan["runtime_model_id"] != EXPECTED_MODEL_ID or plan["model_repository"] != EXPECTED_MODEL_REPOSITORY:
        raise PermissionError("frozen model binding changed")
    if plan["expected_model_request_count"] != EXPECTED_REQUEST_COUNT:
        raise PermissionError("frozen request count changed")
    if plan["max_tokens"] != EXPECTED_MAX_TOKENS or plan["retry_count"] != 0 or plan["output_repair"] is not False:
        raise PermissionError("frozen request bounds changed")
    if plan["automatic_retry_authorized"] is not False or plan["automatic_rerun_authorized"] is not False:
        raise PermissionError("automatic retry/rerun unexpectedly authorized")
    return plan


def materialize_live_authorization(*, approval_text: str, consumption_path: Path, result_path: Path) -> dict[str, Any]:
    """Materialize one exact V25 authorization in memory after all runtime gates pass.

    The returned object is not persisted by this function. The only intended
    positive use is immediate handoff to execute_approved_once(), which calls
    V25 execute_once(); V25 atomically consumes it before preflight/contact.
    """
    head = _validate_runtime_boundary(
        approval_text=approval_text,
        consumption_path=consumption_path,
        result_path=result_path,
    )
    _validate_frozen_plan()
    template = v25.build_live_authorization_template()
    if set(template) != set(v25.build_live_authorization_template()):
        raise PermissionError("V25 authorization template keyset unstable")
    if template.get("live_runner_git_commit") != head:
        raise PermissionError("V25 live runner commit does not match approved main commit")
    if template.get("live_runner_blob_oid") != V25_BLOB_SHA:
        raise PermissionError("V25 live runner blob changed")
    if template.get("max_tokens") != EXPECTED_MAX_TOKENS:
        raise PermissionError("V25 max_tokens changed")
    authorization = deepcopy(template)
    authorization.update(
        {
            "status": "EXPLICIT_USER_APPROVED",
            "authorization_consumed": False,
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        }
    )
    if set(authorization) != set(template):
        raise PermissionError("live authorization must use exact V25 keyset")
    v25.validate_live_execution_authorization(authorization)
    return authorization


def execute_approved_once(*, approval_text: str, consumption_path: Path, result_path: Path) -> dict[str, Any]:
    """Execute exactly once through V25 after exact current-main approval.

    No preflight or transport occurs in this bridge before V25 execute_once().
    V25 performs atomic authorization consumption before its preflight and before
    the first possible model contact.
    """
    authorization = materialize_live_authorization(
        approval_text=approval_text,
        consumption_path=consumption_path,
        result_path=result_path,
    )
    return v25.execute_once(
        authorization=authorization,
        consumption_path=consumption_path,
        result_path=result_path,
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
        "positive_live_materializer_present": callable(materialize_live_authorization),
        "positive_execute_bridge_present": callable(execute_approved_once),
        "new_exact_current_main_user_approval_required": True,
        "authorization_materialized_by_report": False,
        "authorization_consumed_by_report": False,
        "model_contact_performed_by_report": False,
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
    # One optional terminal newline is tolerated; internal/other whitespace is exact.
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
        approval_text=approval,
        consumption_path=Path(args.consumption_path),
        result_path=Path(args.result_path),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "AWAITING_HUMAN_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
