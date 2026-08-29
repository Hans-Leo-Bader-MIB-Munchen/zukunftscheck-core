#!/usr/bin/env python3
"""Model-free v1.7 bounded-request integration preparation.

This module binds the v1.7 candidate prompt, candidate semantic schema and bounded
payload builder into a deterministic dry-run/preview path. It deliberately exposes
no execution path and performs no localhost, network, preflight or model contact.
Any future model execution requires a separately versioned runner and a new explicit
single-use authorization.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm.smoketest import canonical_json
from llm.local_model import structured_output_v0_6_candidate as bounded
import scripts.zs_ki_b_sem_qualifikation_runner_v1_6 as v16

ROOT = Path(__file__).resolve().parents[1]
RUNNER_VERSION = "v1.7-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-7-BOUNDING-PREP-2026-018"
RUNTIME_MODEL_ID = v16.RUNTIME_MODEL_ID
MODEL_REPOSITORY = v16.MODEL_REPOSITORY
PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_7_candidate"
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt"
SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
QUESTIONS_PATH = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
FINDING_TYPES_PATH = ROOT / "domains/zukunftscheck/rules/finding_type_meanings_v0_1.json"
ACTIVE_SCHEMA_PATH = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_2.schema.json"
CANDIDATE_SCHEMA_PATH = bounded.SCHEMA_PATH
TARGET_CASE_ID = "ZS-KI-B-SEM-V07-Q-PF1-SYN-001"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_case(case_id: str = TARGET_CASE_ID) -> dict[str, Any]:
    suite = load(SUITE_PATH)
    return next(case for case in suite["cases"] if case["case_id"] == case_id)


def build_candidate_messages(case_id: str = TARGET_CASE_ID) -> list[dict[str, str]]:
    case = _candidate_case(case_id)
    questions = load(QUESTIONS_PATH)["questions"]
    meanings = load(MEANINGS_PATH)
    finding_types = load(FINDING_TYPES_PATH)["finding_types"]
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions": questions,
        "reference_question_meanings": meanings,
        "finding_type_meanings": finding_types,
    }
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": canonical_json(payload)},
    ]


def build_candidate_request_preview(
    *, case_id: str = TARGET_CASE_ID, model: str = RUNTIME_MODEL_ID
) -> dict[str, Any]:
    """Build the exact bounded candidate request object without transmitting it."""
    return bounded.build_structured_payload(
        model=model,
        messages=build_candidate_messages(case_id),
        max_completion_tokens=bounded.MAX_COMPLETION_TOKENS,
    )


def build_dry_run_manifest() -> dict[str, Any]:
    payload = v16.build_dry_run_manifest(model=RUNTIME_MODEL_ID)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_7_BOUNDING_PREP"
    manifest = payload["manifest"]
    candidate_schema = load(CANDIDATE_SCHEMA_PATH)
    active_schema = load(ACTIVE_SCHEMA_PATH)
    messages = build_candidate_messages()
    user_payload = json.loads(messages[1]["content"])

    manifest.update(
        {
            "run_type": RUN_TYPE,
            "runner_version": RUNNER_VERSION,
            "prompt_version": PROMPT_VERSION,
            "candidate_contract_version": candidate_schema["$id"],
            "active_contract_version_unchanged": active_schema["$id"],
            "candidate_output_mode_version": bounded.OUTPUT_MODE_VERSION,
            "max_completion_tokens": bounded.MAX_COMPLETION_TOKENS,
            "request_timeout_seconds": bounded.REQUEST_TIMEOUT_SECONDS,
            "candidate_prompt_path": str(PROMPT_PATH.relative_to(ROOT)),
            "candidate_schema_path": str(CANDIDATE_SCHEMA_PATH.relative_to(ROOT)),
            "full_reference_question_count": len(user_payload["reference_questions"]),
            "full_meaning_count": len(user_payload["reference_question_meanings"]["meanings"]),
            "context_reduction_performed": False,
            "pf_prefiltering_performed": False,
            "bounded_request_integration_prepared": True,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "model_contact_performed": False,
            "authorization_path": None,
            "model_qualified": False,
            "new_explicit_model_contact_authorization_required_before_any_execution": True,
        }
    )
    return payload


def validate_execution_authorization(model: str = RUNTIME_MODEL_ID) -> dict[str, Any]:
    raise PermissionError(
        "v1.7 bounding integration prep is model-free only; no execution authorization exists"
    )


def main() -> int:
    print(json.dumps(build_dry_run_manifest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
