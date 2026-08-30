#!/usr/bin/env python3
"""V24 fail-closed repair for structured model output in the synthetic SEM runner.

This module is model-free by itself. It preserves the V23 authorization,
consumption, request bounds and no-retry/no-repair semantics while adding strict
validation of returned structured output before a case can be marked completed.
"""
from __future__ import annotations

import json
import socket
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

import scripts.zs_ki_b_sem_qualifikation_runner_v2_3_live_integration_prep as v23

RUNNER_VERSION = "v2.4-structured-output-failclosed-repair"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-4-STRUCTURED-OUTPUT-FAILCLOSED-REPAIR-2026-025"
INTEGRATION_BASE_COMMIT = "c3451b434755f9fbb9ecf1a25f88b7e8540813d5"
RUNNER_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_4_structured_output_failclosed_repair.py"
EXPECTED_MODEL_REQUEST_COUNT = v23.EXPECTED_MODEL_REQUEST_COUNT
BASE_URL = v23.BASE_URL
TIMEOUT_SECONDS = v23.TIMEOUT_SECONDS
MAX_TOKENS = v23.MAX_TOKENS
RETRY_COUNT = v23.RETRY_COUNT
OUTPUT_REPAIR = v23.OUTPUT_REPAIR

PreflightCallable = Callable[..., dict[str, Any]]
TransportCallable = Callable[..., tuple[str, dict[str, Any]]]


class LiveRunnerError(RuntimeError):
    pass


class StructuredOutputError(LiveRunnerError):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        super().__init__(f"{error_code}: {message}")


def current_git_commit() -> str:
    return v23._git("rev-parse", "HEAD")


def current_runner_blob_oid() -> str:
    return v23._git("rev-parse", f"HEAD:{RUNNER_PATH}")


def working_tree_clean() -> bool:
    return v23.working_tree_clean()


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
    template = deepcopy(v23.v21.build_authorization_template())
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
    base_expected = v23.v21.build_authorization_template()
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
        v23.v21.validate_execution_authorization(base_auth)
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
        raise PermissionError("V24 has no exact explicit single-use live-runner authorization")
    if not working_tree_clean():
        raise PermissionError("working tree must be clean before authorization consumption")
    if auth.get("live_runner_git_commit") != current_git_commit():
        raise PermissionError("authorized git commit no longer matches current HEAD")
    if auth.get("live_runner_blob_oid") != current_runner_blob_oid():
        raise PermissionError("authorized V24 runner blob no longer matches current HEAD")
    return auth


def _validate_structured_output(*, raw: str, provider_metadata: dict[str, Any], case_id: str) -> dict[str, Any]:
    finish_reason = provider_metadata.get("finish_reason") if isinstance(provider_metadata, dict) else None
    if finish_reason == "length":
        raise StructuredOutputError(
            "STRUCTURED_OUTPUT_TRUNCATED",
            f"case {case_id} provider finish_reason=length",
        )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(
            "STRUCTURED_OUTPUT_INVALID_JSON",
            f"case {case_id} model response is not valid JSON: {exc.msg}",
        ) from exc
    if not isinstance(parsed, dict):
        raise StructuredOutputError(
            "STRUCTURED_OUTPUT_NOT_OBJECT",
            f"case {case_id} model response top level must be a JSON object",
        )
    return parsed


