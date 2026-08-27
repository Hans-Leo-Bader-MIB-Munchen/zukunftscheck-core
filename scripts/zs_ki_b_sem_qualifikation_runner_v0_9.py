#!/usr/bin/env python3
"""Fail-closed v0.9 wrapper for the frozen v0.7 semantic qualification.

Adds two preconditions before any generation request:
1. exact model identifier must match the separately approved authorization artifact;
2. LM Studio must report the approved model as loaded with at least 32768 context tokens.

The frozen suite, Human-Gold, policy, prompt, Meaning Layer, contract and semantic
boundary remain unchanged and are reused from runner v0.8.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_8 as base
from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_5 import chat_completion_structured
from llm.smoketest import parse_model_json

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V0-7-FROZEN-2026-009"
RUNNER_VERSION = "v0.9"
EXPECTED_MODEL_REQUEST_COUNT = 16
REQUIRED_LOADED_CONTEXT_LENGTH = 32768
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_9.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_model_run_authorization_v0_2.json"
PREVIOUS_FAILURE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v08_execution_failure_context_v0_1.json"


def _configure_base() -> None:
    base.RUN_TYPE = RUN_TYPE
    base.RUNNER_VERSION = RUNNER_VERSION
    base.EXPECTED_MODEL_REQUEST_COUNT = EXPECTED_MODEL_REQUEST_COUNT
    base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    base.AUTH_PATH = AUTH_PATH


def _authorization_status() -> bool:
    if not AUTH_PATH.exists():
        return False
    try:
        auth = base.load(AUTH_PATH)
    except (OSError, json.JSONDecodeError):
        return False
    return auth.get("status") == "EXPLICIT_USER_APPROVED"


def validate_execution_authorization(model: str) -> dict[str, Any]:
    if not AUTH_PATH.exists():
        raise PermissionError("explicit v0.9 model-run authorization artifact is absent")
    auth = base.load(AUTH_PATH)
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("v0.9 model-run authorization status is not EXPLICIT_USER_APPROVED")
    if auth.get("run_type") != RUN_TYPE:
        raise PermissionError("v0.9 model-run authorization does not match runner run_type")
    if auth.get("model") != model:
        raise PermissionError(
            f"authorized model mismatch: authorization={auth.get('model')!r}, requested={model!r}"
        )
    if auth.get("required_loaded_context_length") != REQUIRED_LOADED_CONTEXT_LENGTH:
        raise PermissionError("authorization context requirement does not match runner requirement")
    if auth.get("expected_model_request_count") != EXPECTED_MODEL_REQUEST_COUNT:
        raise PermissionError("authorization request count does not match runner scope")
    if auth.get("synthetic_only") is not True or auth.get("local_loopback_only") is not True:
        raise PermissionError("authorization must remain synthetic-only and loopback-only")
    if auth.get("single_run_only") is not True or auth.get("retry_count") != 0 or auth.get("output_repair") is not False:
        raise PermissionError("authorization violates frozen one-shot constraints")
    if auth.get("remote_cloud") is not False or auth.get("real_data") is not False:
        raise PermissionError("authorization must prohibit cloud and real-data execution")
    return auth


def _lmstudio_models_url(base_url: str) -> str:
    normalized = validate_local_base_url(base_url)
    parts = urlsplit(normalized)
    return f"{parts.scheme}://{parts.netloc}/api/v1/models"


def preflight_loaded_model(*, base_url: str, model: str, timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Verify exact loaded instance and context without making a generation request."""
    url = _lmstudio_models_url(base_url)
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"LM Studio preflight failed: {type(exc).__name__}: {exc}") from exc

    models = payload.get("models")
    if not isinstance(models, list):
        raise RuntimeError("LM Studio preflight response has no models list")

    for model_row in models:
        if not isinstance(model_row, dict):
            continue
        instances = model_row.get("loaded_instances") or []
        for instance in instances:
            if not isinstance(instance, dict) or instance.get("id") != model:
                continue
            config = instance.get("config") or {}
            context_length = config.get("context_length")
            if not isinstance(context_length, int):
                raise RuntimeError(f"loaded model {model!r} exposes no integer context_length")
            if context_length < REQUIRED_LOADED_CONTEXT_LENGTH:
                raise RuntimeError(
                    f"loaded context too small for authorized run: {context_length} < {REQUIRED_LOADED_CONTEXT_LENGTH}"
                )
            quantization = model_row.get("quantization")
            quantization_name = quantization.get("name") if isinstance(quantization, dict) else None
            return {
                "endpoint": url,
                "model_key": model_row.get("key"),
                "loaded_instance_id": instance.get("id"),
                "loaded_context_length": context_length,
                "required_loaded_context_length": REQUIRED_LOADED_CONTEXT_LENGTH,
                "max_context_length": model_row.get("max_context_length"),
                "quantization": quantization_name,
                "format": model_row.get("format"),
                "generation_request_count": 0,
            }

    raise RuntimeError(f"authorized model instance {model!r} is not loaded in LM Studio")


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _configure_base()
    payload = base.build_dry_run_manifest(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V0_9"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["expected_model_request_count"] = EXPECTED_MODEL_REQUEST_COUNT
    manifest["execution_authorized"] = _authorization_status()
    manifest["required_loaded_context_length"] = REQUIRED_LOADED_CONTEXT_LENGTH
    manifest["previous_failed_run_recorded"] = PREVIOUS_FAILURE_PATH.exists()
    return payload


def _persist(payload: dict[str, Any], output: str) -> None:
    base._persist(payload, output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    aggregate = build_dry_run_manifest(model=args.model, base_url=args.base_url)
    if not args.execute:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
        return 0
    if not args.model.strip():
        parser.error("--model ist zusammen mit --execute erforderlich")
    try:
        validate_execution_authorization(args.model)
    except PermissionError as exc:
        parser.error(str(exc))

    try:
        preflight = preflight_loaded_model(base_url=args.base_url, model=args.model)
    except RuntimeError as exc:
        aggregate["mode"] = "PRECONDITION_FAILED_SEM_QUALIFICATION_V0_9"
        aggregate["preflight_error"] = str(exc)
        aggregate["manifest"]["execution_attempted"] = False
        aggregate["manifest"]["observed_run_count"] = 0
        aggregate["manifest"]["observed_model_request_count"] = 0
        _persist(aggregate, args.output)
        return 4

    package = base.validate_frozen_package()
    prompt_text = base.PROMPT_PATH.read_text(encoding="utf-8")
    gold_index = {row["case_id"]: row for row in package["gold"]["cases"]}
    aggregate["mode"] = "EXECUTING_SEM_QUALIFICATION_V0_9"
    aggregate["preflight"] = preflight
    aggregate["cases"] = []
    manifest = aggregate["manifest"]
    manifest["execution_attempted"] = True
    manifest["execution_authorized"] = True
    manifest["observed_run_count"] = 1

    for case in package["suite"]["cases"]:
        manifest["observed_model_request_count"] += 1
        row: dict[str, Any] = {"case_id": case["case_id"], "model_response_raw": None, "model_response": None}
        aggregate["cases"].append(row)
        try:
            content, envelope = chat_completion_structured(
                base_url=args.base_url,
                model=args.model,
                messages=base.build_messages(case, prompt_text),
                temperature=0.0,
            )
        except LocalModelError as exc:
            row["endpoint_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9"
            _persist(aggregate, args.output)
            return 2
        row["model_response_raw"] = content
        row["provider_envelope_metadata"] = {
            "id": envelope.get("id"),
            "model": envelope.get("model"),
            "created": envelope.get("created"),
            "usage": envelope.get("usage"),
        }
        try:
            response = parse_model_json(content)
        except (json.JSONDecodeError, ValueError) as exc:
            row["parse_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9"
            _persist(aggregate, args.output)
            return 2
        row["model_response"] = response
        row["boundary_evaluation"] = base.evaluate_boundary(case, response)
        if not row["boundary_evaluation"]["passed"]:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9"
            _persist(aggregate, args.output)
            return 2
        row["gold_evaluation"] = base.evaluate_gold(gold_index[case["case_id"]], response)
        if not row["gold_evaluation"]["passed"]:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V0_9"
            _persist(aggregate, args.output)
            return 3
        _persist(aggregate, args.output)

    aggregate["mode"] = "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V0_9"
    aggregate["technical_boundary_pass"] = True
    aggregate["frozen_gold_pass"] = True
    aggregate["allowed_conclusion"] = package["policy"]["allowed_conclusion_if_passed"]
    aggregate["forbidden_conclusions"] = package["policy"]["forbidden_conclusions_even_if_passed"]
    _persist(aggregate, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
