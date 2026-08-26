#!/usr/bin/env python3
"""One-shot local SEM qualification runner for R16/R18/R21/R22.

The runner executes exactly one qualification run containing exactly four local
model requests, one per frozen synthetic case. It performs no retry, no output
repair and no human-gold decision. Raw model outputs are persisted. Contract and
semantic-boundary validation are fail-closed; a parse/boundary/scope failure
aborts the remaining requests.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.validation.semantic_boundary import validate_semantic_response
from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_2 import build_response_format, chat_completion_structured
from llm.smoketest import canonical_json, parse_model_json, sha256_text

PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_1"
PROMPT_SHA256 = "d3c035b238b0b6bbaec939e6e6bf314387ede804637a98e81b55e8cea57038cd"
CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-ONE-RUN-2026-001"
RUNNER_VERSION = "v0.1"
EXPECTED_RUN_COUNT = 1
EXPECTED_MODEL_REQUEST_COUNT = 4
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_1.json"
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_1.txt"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
CASE_PATHS = [
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r16_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r18_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r21_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r22_syn_v0_1.json",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_git_commit() -> str:
    try:
        completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot resolve clean git state for auditable SEM run") from exc
    if status.stdout.strip():
        raise RuntimeError("working tree must be clean for auditable SEM run")
    commit = completed.stdout.strip()
    if len(commit) != 40 or any(ch not in "0123456789abcdefABCDEF" for ch in commit):
        raise RuntimeError("invalid git commit returned for auditable SEM run")
    return commit.lower()


def canonical_frozen_input(case: dict[str, Any]) -> str:
    case_id = case["case_id"]
    locations = case["source_locations"]
    if case_id == "ZS-KI-B-SEM-R18-SYN-001":
        return "\n".join(
            f'{row["source_location_id"]}|{row["page_reference"]}|{row["original_text"]}' for row in locations
        )
    if len(locations) != 1:
        raise ValueError(f"{case_id}: exactly one source location expected")
    return locations[0]["original_text"]


def validate_frozen_cases(cases: list[dict[str, Any]]) -> None:
    expected_ids = [
        "ZS-KI-B-SEM-R16-SYN-001",
        "ZS-KI-B-SEM-R18-SYN-001",
        "ZS-KI-B-SEM-R21-SYN-001",
        "ZS-KI-B-SEM-R22-SYN-001",
    ]
    if [case.get("case_id") for case in cases] != expected_ids:
        raise ValueError("SEM qualification case set/order differs from frozen R16/R18/R21/R22 set")
    for case in cases:
        if case.get("data_class") != "SYNTHETIC_ONLY":
            raise ValueError(f'{case.get("case_id")}: data_class must be SYNTHETIC_ONLY')
        actual = sha256_text(canonical_frozen_input(case))
        if actual != case.get("frozen_input_sha256"):
            raise ValueError(f'{case["case_id"]}: frozen input hash mismatch')


def build_messages(case: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
    questions = load(QUESTIONS_PATH)["questions"]
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
        "finding_type_meanings": finding_types,
    }
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": canonical_json(user_payload)},
    ]


def provider_metadata(envelope: dict[str, Any]) -> dict[str, Any]:
    return {"id": envelope.get("id"), "model": envelope.get("model"), "created": envelope.get("created"), "usage": envelope.get("usage")}


def persist(result: dict[str, Any], output_path: str) -> None:
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

    base_url = validate_local_base_url(args.base_url)
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    if sha256_text(prompt_text) != PROMPT_SHA256:
        raise RuntimeError("frozen SEM prompt hash mismatch")
    cases = [load(path) for path in CASE_PATHS]
    validate_frozen_cases(cases)
    response_format = build_response_format()
    git_commit = current_git_commit()

    manifest: dict[str, Any] = {
        "run_type": RUN_TYPE,
        "runner_version": RUNNER_VERSION,
        "expected_run_count": EXPECTED_RUN_COUNT,
        "observed_run_count": 0,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        "observed_model_request_count": 0,
        "git_commit": git_commit,
        "contract_version": CONTRACT_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "reference_snapshot": "reference_questions_v0_1.json/schema_version_v0.1/67",
        "reference_snapshot_sha256": sha256_text(canonical_json(load(QUESTIONS_PATH))),
        "response_format_sha256": sha256_text(canonical_json(response_format)),
        "case_ids": [case["case_id"] for case in cases],
        "case_versions": {case["case_id"]: case["case_version"] for case in cases},
        "frozen_input_sha256": {case["case_id"]: case["frozen_input_sha256"] for case in cases},
        "fixture_sha256": {case["case_id"]: sha256_text(canonical_json(case)) for case in cases},
        "data_class": "SYNTHETIC_ONLY",
        "retry_count": 0,
        "output_repair": False,
        "tools": False,
        "web": False,
        "MCP": False,
        "remote_cloud": False,
        "real_data": False,
        "abort_on_scope_or_contract_violation": True,
        "base_url": base_url,
        "model": args.model or None,
        "execution_attempted": False,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    if not args.execute:
        print(json.dumps({"mode": "DRY_RUN_SEM_QUALIFICATION_V0_1", "manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    if not args.model.strip():
        parser.error("--model ist zusammen mit --execute erforderlich")

    manifest["execution_attempted"] = True
    manifest["observed_run_count"] = 1
    results: list[dict[str, Any]] = []
    aggregate: dict[str, Any] = {
        "mode": "EXECUTING_SEM_QUALIFICATION_V0_1",
        "manifest": manifest,
        "cases": results,
        "human_gold_evaluation": "PENDING_HUMAN_REVIEW",
    }

    for case in cases:
        messages = build_messages(case, prompt_text)
        case_result: dict[str, Any] = {
            "case_id": case["case_id"],
            "model_response_raw": None,
            "model_response": None,
            "provider_envelope_metadata": None,
            "boundary_evaluation": None,
            "human_gold_evaluation": "PENDING_HUMAN_REVIEW",
        }
        results.append(case_result)
        manifest["observed_model_request_count"] += 1
        try:
            content, envelope = chat_completion_structured(
                base_url=base_url,
                model=args.model,
                messages=messages,
                temperature=0.0,
            )
        except LocalModelError as exc:
            case_result["endpoint_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_1"
            persist(aggregate, args.output)
            return 2

        case_result["model_response_raw"] = content
        case_result["model_response_sha256"] = sha256_text(content)
        case_result["provider_envelope_metadata"] = provider_metadata(envelope)
        try:
            response = parse_model_json(content)
        except (json.JSONDecodeError, ValueError) as exc:
            case_result["parse_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_1"
            persist(aggregate, args.output)
            return 2

        case_result["model_response"] = response
        allowed_ids = {row["source_location_id"] for row in case["source_locations"]}
        issues = validate_semantic_response(response, allowed_source_location_ids=allowed_ids)
        target_match = response.get("source_location_id") == case["target_source_location_id"]
        case_result["boundary_evaluation"] = {
            "passed": not issues and target_match,
            "target_source_match": target_match,
            "issues": [issue.to_dict() for issue in issues],
        }
        if issues or not target_match:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_1"
            persist(aggregate, args.output)
            return 2
        persist(aggregate, args.output)

    aggregate["mode"] = "EXECUTED_ONCE_AWAITING_HUMAN_GOLD_REVIEW_SEM_QUALIFICATION_V0_1"
    aggregate["technical_boundary_pass"] = True
    persist(aggregate, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
