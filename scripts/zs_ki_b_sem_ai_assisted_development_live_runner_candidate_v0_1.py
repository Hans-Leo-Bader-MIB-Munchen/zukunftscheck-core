#!/usr/bin/env python3
"""Static live-runner architecture candidate for the 24 synthetic SEM development cases.

This module builds and validates the exact future request package, but deliberately
exposes no model-contact path yet. Durable single-use authorization consumption and a
separately frozen preflight-result binding must be integrated in a later candidate
before any execution can become eligible for explicit user approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNNER_VERSION = "ZS-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-LIVE-RUNNER-2026-001_v0.1"
RUN_TYPE = "ZS-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-SYNTHETIC-ONE-RUN-2026-001"
EXPECTED_CASE_COUNT = 24
EXPECTED_MODEL_REQUEST_COUNT = 24
HARD_STOP = "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION"

RUNTIME_BINDING_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_runtime_binding_candidate_v0_1.json"
RUNTIME_BINDING_BLOB = "d6a177fdb205b9283ef3e2983b81d524d910d1f8"
CHALLENGES_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_challenges_v0_1.json"
CHALLENGES_BLOB = "3fd3128e39ee67661d3c7d545de1d7376de2a855"
GOLD_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_gold_v0_2.json"
GOLD_BLOB = "76d18ca315b2066c564770d489b60b7d4e1f3566"
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt"
PROMPT_BLOB = "20bb484a22e37ff12e1c2c5976e8baf85fbe7d24"
QUESTIONS_PATH = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
QUESTIONS_BLOB = "d9ab893d6614a5fd98738d24e9541feb83e4ecb5"
MEANINGS_PATH = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
MEANINGS_BLOB = "a3fcb71782fb2097f45e7cbea325b09181972664"
FINDING_TYPES_PATH = ROOT / "domains/zukunftscheck/rules/finding_type_meanings_v0_1.json"
SCHEMA_PATH = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json"
SCHEMA_BLOB = "bc3dd4832db51677bdaf6f16028ade1b02214673"
ORDERED_CASE_IDS_SHA256 = "b02bc870f83c322cd000f47e2000a1e17617f465293afb990ff949f534c6b2e8"


class LiveRunnerCandidateError(RuntimeError):
    pass


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise LiveRunnerCandidateError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_blob(path: Path, expected: str) -> None:
    if not path.is_file() or git_blob_sha1(path) != expected:
        raise PermissionError(f"bound artifact mismatch: {path.relative_to(ROOT)}")


def validate_static_package() -> dict[str, Any]:
    for path, blob in (
        (RUNTIME_BINDING_PATH, RUNTIME_BINDING_BLOB),
        (CHALLENGES_PATH, CHALLENGES_BLOB),
        (GOLD_PATH, GOLD_BLOB),
        (PROMPT_PATH, PROMPT_BLOB),
        (QUESTIONS_PATH, QUESTIONS_BLOB),
        (MEANINGS_PATH, MEANINGS_BLOB),
        (SCHEMA_PATH, SCHEMA_BLOB),
    ):
        _assert_blob(path, blob)

    runtime = load_json(RUNTIME_BINDING_PATH)
    cases = load_json(CHALLENGES_PATH)["cases"]
    gold = load_json(GOLD_PATH)["cases"]
    case_ids = [case["case_id"] for case in cases]
    gold_ids = [case["case_id"] for case in gold]
    if len(case_ids) != EXPECTED_CASE_COUNT or len(set(case_ids)) != EXPECTED_CASE_COUNT:
        raise PermissionError("development case count/uniqueness binding failed")
    if case_ids != gold_ids:
        raise PermissionError("development cases and Gold order differ")
    if hashlib.sha256(canonical_json(case_ids).encode("utf-8")).hexdigest() != ORDERED_CASE_IDS_SHA256:
        raise PermissionError("ordered development case IDs hash mismatch")

    params = runtime["runtime_parameters"]
    expected = {
        "model_id": "ministral-3-14b-instruct-2512",
        "model_repository": "mistralai/Ministral-3-14B-Instruct-2512-GGUF",
        "quantization": "Q4_K_M",
        "adapter_version": "LM_STUDIO_OPENAI_COMPATIBLE_CHAT_COMPLETIONS_V1",
        "endpoint_base_url": "http://127.0.0.1:1234/v1",
        "endpoint_path": "/chat/completions",
        "max_tokens": 2048,
        "temperature": 0.0,
        "stream": False,
        "request_timeout_seconds": 1800.0,
        "retry_count": 0,
        "output_repair": False,
        "required_loaded_context_min": 32768,
    }
    for key, value in expected.items():
        if params.get(key) != value:
            raise PermissionError(f"runtime binding mismatch: {key}")
    for key in ("execution_authorized", "model_contact_authorized", "preflight_authorized", "ready_for_user_approval"):
        if runtime.get(key) is not False:
            raise PermissionError(f"runtime binding must remain non-authorizing: {key}")
    return runtime


def ordered_case_ids() -> list[str]:
    validate_static_package()
    return [case["case_id"] for case in load_json(CHALLENGES_PATH)["cases"]]


def _case(case_id: str) -> dict[str, Any]:
    matches = [case for case in load_json(CHALLENGES_PATH)["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise KeyError(f"unknown or duplicate development case: {case_id}")
    return matches[0]


def build_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "zs_ki_b_semantic_contract_v0_3_candidate",
            "strict": True,
            "schema": load_json(SCHEMA_PATH),
        },
    }


def build_candidate_messages(case_id: str) -> list[dict[str, str]]:
    validate_static_package()
    case = _case(case_id)
    payload = {
        "case_id": case["case_id"],
        "data_class": "SYNTHETIC_ONLY",
        "target_source_location_id": case["source_location_id"],
        "source_locations": [{"source_location_id": case["source_location_id"], "text": case["text"]}],
        "reference_questions": load_json(QUESTIONS_PATH)["questions"],
        "reference_question_meanings": load_json(MEANINGS_PATH),
        "finding_type_meanings": load_json(FINDING_TYPES_PATH)["finding_types"],
    }
    return [
        {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
        {"role": "user", "content": canonical_json(payload)},
    ]


def build_candidate_request(case_id: str) -> dict[str, Any]:
    runtime = validate_static_package()["runtime_parameters"]
    request = {
        "model": runtime["model_id"],
        "messages": build_candidate_messages(case_id),
        "temperature": runtime["temperature"],
        "max_tokens": runtime["max_tokens"],
        "stream": False,
        "response_format": build_response_format(),
    }
    if "max_completion_tokens" in request:
        raise LiveRunnerCandidateError("max_completion_tokens forbidden")
    return request


def validate_execution_authorization(*args: Any, **kwargs: Any) -> dict[str, Any]:
    raise PermissionError(
        "v0.1 is static request architecture only; durable single-use authorization consumption and frozen preflight binding are not yet integrated"
    )


def execute_once(*args: Any, **kwargs: Any) -> dict[str, Any]:
    raise PermissionError(
        "v0.1 live-runner candidate is not executable and cannot contact localhost or a model"
    )


def build_static_architecture_report() -> dict[str, Any]:
    case_ids = ordered_case_ids()
    preview = build_candidate_request(case_ids[0])
    user_payload = json.loads(preview["messages"][1]["content"])
    return {
        "mode": "STATIC_LIVE_RUNNER_ARCHITECTURE_CANDIDATE_ONLY",
        "status": "PASS_STATIC_REQUEST_ARCHITECTURE_AWAITING_CONSUMPTION_AND_PREFLIGHT_GATE",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "expected_case_count": len(case_ids),
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "reference_question_count": len(user_payload["reference_questions"]),
        "meaning_count": len(user_payload["reference_question_meanings"]["meanings"]),
        "model_id": preview["model"],
        "max_tokens": preview["max_tokens"],
        "temperature": preview["temperature"],
        "stream": preview["stream"],
        "response_format_type": preview["response_format"]["type"],
        "execution_authorized": False,
        "model_contact_authorized": False,
        "preflight_authorized": False,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "output_repair_authorized": False,
        "ready_for_user_approval": False,
        "qualification_claim_allowed": False,
        "hard_stop": HARD_STOP,
    }


def main() -> int:
    print(json.dumps(build_static_architecture_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
