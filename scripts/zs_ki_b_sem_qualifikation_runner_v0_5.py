#!/usr/bin/env python3
"""Additive SEM qualification runner v0.5 for the architecture-delta branch.

Binds semantic contract v0.2, prompt v0.3, proposal-level provenance boundary,
and the limited reference-question meaning layer. It preserves synthetic-only,
loopback-only, no-retry and no-repair constraints. No model call occurs in dry run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_1 as base
from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2
from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_5 import build_response_format, chat_completion_structured
from llm.smoketest import canonical_json, parse_model_json, sha256_text

PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_3"
CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-ARCHITEKTURDELTA-2026-005"
RUNNER_VERSION = "v0.5"
EXPECTED_RUN_COUNT = 1
EXPECTED_MODEL_REQUEST_COUNT = 4
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_5.json"
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_3.txt"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_question_meanings_v0_1.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
CASE_PATHS = base.CASE_PATHS


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_git_commit() -> str:
    return base.current_git_commit()


def build_messages(case: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
    questions = load(QUESTIONS_PATH)["questions"]
    meanings = load(MEANINGS_PATH)
    finding_types = load(FINDING_TYPES_PATH)["finding_types"]
    user_payload = {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions": [
            {"question_id": row["question_id"], "pf_id": row["pf_id"], "question": row["question"]}
            for row in questions
        ],
        "reference_question_meanings": meanings,
        "finding_type_meanings": finding_types,
    }
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": canonical_json(user_payload)},
    ]


def evaluate_boundary(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    allowed_ids = {
        row["source_location_id"]
        for row in case.get("source_locations", [])
        if isinstance(row, dict) and isinstance(row.get("source_location_id"), str)
    }
    target = case.get("target_source_location_id")
    issues = validate_semantic_response_v0_2(
        response,
        allowed_source_location_ids=allowed_ids,
        target_source_location_id=target,
    )
    target_match = response.get("source_location_id") == target
    return {
        "passed": not issues and target_match,
        "target_source_match": target_match,
        "issues": [issue.to_dict() for issue in issues],
    }


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    validated_base_url = validate_local_base_url(base_url)
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    cases = [load(path) for path in CASE_PATHS]
    base.validate_frozen_cases(cases)
    response_format = build_response_format()
    manifest = {
        "run_type": RUN_TYPE,
        "runner_version": RUNNER_VERSION,
        "expected_run_count": EXPECTED_RUN_COUNT,
        "observed_run_count": 0,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": 0,
        "git_commit": current_git_commit(),
        "contract_version": CONTRACT_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": sha256_text(prompt_text),
        "reference_snapshot": "reference_questions_v0_1.json/schema_version_v0.1/67",
        "reference_snapshot_sha256": sha256_text(canonical_json(load(QUESTIONS_PATH))),
        "meaning_layer": "reference_question_meanings_v0_1.json/R16-limited",
        "meaning_layer_sha256": sha256_text(canonical_json(load(MEANINGS_PATH))),
        "response_format_sha256": sha256_text(canonical_json(response_format)),
        "case_ids": [case["case_id"] for case in cases],
        "data_class": "SYNTHETIC_ONLY",
        "retry_count": 0,
        "output_repair": False,
        "tools": False,
        "web": False,
        "MCP": False,
        "remote_cloud": False,
        "real_data": False,
        "abort_on_scope_or_contract_violation": True,
        "base_url": validated_base_url,
        "model": model or None,
        "execution_attempted": False,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    return {"mode": "DRY_RUN_SEM_QUALIFICATION_V0_2", "manifest": manifest}


def _persist(result: dict[str, Any], output_path: str) -> None:
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    Path(output_path).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    dry = build_dry_run_manifest(model=args.model, base_url=args.base_url)
    if not args.execute:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return 0
    if not args.model.strip():
        parser.error("--model ist zusammen mit --execute erforderlich")

    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    cases = [load(path) for path in CASE_PATHS]
    base.validate_frozen_cases(cases)
    aggregate = dry
    manifest = aggregate["manifest"]
    aggregate["mode"] = "EXECUTING_SEM_QUALIFICATION_V0_2"
    aggregate["cases"] = []
    aggregate["human_gold_evaluation"] = "PENDING_HUMAN_REVIEW"
    manifest["execution_attempted"] = True
    manifest["observed_run_count"] = 1

    for case in cases:
        manifest["observed_model_request_count"] += 1
        case_result: dict[str, Any] = {
            "case_id": case["case_id"],
            "model_response_raw": None,
            "model_response": None,
            "boundary_evaluation": None,
            "human_gold_evaluation": "PENDING_HUMAN_REVIEW",
        }
        aggregate["cases"].append(case_result)
        try:
            content, envelope = chat_completion_structured(
                base_url=args.base_url,
                model=args.model,
                messages=build_messages(case, prompt_text),
                temperature=0.0,
            )
        except LocalModelError as exc:
            case_result["endpoint_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_2"
            _persist(aggregate, args.output)
            return 2

        case_result["model_response_raw"] = content
        case_result["provider_envelope_metadata"] = {
            "id": envelope.get("id"),
            "model": envelope.get("model"),
            "created": envelope.get("created"),
            "usage": envelope.get("usage"),
        }
        try:
            response = parse_model_json(content)
        except (json.JSONDecodeError, ValueError) as exc:
            case_result["parse_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_2"
            _persist(aggregate, args.output)
            return 2
        case_result["model_response"] = response
        case_result["boundary_evaluation"] = evaluate_boundary(case, response)
        if not case_result["boundary_evaluation"]["passed"]:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_2"
            _persist(aggregate, args.output)
            return 2
        _persist(aggregate, args.output)

    aggregate["mode"] = "EXECUTED_ONCE_AWAITING_HUMAN_GOLD_REVIEW_SEM_QUALIFICATION_V0_2"
    aggregate["technical_boundary_pass"] = True
    _persist(aggregate, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
