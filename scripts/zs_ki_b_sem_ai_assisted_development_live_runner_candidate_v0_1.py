#!/usr/bin/env python3
"""Fail-closed live-runner candidate for one future 24-case synthetic development run.

This file defines the future request and execution path but performs no model contact
unless an exact, separately approved authorization object and a separately frozen
preflight result are supplied. No approval is created or implied here.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
AUTH_PREP_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_authorization_prep_candidate_v0_2.json"
CHALLENGES_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_challenges_v0_1.json"
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt"
SCHEMA_PATH = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json"

RUNNER_VERSION = "v0.1-live-candidate-not-authorized"
RUN_TYPE = "ZS-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-LIVE-CANDIDATE-2026-001"
EXPECTED_CASE_COUNT = 24
EXPECTED_MODEL_REQUEST_COUNT = 24
HARD_STOP = "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION"

TransportCallable = Callable[..., tuple[str, dict[str, Any]]]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_authorization_prep() -> dict[str, Any]:
    return _load_json(AUTH_PREP_PATH)


def load_challenges() -> dict[str, Any]:
    return _load_json(CHALLENGES_PATH)


def validate_static_bindings() -> dict[str, Any]:
    prep = load_authorization_prep()
    challenges = load_challenges()
    if prep.get("execution_authorized") is not False:
        raise PermissionError("authorization prep must remain non-authorizing")
    if prep.get("model_contact_authorized") is not False:
        raise PermissionError("authorization prep must remain non-authorizing")
    if prep.get("preflight_authorized") is not False:
        raise PermissionError("authorization prep must remain non-authorizing")
    if prep.get("ready_for_user_approval") is not False:
        raise PermissionError("authorization prep is not ready for approval")
    if prep.get("hard_stop") != HARD_STOP:
        raise PermissionError("hard stop changed")
    if prep.get("expected_case_count") != EXPECTED_CASE_COUNT:
        raise ValueError("expected case count changed")
    if prep.get("expected_model_request_count") != EXPECTED_MODEL_REQUEST_COUNT:
        raise ValueError("expected model request count changed")
    if challenges.get("case_count") != EXPECTED_CASE_COUNT or len(challenges.get("cases", [])) != EXPECTED_CASE_COUNT:
        raise ValueError("challenge fixture must contain exactly 24 cases")
    ids = [case.get("case_id") for case in challenges["cases"]]
    if len(set(ids)) != EXPECTED_CASE_COUNT:
        raise ValueError("challenge case IDs must be unique")
    return prep


def build_request_preview(case: dict[str, Any]) -> dict[str, Any]:
    prep = validate_static_bindings()
    runtime = prep["runtime_parameters"]
    schema = _load_json(SCHEMA_PATH)
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "model": runtime["model_id"],
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps({"source_locations": [{"source_location_id": case["source_location_id"], "text": case["text"]}]}, ensure_ascii=False)},
        ],
        "temperature": runtime["temperature"],
        "max_tokens": runtime["max_tokens"],
        "stream": runtime["stream"],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "zs_ki_b_semantic_proposal",
                "strict": True,
                "schema": schema,
            },
        },
    }
    if payload["model"] != "ministral-3-14b-instruct-2512":
        raise ValueError("model binding changed")
    if payload["temperature"] != 0.0 or payload["max_tokens"] != 2048 or payload["stream"] is not False:
        raise ValueError("request runtime binding changed")
    return payload


def validate_execution_gate(*, authorization: dict[str, Any] | None, preflight_result: dict[str, Any] | None) -> None:
    if not isinstance(authorization, dict):
        raise PermissionError("separate explicit authorization missing")
    if authorization.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("explicit user approval missing")
    for key in ("execution_authorized", "model_contact_authorized"):
        if authorization.get(key) is not True:
            raise PermissionError(f"{key} must be explicitly true in separate authorization")
    if authorization.get("expected_run_count") != 1 or authorization.get("expected_model_request_count") != 24:
        raise PermissionError("authorization scope must be exactly one 24-request run")
    if authorization.get("automatic_retry_authorized") is not False:
        raise PermissionError("automatic retry forbidden")
    if authorization.get("automatic_rerun_authorized") is not False:
        raise PermissionError("automatic rerun forbidden")
    if authorization.get("output_repair_authorized") is not False:
        raise PermissionError("output repair forbidden")
    if not isinstance(preflight_result, dict):
        raise PermissionError("separately frozen preflight result missing")
    if preflight_result.get("status") != "PASS_FROZEN":
        raise PermissionError("preflight result not frozen PASS")
    if preflight_result.get("model_id") != "ministral-3-14b-instruct-2512":
        raise PermissionError("preflight model identity mismatch")
    if int(preflight_result.get("loaded_context", 0)) < 32768:
        raise PermissionError("preflight context below required minimum")


def _default_transport(*, base_url: str, endpoint_path: str, payload: dict[str, Any], timeout_seconds: float) -> tuple[str, dict[str, Any]]:
    if base_url != "http://127.0.0.1:1234/v1" or endpoint_path != "/chat/completions":
        raise PermissionError("unexpected endpoint")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        base_url + endpoint_path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"transport failed: {exc}") from exc
    choices = envelope.get("choices") if isinstance(envelope, dict) else None
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("provider envelope has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise RuntimeError("provider envelope has no string content")
    metadata = {key: envelope.get(key) for key in ("id", "model", "created", "usage")}
    return content, metadata


def execute_once(*, authorization: dict[str, Any], preflight_result: dict[str, Any], transport: TransportCallable | None = None) -> dict[str, Any]:
    validate_static_bindings()
    validate_execution_gate(authorization=authorization, preflight_result=preflight_result)
    prep = load_authorization_prep()
    challenges = load_challenges()["cases"]
    runtime = prep["runtime_parameters"]
    transport_fn = transport or _default_transport
    completed: list[dict[str, Any]] = []
    request_count = 0
    for case in challenges:
        if request_count >= EXPECTED_MODEL_REQUEST_COUNT:
            raise RuntimeError("request ceiling exceeded")
        payload = build_request_preview(case)
        request_count += 1
        raw, metadata = transport_fn(
            base_url=runtime["endpoint_base_url"],
            endpoint_path=runtime["endpoint_path"],
            payload=payload,
            timeout_seconds=runtime["request_timeout_seconds"],
        )
        parsed = json.loads(raw)
        completed.append({"case_id": case["case_id"], "response": parsed, "provider_metadata": metadata})
    if request_count != EXPECTED_MODEL_REQUEST_COUNT:
        raise RuntimeError("exactly 24 requests required")
    return {
        "mode": "EXECUTED_ONCE_AWAITING_DEVELOPMENT_EVALUATION",
        "run_type": RUN_TYPE,
        "runner_version": RUNNER_VERSION,
        "data_class": "SYNTHETIC_ONLY",
        "development_only": True,
        "qualification_claim_allowed": False,
        "observed_model_request_count": request_count,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "output_repair_authorized": False,
        "cases": completed,
    }


def main() -> int:
    validate_static_bindings()
    print(json.dumps({
        "runner_version": RUNNER_VERSION,
        "status": "STATIC_LIVE_RUNNER_CANDIDATE_NOT_AUTHORIZED",
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "model_request_count": 0,
        "hard_stop": HARD_STOP,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
