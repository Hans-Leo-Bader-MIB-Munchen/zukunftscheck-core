#!/usr/bin/env python3
"""Model-free integration of the future live synthetic qualification runner.

The module is live-capable but performs no model contact by itself. Any execution
requires an exact explicit V21 single-use authorization, an atomic V22 persistent
consumption claim before preflight, and the exact current committed V23 runner
binding. Tests must inject transports; no test needs localhost or a model.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_8_prep as v18
import scripts.zs_ki_b_sem_qualifikation_runner_v1_9_readiness_prep as v19
import scripts.zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep as v21
import scripts.zs_ki_b_sem_qualifikation_runner_v2_2_persistent_consumption_prep as v22
import scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 as integrity

RUNNER_VERSION = "v2.3-live-integration-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-3-LIVE-INTEGRATION-PREP-2026-024"
INTEGRATION_BASE_COMMIT = "3cda3b168e3fa968c0390b0e3b622f6d736f192c"
RUNNER_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_3_live_integration_prep.py"
EXPECTED_MODEL_REQUEST_COUNT = 16
BASE_URL = "http://127.0.0.1:1234/v1"
TIMEOUT_SECONDS = 1800.0
MAX_TOKENS = 1024
RETRY_COUNT = 0
OUTPUT_REPAIR = False

PreflightCallable = Callable[..., dict[str, Any]]
TransportCallable = Callable[..., tuple[str, dict[str, Any]]]


class LiveRunnerError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise LiveRunnerError(f"redirect rejected: {code} {newurl}")


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def current_git_commit() -> str:
    return _git("rev-parse", "HEAD")


def current_runner_blob_oid() -> str:
    return _git("rev-parse", f"HEAD:{RUNNER_PATH}")


def working_tree_clean() -> bool:
    return _git("status", "--porcelain") == ""


def build_live_binding() -> dict[str, Any]:
    return {
        "live_runner_version": RUNNER_VERSION,
        "live_run_type": RUN_TYPE,
        "live_runner_git_commit": current_git_commit(),
        "live_runner_blob_oid": current_runner_blob_oid(),
        "live_runner_path": RUNNER_PATH,
        "integration_base_commit": INTEGRATION_BASE_COMMIT,
    }


def build_live_authorization_template() -> dict[str, Any]:
    template = deepcopy(v21.build_authorization_template())
    template.update(build_live_binding())
    template["status"] = "NOT_AUTHORIZED_TEMPLATE"
    template["authorization_consumed"] = False
    template["execution_authorized"] = False
    template["model_run_authorized"] = False
    template["model_contact_authorized"] = False
    return template


def _live_authorization_matches(auth: dict[str, Any]) -> bool:
    if not isinstance(auth, dict):
        return False
    expected = build_live_authorization_template()
    base_expected = v21.build_authorization_template()
    base_auth = {k: auth.get(k) for k in base_expected}
    base_auth.update(
        {
            "status": auth.get("status"),
            "execution_authorized": auth.get("execution_authorized"),
            "model_run_authorized": auth.get("model_run_authorized"),
            "model_contact_authorized": auth.get("model_contact_authorized"),
            "authorization_consumed": auth.get("authorization_consumed"),
        }
    )
    try:
        v21.validate_execution_authorization(base_auth)
    except PermissionError:
        return False
    return all(
        auth.get(key) == expected[key]
        for key in (
            "live_runner_version",
            "live_run_type",
            "live_runner_git_commit",
            "live_runner_blob_oid",
            "live_runner_path",
            "integration_base_commit",
        )
    )


def validate_live_execution_authorization(auth: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(auth, dict) or not _live_authorization_matches(auth):
        raise PermissionError("V23 has no exact explicit single-use live-runner authorization")
    if not working_tree_clean():
        raise PermissionError("working tree must be clean before authorization consumption")
    if auth.get("live_runner_git_commit") != current_git_commit():
        raise PermissionError("authorized git commit no longer matches current HEAD")
    if auth.get("live_runner_blob_oid") != current_runner_blob_oid():
        raise PermissionError("authorized V23 runner blob no longer matches current HEAD")
    return auth


def _assert_request_bounds(payload: dict[str, Any]) -> None:
    if payload.get("model") != v19.EXPECTED_MODEL_ID:
        raise LiveRunnerError("runtime model binding changed")
    if payload.get("max_tokens") != MAX_TOKENS:
        raise LiveRunnerError("max_tokens binding changed")
    if payload.get("stream") is not False:
        raise LiveRunnerError("stream must remain false")


def _default_preflight(*, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    if base_url != BASE_URL:
        raise LiveRunnerError("non-loopback or unexpected base URL rejected")
    opener = urllib.request.build_opener(_NoRedirect())
    req = urllib.request.Request(f"{base_url}/models", method="GET")
    try:
        with opener.open(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, TimeoutError, OSError) as exc:
        raise LiveRunnerError(f"preflight failed: {exc}") from exc
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise LiveRunnerError("preflight response is not an object")
    return payload


def _default_transport(*, base_url: str, payload: dict[str, Any], timeout_seconds: float, case_id: str) -> tuple[str, dict[str, Any]]:
    if base_url != BASE_URL:
        raise LiveRunnerError("non-loopback or unexpected base URL rejected")
    _assert_request_bounds(payload)
    opener = urllib.request.build_opener(_NoRedirect())
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=timeout_seconds) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, TimeoutError, OSError) as exc:
        raise LiveRunnerError(f"case {case_id} transport failed: {exc}") from exc
    choices = envelope.get("choices") if isinstance(envelope, dict) else None
    if not isinstance(choices, list) or not choices:
        raise LiveRunnerError(f"case {case_id} provider envelope has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise LiveRunnerError(f"case {case_id} provider envelope has no string content")
    metadata = {k: envelope.get(k) for k in ("id", "model", "created", "usage")}
    return content, metadata


def _persist_result_once(path: Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    if not target.parent.exists():
        raise FileNotFoundError(f"result directory does not exist: {target.parent}")
    if target.exists():
        raise FileExistsError(f"result already exists; automatic rerun forbidden: {target}")
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if sys.platform == "win32":
        v22._claim_windows(target, data)
    else:
        v22._claim_posix(target, data)


def _failure_result(*, stage: str, auth: dict[str, Any], case_ids: list[str], completed: list[dict[str, Any]], exc: BaseException) -> dict[str, Any]:
    return {
        "mode": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V2_3",
        "status": "FAILED_PRESERVED_NO_RETRY",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "stage": stage,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "ordered_case_ids": case_ids,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": len(completed),
        "completed_cases": completed,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "retry_count": RETRY_COUNT,
        "output_repair": OUTPUT_REPAIR,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "model_qualified": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def execute_once(
    *,
    authorization: dict[str, Any],
    consumption_path: Path,
    result_path: Path,
    preflight: PreflightCallable | None = None,
    transport: TransportCallable | None = None,
) -> dict[str, Any]:
    """Execute exactly one authorized synthetic 16-case qualification attempt.

    Ordering is safety-critical:
    1. validate exact authorization/current committed runner;
    2. reject an already occupied result path;
    3. atomically persist consumption (authorization becomes unusable);
    4. only then perform preflight;
    5. execute the exact ordered 16 cases with no retry/repair;
    6. persist success or any caught failure once.
    """
    auth = validate_live_execution_authorization(authorization)
    result_target = Path(result_path)
    if result_target.exists():
        raise FileExistsError(f"result already exists; automatic rerun forbidden: {result_target}")

    case_ids = v21._frozen_case_ids()
    if tuple(case_ids) != integrity.EXPECTED_ORDERED_CASE_IDS or len(case_ids) != EXPECTED_MODEL_REQUEST_COUNT:
        raise PermissionError("exact ordered 16-case suite binding failed")

    v22.claim_authorization_once(Path(consumption_path), auth)
    completed: list[dict[str, Any]] = []
    preflight_fn = preflight or _default_preflight
    transport_fn = transport or _default_transport

    try:
        preflight_metadata = preflight_fn(base_url=BASE_URL, timeout_seconds=TIMEOUT_SECONDS)
    except BaseException as exc:
        failure = _failure_result(stage="PREFLIGHT_AFTER_CONSUMPTION", auth=auth, case_ids=case_ids, completed=completed, exc=exc)
        _persist_result_once(result_target, failure)
        return failure

    try:
        for case_id in case_ids:
            request = v18.build_candidate_request_preview(case_id=case_id)
            _assert_request_bounds(request)
            raw, provider_metadata = transport_fn(
                base_url=BASE_URL,
                payload=request,
                timeout_seconds=TIMEOUT_SECONDS,
                case_id=case_id,
            )
            completed.append(
                {
                    "case_id": case_id,
                    "model_response_raw": raw,
                    "provider_envelope_metadata": provider_metadata,
                }
            )
    except BaseException as exc:
        failure = _failure_result(stage="MODEL_REQUEST_AFTER_CONSUMPTION", auth=auth, case_ids=case_ids, completed=completed, exc=exc)
        _persist_result_once(result_target, failure)
        return failure

    success = {
        "mode": "EXECUTED_ONCE_AWAITING_HUMAN_REVIEW_SEM_QUALIFICATION_V2_3",
        "status": "AWAITING_HUMAN_REVIEW",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "ordered_case_ids": case_ids,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": len(completed),
        "preflight_metadata": preflight_metadata,
        "cases": completed,
        "retry_count": RETRY_COUNT,
        "output_repair": OUTPUT_REPAIR,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "human_gold_evaluation": "PENDING_HUMAN_REVIEW",
        "model_qualified": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    _persist_result_once(result_target, success)
    return success


def build_integration_report() -> dict[str, Any]:
    v22_report = v22.build_persistence_report()
    template = build_live_authorization_template()
    checks = {
        "v22_persistent_consumption_binding_pass": v22_report.get("status") == "PASS",
        "v22_not_ready_to_execute": v22_report.get("ready_to_execute") is False,
        "working_tree_clean": working_tree_clean(),
        "runner_commit_bound": len(template["live_runner_git_commit"]) == 40,
        "runner_blob_bound": len(template["live_runner_blob_oid"]) == 40,
        "exact_ordered_16_cases": tuple(template["ordered_case_ids"]) == integrity.EXPECTED_ORDERED_CASE_IDS,
        "expected_request_count_16": template["expected_model_request_count"] == EXPECTED_MODEL_REQUEST_COUNT,
        "loopback_exact": template["required_base_url"] == BASE_URL,
        "max_tokens_1024": template["max_tokens"] == MAX_TOKENS,
        "stream_false": template["stream"] is False,
        "timeout_1800": template["required_request_timeout_seconds"] == TIMEOUT_SECONDS,
        "retry_zero": template["retry_count"] == RETRY_COUNT,
        "output_repair_false": template["output_repair"] is OUTPUT_REPAIR,
        "template_not_authorized": template["status"] == "NOT_AUTHORIZED_TEMPLATE",
        "execution_not_authorized": template["execution_authorized"] is False,
        "model_contact_not_authorized": template["model_contact_authorized"] is False,
        "claim_before_preflight_defined": True,
        "failure_result_persistence_defined": True,
        "success_awaits_human_review": True,
        "automatic_retry_forbidden": True,
        "automatic_rerun_forbidden": True,
        "model_not_qualified": True,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_LIVE_RUNNER_INTEGRATION_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "checks": checks,
        "live_runner_integration_ready": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "authorization_artifact_created": False,
        "consumption_artifact_created_by_report": False,
        "result_artifact_created_by_report": False,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def main() -> int:
    report = build_integration_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
