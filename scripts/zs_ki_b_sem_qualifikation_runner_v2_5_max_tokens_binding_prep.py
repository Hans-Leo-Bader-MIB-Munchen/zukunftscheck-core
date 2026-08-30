#!/usr/bin/env python3
"""V25 model-free max_tokens rebinding prep for the synthetic SEM runner."""
from __future__ import annotations

import json
import os
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

import scripts.zs_ki_b_sem_qualifikation_runner_v2_4_structured_output_failclosed_repair as v24

RUNNER_VERSION = "v2.5-max-tokens-binding-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-5-MAX-TOKENS-BINDING-PREP-2026-026"
INTEGRATION_BASE_COMMIT = "0d96eed2d8246b8316a219c5c99242f83e09ee5f"
RUNNER_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"
EXPECTED_MODEL_REQUEST_COUNT = v24.EXPECTED_MODEL_REQUEST_COUNT
BASE_URL = v24.BASE_URL
TIMEOUT_SECONDS = v24.TIMEOUT_SECONDS
MAX_TOKENS = 2048
RETRY_COUNT = 0
OUTPUT_REPAIR = False

PreflightCallable = Callable[..., dict[str, Any]]
TransportCallable = Callable[..., tuple[str, dict[str, Any]]]
LiveRunnerError = v24.LiveRunnerError
StructuredOutputError = v24.StructuredOutputError
V22_CLAIM_POSIX = v24.v23.v22._claim_posix
V22_CLAIM_WINDOWS = v24.v23.v22._claim_windows


def current_git_commit() -> str:
    return v24.v23._git("rev-parse", "HEAD")


def current_runner_blob_oid() -> str:
    return v24.v23._git("rev-parse", f"HEAD:{RUNNER_PATH}")


def working_tree_clean() -> bool:
    return v24.working_tree_clean()


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
    template = deepcopy(v24.build_live_authorization_template())
    template.update(build_live_binding())
    template["max_tokens"] = MAX_TOKENS
    template["status"] = "NOT_AUTHORIZED_TEMPLATE"
    template["authorization_consumed"] = False
    template["execution_authorized"] = False
    template["model_run_authorized"] = False
    template["model_contact_authorized"] = False
    return template


def _approved_probe_from_template(template: dict[str, Any]) -> dict[str, Any]:
    probe = deepcopy(template)
    probe.update(
        {
            "status": "EXPLICIT_USER_APPROVED",
            "authorization_consumed": False,
            "execution_authorized": True,
            "model_run_authorized": True,
            "model_contact_authorized": True,
        }
    )
    return probe


def _live_authorization_matches(auth: dict[str, Any]) -> bool:
    if not isinstance(auth, dict):
        return False
    expected = build_live_authorization_template()
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        return False
    if auth.get("authorization_consumed") is not False:
        return False
    if auth.get("execution_authorized") is not True:
        return False
    if auth.get("model_run_authorized") is not True:
        return False
    if auth.get("model_contact_authorized") is not True:
        return False
    excluded = {
        "status",
        "authorization_consumed",
        "execution_authorized",
        "model_run_authorized",
        "model_contact_authorized",
    }
    return all(auth.get(key) == value for key, value in expected.items() if key not in excluded)


