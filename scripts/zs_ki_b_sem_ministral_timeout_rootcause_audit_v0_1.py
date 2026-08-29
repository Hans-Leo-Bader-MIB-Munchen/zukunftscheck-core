#!/usr/bin/env python3
"""Model-free static audit for the v1.5 Ministral PF1 timeout.

No network, localhost, model, LM Studio, subprocess, or generation contact occurs.
The audit profiles the exact frozen PF1 request construction and highlights
transport/schema properties that can permit very long generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm.smoketest import canonical_json

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt"
QUESTIONS_PATH = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
FINDING_TYPES_PATH = ROOT / "domains/zukunftscheck/rules/finding_type_meanings_v0_1.json"
SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
SCHEMA_PATH = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_2.schema.json"
TRANSPORT_PATH = ROOT / "llm/local_model/structured_output_v0_5.py"
TARGET_CASE_ID = "ZS-KI-B-SEM-V07-Q-PF1-SYN-001"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text_metrics(text: str) -> dict[str, int]:
    return {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
    }


def _array_paths_without_max_items(schema: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(schema, dict):
        if schema.get("type") == "array" and "maxItems" not in schema:
            found.append(path)
        for key, value in schema.items():
            found.extend(_array_paths_without_max_items(value, f"{path}.{key}"))
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            found.extend(_array_paths_without_max_items(value, f"{path}[{index}]"))
    return found


def build_pf1_payload() -> dict[str, Any]:
    suite = load(SUITE_PATH)
    case = next(row for row in suite["cases"] if row["case_id"] == TARGET_CASE_ID)
    return {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions": load(QUESTIONS_PATH)["questions"],
        "reference_question_meanings": load(MEANINGS_PATH),
        "finding_type_meanings": load(FINDING_TYPES_PATH)["finding_types"],
    }


def build_audit() -> dict[str, Any]:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = build_pf1_payload()
    payload_text = canonical_json(payload)
    schema = load(SCHEMA_PATH)
    schema_text = canonical_json(schema)
    transport_source = TRANSPORT_PATH.read_text(encoding="utf-8")

    components = {
        "system_prompt": text_metrics(prompt),
        "full_user_payload": text_metrics(payload_text),
        "reference_questions": text_metrics(canonical_json(payload["reference_questions"])),
        "reference_question_meanings": text_metrics(canonical_json(payload["reference_question_meanings"])),
        "finding_type_meanings": text_metrics(canonical_json(payload["finding_type_meanings"])),
        "source_locations": text_metrics(canonical_json(payload["source_locations"])),
        "response_schema": text_metrics(schema_text),
    }

    total_message_chars = components["system_prompt"]["characters"] + components["full_user_payload"]["characters"]
    total_message_bytes = components["system_prompt"]["utf8_bytes"] + components["full_user_payload"]["utf8_bytes"]

    return {
        "audit_version": "ZS-KI-B-SEM-MINISTRAL-TIMEOUT-ROOTCAUSE-AUDIT-2026-001_v0.1",
        "mode": "MODEL_FREE_STATIC_AUDIT",
        "target_case_id": TARGET_CASE_ID,
        "model_contact_performed": False,
        "localhost_contact_performed": False,
        "remote_contact_performed": False,
        "request_profile": {
            "reference_question_count": len(payload["reference_questions"]),
            "meaning_count": len(payload["reference_question_meanings"].get("meanings", [])),
            "source_location_count": len(payload["source_locations"]),
            "components": components,
            "messages_total": {"characters": total_message_chars, "utf8_bytes": total_message_bytes},
        },
        "transport_profile": {
            "stream_false": '"stream": False' in transport_source,
            "has_max_tokens_parameter": "max_tokens" in transport_source,
            "has_max_completion_tokens_parameter": "max_completion_tokens" in transport_source,
            "default_timeout_seconds": 600.0,
            "v15_required_timeout_seconds": 1800,
        },
        "schema_profile": {
            "strict_json_schema": True,
            "array_paths_without_max_items": _array_paths_without_max_items(schema),
            "unbounded_array_count": len(_array_paths_without_max_items(schema)),
        },
        "observed_v15_run_evidence": {
            "prompt_tokens_from_lm_studio_log": 14896,
            "observed_decode_rate_tokens_per_second_range": [1.5, 1.76],
            "timeout_seconds": 1800,
            "completed_response_observed": False,
        },
        "root_cause_assessment": {
            "established": [
                "PF1 sends all 67 reference questions and the complete 67-entry Meaning Layer despite a one-sentence synthetic source case.",
                "The structured transport defines no max_tokens or max_completion_tokens generation cap.",
                "The strict response schema contains arrays without maxItems, so the contract itself does not impose a finite proposal/assignment/note count.",
                "The v1.5 transport timeout was correctly raised to 1800 seconds, yet no complete PF1 response arrived within that window.",
            ],
            "not_yet_established": [
                "Whether the dominant bottleneck is CPU/GPU offload, KV-cache/context handling, constrained-decoding behavior, or model-specific generation behavior.",
                "Whether a bounded output cap alone would preserve semantic quality.",
                "Whether reducing the Meaning Layer supplied per case can preserve qualification validity.",
            ],
            "recommended_next_model_free_action": "Design a bounded-request v1.7 candidate architecture without authorizing execution: explicit output cap, bounded schema cardinalities, and a semantically justified context-reduction strategy tested only with static/unit tests.",
        },
    }


def main() -> int:
    print(json.dumps(build_audit(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