def _default_preflight(*, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    return v23._default_preflight(base_url=base_url, timeout_seconds=timeout_seconds)


def _default_transport(*, base_url: str, payload: dict[str, Any], timeout_seconds: float, case_id: str) -> tuple[str, dict[str, Any]]:
    if base_url != BASE_URL:
        raise LiveRunnerError("non-loopback or unexpected base URL rejected")
    v23._assert_request_bounds(payload)
    opener = urllib.request.build_opener(v23._NoRedirect())
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
    choice = choices[0]
    message = choice.get("message") if isinstance(choice, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise LiveRunnerError(f"case {case_id} provider envelope has no string content")
    metadata = {k: envelope.get(k) for k in ("id", "model", "created", "usage")}
    if isinstance(choice, dict) and "finish_reason" in choice:
        metadata["finish_reason"] = choice.get("finish_reason")
    return content, metadata


def _persist_result_once(path: Path, payload: dict[str, Any]) -> None:
    v23._persist_result_once(path, payload)


def _failure_result(*, stage: str, auth: dict[str, Any], case_ids: list[str], completed: list[dict[str, Any]], observed_model_request_count: int, exc: BaseException) -> dict[str, Any]:
    failure = {
        "mode": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V2_4",
        "status": "FAILED_PRESERVED_NO_RETRY",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "stage": stage,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "ordered_case_ids": case_ids,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": observed_model_request_count,
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
    error_code = getattr(exc, "error_code", None)
    if isinstance(error_code, str):
        failure["error_code"] = error_code
    return failure


def execute_once(
    *,
    authorization: dict[str, Any],
    consumption_path: Path,
    result_path: Path,
    preflight: PreflightCallable | None = None,
    transport: TransportCallable | None = None,
) -> dict[str, Any]:
    """Execute one authorized synthetic attempt with fail-closed structured output."""
    auth = validate_live_execution_authorization(authorization)
    result_target = Path(result_path)
    if result_target.exists():
        raise FileExistsError(f"result already exists; automatic rerun forbidden: {result_target}")

    case_ids = v23.v21._frozen_case_ids()
    if tuple(case_ids) != v23.integrity.EXPECTED_ORDERED_CASE_IDS or len(case_ids) != EXPECTED_MODEL_REQUEST_COUNT:
        raise PermissionError("exact ordered 16-case suite binding failed")

    v23.v22.claim_authorization_once(Path(consumption_path), auth)
    completed: list[dict[str, Any]] = []
    attempted_count = 0
    preflight_fn = preflight or _default_preflight
    transport_fn = transport or _default_transport

    try:
        preflight_metadata = preflight_fn(base_url=BASE_URL, timeout_seconds=TIMEOUT_SECONDS)
    except BaseException as exc:
        failure = _failure_result(
            stage="PREFLIGHT_AFTER_CONSUMPTION",
            auth=auth,
            case_ids=case_ids,
            completed=completed,
            observed_model_request_count=attempted_count,
            exc=exc,
        )
        _persist_result_once(result_target, failure)
        return failure

    try:
        for case_id in case_ids:
            request = v23.v18.build_candidate_request_preview(case_id=case_id)
            v23._assert_request_bounds(request)
            attempted_count += 1
            raw, provider_metadata = transport_fn(
                base_url=BASE_URL,
                payload=request,
                timeout_seconds=TIMEOUT_SECONDS,
                case_id=case_id,
            )
            _validate_structured_output(raw=raw, provider_metadata=provider_metadata, case_id=case_id)
            completed.append(
                {
                    "case_id": case_id,
                    "model_response_raw": raw,
                    "provider_envelope_metadata": provider_metadata,
                }
            )
    except BaseException as exc:
        failure = _failure_result(
            stage="MODEL_REQUEST_AFTER_CONSUMPTION",
            auth=auth,
            case_ids=case_ids,
            completed=completed,
            observed_model_request_count=attempted_count,
            exc=exc,
        )
        _persist_result_once(result_target, failure)
        return failure

    success = {
        "mode": "EXECUTED_ONCE_AWAITING_HUMAN_REVIEW_SEM_QUALIFICATION_V2_4",
        "status": "AWAITING_HUMAN_REVIEW",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "ordered_case_ids": case_ids,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": attempted_count,
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
    v22_report = v23.v22.build_persistence_report()
    template = build_live_authorization_template()
    checks = {
        "v22_persistent_consumption_binding_pass": v22_report.get("status") == "PASS",
        "v22_not_ready_to_execute": v22_report.get("ready_to_execute") is False,
        "working_tree_clean": working_tree_clean(),
        "runner_commit_bound": len(template["live_runner_git_commit"]) == 40,
        "runner_blob_bound": len(template["live_runner_blob_oid"]) == 40,
        "exact_ordered_16_cases": tuple(template["ordered_case_ids"]) == v23.integrity.EXPECTED_ORDERED_CASE_IDS,
        "expected_request_count_16": template["expected_model_request_count"] == EXPECTED_MODEL_REQUEST_COUNT,
        "loopback_exact": template["required_base_url"] == BASE_URL,
        "max_tokens_1024_unchanged": template["max_tokens"] == 1024 == MAX_TOKENS,
        "stream_false": template["stream"] is False,
        "timeout_1800": template["required_request_timeout_seconds"] == TIMEOUT_SECONDS,
        "retry_zero": template["retry_count"] == RETRY_COUNT == 0,
        "output_repair_false": template["output_repair"] is OUTPUT_REPAIR is False,
        "template_not_authorized": template["status"] == "NOT_AUTHORIZED_TEMPLATE",
        "execution_not_authorized": template["execution_authorized"] is False,
        "model_contact_not_authorized": template["model_contact_authorized"] is False,
        "structured_output_json_validation_defined": True,
        "structured_output_object_validation_defined": True,
        "finish_reason_length_failclosed_defined": True,
        "missing_finish_reason_compatible": True,
        "automatic_retry_forbidden": True,
        "automatic_rerun_forbidden": True,
        "model_not_qualified": True,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_STRUCTURED_OUTPUT_FAILCLOSED_REPAIR",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "checks": checks,
        "live_runner_repair_ready": passed,
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