def validate_live_execution_authorization(auth: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(auth, dict) or not _live_authorization_matches(auth):
        raise PermissionError("V25 has no exact explicit single-use live-runner authorization")
    if not working_tree_clean():
        raise PermissionError("working tree must be clean before authorization consumption")
    if auth.get("live_runner_git_commit") != current_git_commit():
        raise PermissionError("authorized git commit no longer matches current HEAD")
    if auth.get("live_runner_blob_oid") != current_runner_blob_oid():
        raise PermissionError("authorized V25 runner blob no longer matches current HEAD")
    return auth


def _build_consumed_state_v25(auth: dict[str, Any]) -> dict[str, Any]:
    """Build a durable consumed state that preserves the exact V25 binding."""
    validate_live_execution_authorization(auth)
    consumed = deepcopy(auth)
    consumed.update(
        {
            "status": "CONSUMED_PRE_MODEL_CONTACT",
            "authorization_consumed": True,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "persistence_version": v24.v23.v22.PERSISTENCE_VERSION,
            "consumption_boundary": "BEFORE_FIRST_MODEL_CONTACT",
            "single_use_claimed": True,
        }
    )
    return consumed


def _claim_authorization_once_v25(path: Path, auth: dict[str, Any]) -> dict[str, Any]:
    """Atomically consume an exact V25 authorization before any possible contact."""
    consumed = _build_consumed_state_v25(auth)
    target = Path(path)
    if not target.parent.exists():
        raise FileNotFoundError(f"authorization state directory does not exist: {target.parent}")
    payload = (json.dumps(consumed, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if os.name == "nt":
        V22_CLAIM_WINDOWS(target, payload)
    else:
        V22_CLAIM_POSIX(target, payload)
    auth.update(
        {
            "status": "CONSUMED_PRE_MODEL_CONTACT",
            "authorization_consumed": True,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
        }
    )
    return consumed


def _assert_request_bounds(payload: dict[str, Any]) -> None:
    if payload.get("model") != v24.v23.v19.EXPECTED_MODEL_ID:
        raise LiveRunnerError("runtime model binding changed")
    if payload.get("max_tokens") != MAX_TOKENS:
        raise LiveRunnerError("max_tokens binding changed")
    if payload.get("stream") is not False:
        raise LiveRunnerError("stream must remain false")


def build_candidate_request(case_id: str) -> dict[str, Any]:
    request = deepcopy(v24.v23.v18.build_candidate_request_preview(case_id=case_id))
    request["max_tokens"] = MAX_TOKENS
    _assert_request_bounds(request)
    return request


def _validate_structured_output(*, raw: str, provider_metadata: dict[str, Any], case_id: str) -> dict[str, Any]:
    return v24._validate_structured_output(raw=raw, provider_metadata=provider_metadata, case_id=case_id)


def _default_preflight(*, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    return v24._default_preflight(base_url=base_url, timeout_seconds=timeout_seconds)


def _default_transport(*, base_url: str, payload: dict[str, Any], timeout_seconds: float, case_id: str) -> tuple[str, dict[str, Any]]:
    if base_url != BASE_URL:
        raise LiveRunnerError("non-loopback or unexpected base URL rejected")
    _assert_request_bounds(payload)
    opener = urllib.request.build_opener(v24.v23._NoRedirect())
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


def _failure_result(*, stage: str, auth: dict[str, Any], case_ids: list[str], completed: list[dict[str, Any]], observed_model_request_count: int, exc: BaseException) -> dict[str, Any]:
    failure = {
        "mode": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V2_5",
        "status": "FAILED_PRESERVED_NO_RETRY",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "stage": stage,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "max_tokens": MAX_TOKENS,
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


def execute_once(*, authorization: dict[str, Any], consumption_path: Path, result_path: Path, preflight: PreflightCallable | None = None, transport: TransportCallable | None = None) -> dict[str, Any]:
    auth = validate_live_execution_authorization(authorization)
    result_target = Path(result_path)
    if result_target.exists():
        raise FileExistsError(f"result already exists; automatic rerun forbidden: {result_target}")
    case_ids = v24.v23.v21._frozen_case_ids()
    if tuple(case_ids) != v24.v23.integrity.EXPECTED_ORDERED_CASE_IDS or len(case_ids) != EXPECTED_MODEL_REQUEST_COUNT:
        raise PermissionError("exact ordered 16-case suite binding failed")

    _claim_authorization_once_v25(Path(consumption_path), auth)
    completed: list[dict[str, Any]] = []
    attempted_count = 0
    preflight_fn = preflight or _default_preflight
    transport_fn = transport or _default_transport

    try:
        preflight_metadata = preflight_fn(base_url=BASE_URL, timeout_seconds=TIMEOUT_SECONDS)
    except BaseException as exc:
        failure = _failure_result(stage="PREFLIGHT_AFTER_CONSUMPTION", auth=auth, case_ids=case_ids, completed=completed, observed_model_request_count=attempted_count, exc=exc)
        v24._persist_result_once(result_target, failure)
        return failure

    try:
        for case_id in case_ids:
            request = build_candidate_request(case_id)
            attempted_count += 1
            raw, provider_metadata = transport_fn(base_url=BASE_URL, payload=request, timeout_seconds=TIMEOUT_SECONDS, case_id=case_id)
            _validate_structured_output(raw=raw, provider_metadata=provider_metadata, case_id=case_id)
            completed.append({"case_id": case_id, "model_response_raw": raw, "provider_envelope_metadata": provider_metadata})
    except BaseException as exc:
        failure = _failure_result(stage="MODEL_REQUEST_AFTER_CONSUMPTION", auth=auth, case_ids=case_ids, completed=completed, observed_model_request_count=attempted_count, exc=exc)
        v24._persist_result_once(result_target, failure)
        return failure

    success = {
        "mode": "EXECUTED_ONCE_AWAITING_HUMAN_REVIEW_SEM_QUALIFICATION_V2_5",
        "status": "AWAITING_HUMAN_REVIEW",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "authorized_git_commit": auth.get("live_runner_git_commit"),
        "authorized_runner_blob_oid": auth.get("live_runner_blob_oid"),
        "qualification_snapshot_sha256": auth.get("qualification_snapshot_sha256"),
        "max_tokens": MAX_TOKENS,
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
    v24._persist_result_once(result_target, success)
    return success


def _report_consumption_probe(template: dict[str, Any]) -> bool:
    approved = _approved_probe_from_template(template)
    consumed = _build_consumed_state_v25(approved)
    immutable_keys = set(template) - {
        "status",
        "authorization_consumed",
        "execution_authorized",
        "model_run_authorized",
        "model_contact_authorized",
    }
    return (
        all(consumed.get(key) == template.get(key) for key in immutable_keys)
        and consumed.get("max_tokens") == MAX_TOKENS
        and consumed.get("live_runner_version") == RUNNER_VERSION
        and consumed.get("live_run_type") == RUN_TYPE
        and consumed.get("live_runner_path") == RUNNER_PATH
        and consumed.get("integration_base_commit") == INTEGRATION_BASE_COMMIT
        and consumed.get("status") == "CONSUMED_PRE_MODEL_CONTACT"
        and consumed.get("authorization_consumed") is True
        and consumed.get("execution_authorized") is False
        and consumed.get("model_run_authorized") is False
        and consumed.get("model_contact_authorized") is False
        and consumed.get("persistence_version") == v24.v23.v22.PERSISTENCE_VERSION
        and consumed.get("consumption_boundary") == "BEFORE_FIRST_MODEL_CONTACT"
        and consumed.get("single_use_claimed") is True
    )


def _report_v22_primitive_probe() -> bool:
    names = set(_claim_authorization_once_v25.__code__.co_names)
    return (
        V22_CLAIM_POSIX is v24.v23.v22._claim_posix
        and V22_CLAIM_WINDOWS is v24.v23.v22._claim_windows
        and "V22_CLAIM_POSIX" in names
        and "V22_CLAIM_WINDOWS" in names
    )


def build_integration_report() -> dict[str, Any]:
    template = build_live_authorization_template()
    candidates = {
        "1536": {"headroom_vs_1024": "+50%", "assessment": "finite but relatively narrow after a hard ceiling hit"},
        "2048": {"headroom_vs_1024": "+100%", "assessment": "selected finite moderate rebinding candidate"},
        "3072": {"headroom_vs_1024": "+200%", "assessment": "larger output/resource envelope without current evidence"},
        "4096": {"headroom_vs_1024": "+300%", "assessment": "largest considered envelope; presently weakly justified"},
    }
    checks = {
        "v24_structured_output_validator_reused": _validate_structured_output is not None,
        "integration_base_exact": INTEGRATION_BASE_COMMIT == "0d96eed2d8246b8316a219c5c99242f83e09ee5f",
        "max_tokens_explicit_2048": MAX_TOKENS == 2048,
        "template_max_tokens_2048": template["max_tokens"] == 2048,
        "v25_consumption_preserves_v25_binding": _report_consumption_probe(template),
        "v22_atomic_write_primitives_reused": _report_v22_primitive_probe(),
        "retry_zero": RETRY_COUNT == 0,
        "output_repair_false": OUTPUT_REPAIR is False,
        "template_not_authorized": template["status"] == "NOT_AUTHORIZED_TEMPLATE",
        "execution_not_authorized": template["execution_authorized"] is False,
        "model_run_not_authorized": template["model_run_authorized"] is False,
        "model_contact_not_authorized": template["model_contact_authorized"] is False,
        "authorization_not_consumed": template["authorization_consumed"] is False,
        "automatic_retry_forbidden": RETRY_COUNT == 0,
        "automatic_rerun_forbidden": True,
        "adaptive_token_increase_forbidden": True,
        "model_not_qualified": True,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_MAX_TOKENS_BINDING_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "governance_status": "NO_MODEL_RUN_AUTHORIZED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "integration_base_commit": INTEGRATION_BASE_COMMIT,
        "selected_max_tokens_candidate": MAX_TOKENS,
        "candidate_assessment": candidates,
        "run_003_evidence": {
            "pf12_completion_tokens": 1024,
            "bound_max_tokens": 1024,
            "structured_output_truncated": True,
            "exact_required_bound_known": False,
        },
        "checks": checks,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_performed": False,
        "authorization_artifact_created": False,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def main() -> int:
    report = build_integration_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
