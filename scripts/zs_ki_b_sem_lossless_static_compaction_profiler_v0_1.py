#!/usr/bin/env python3
"""Model-free lossless static payload compaction profiler v0.1.

Evaluates a reversible columnar representation for the two largest repeated JSON
blocks in SEM runner v0.6: reference_questions and reference_question_meanings.
No semantic item is removed. No model/network contact occurs.

The candidate representation replaces repeated per-row object keys with one field
legend plus ordered row arrays. Before reporting any size reduction, the script
round-trips both compact blocks back into the current v0.6 structures and requires
exact Python-structure equality.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_6 as runner
from llm.local_model.structured_output_v0_5 import build_response_format
from llm.smoketest import canonical_json


def measure(value: Any) -> dict[str, int]:
    text = value if isinstance(value, str) else canonical_json(value)
    return {"chars": len(text), "utf8_bytes": len(text.encode("utf-8"))}


def compact_questions(doc: dict[str, Any]) -> dict[str, Any]:
    fields = ["question_id", "pf_id", "question"]
    return {
        "schema_version": doc["schema_version"],
        "source_drive_file_id": doc.get("source_drive_file_id"),
        "count": doc["count"],
        "fields": fields,
        "rows": [[row[field] for field in fields] for row in doc["questions"]],
    }


def expand_questions(compact: dict[str, Any]) -> dict[str, Any]:
    fields = compact["fields"]
    return {
        "schema_version": compact["schema_version"],
        "source_drive_file_id": compact.get("source_drive_file_id"),
        "count": compact["count"],
        "questions": [dict(zip(fields, row, strict=True)) for row in compact["rows"]],
    }


def compact_meanings(doc: dict[str, Any]) -> dict[str, Any]:
    fields = ["question_id", "pf_id", "positive_scope", "negative_scope", "disambiguation_notes"]
    return {
        "schema_version": doc["schema_version"],
        "calibration_scope": doc["calibration_scope"],
        "fields": fields,
        "rows": [[row[field] for field in fields] for row in doc["meanings"]],
    }


def expand_meanings(compact: dict[str, Any]) -> dict[str, Any]:
    fields = compact["fields"]
    return {
        "schema_version": compact["schema_version"],
        "calibration_scope": compact["calibration_scope"],
        "meanings": [dict(zip(fields, row, strict=True)) for row in compact["rows"]],
    }


def build_full_user_payload(case: dict[str, Any], questions_doc: dict[str, Any], meanings_doc: dict[str, Any], finding_types: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions": [
            {"question_id": row["question_id"], "pf_id": row["pf_id"], "question": row["question"]}
            for row in questions_doc["questions"]
        ],
        "reference_question_meanings": meanings_doc,
        "finding_type_meanings": finding_types,
    }


def build_compact_user_payload(case: dict[str, Any], compact_q: dict[str, Any], compact_m: dict[str, Any], finding_types: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions_compact": compact_q,
        "reference_question_meanings_compact": compact_m,
        "finding_type_meanings": finding_types,
    }


def main() -> int:
    questions_doc = runner.load(runner.QUESTIONS_PATH)
    meanings_doc = runner.load(runner.MEANINGS_PATH)
    finding_types = runner.load(runner.FINDING_TYPES_PATH)["finding_types"]
    compact_q = compact_questions(questions_doc)
    compact_m = compact_meanings(meanings_doc)

    q_roundtrip = expand_questions(compact_q) == questions_doc
    m_roundtrip = expand_meanings(compact_m) == meanings_doc
    if not q_roundtrip or not m_roundtrip:
        raise RuntimeError("lossless roundtrip failed; no compaction result may be reported")

    prompt_text = runner.PROMPT_PATH.read_text(encoding="utf-8")
    response_format = build_response_format()
    prompt_bytes = len(prompt_text.encode("utf-8"))
    schema_bytes = measure(response_format)["utf8_bytes"]

    cases = []
    for path in runner.CASE_PATHS:
        case = runner.load(path)
        full_payload = build_full_user_payload(case, questions_doc, meanings_doc, finding_types)
        compact_payload = build_compact_user_payload(case, compact_q, compact_m, finding_types)
        full_bytes = measure(full_payload)["utf8_bytes"]
        compact_bytes = measure(compact_payload)["utf8_bytes"]
        full_total = prompt_bytes + schema_bytes + full_bytes
        compact_total = prompt_bytes + schema_bytes + compact_bytes
        reduction = 0.0 if full_total == 0 else (1 - compact_total / full_total) * 100
        cases.append({
            "case_id": case["case_id"],
            "full_user_payload_bytes": full_bytes,
            "compact_user_payload_bytes": compact_bytes,
            "full_total_static_request_bytes": full_total,
            "compact_total_static_request_bytes": compact_total,
            "total_static_request_byte_reduction_percent": round(reduction, 2),
        })

    q_original = {
        "questions": [
            {"question_id": row["question_id"], "pf_id": row["pf_id"], "question": row["question"]}
            for row in questions_doc["questions"]
        ]
    }
    result = {
        "mode": "MODEL_FREE_LOSSLESS_STATIC_COMPACTION_PROFILE_V0_1",
        "model_contact": False,
        "network_contact": False,
        "qualification_claim": False,
        "production_change_claim": False,
        "runner_version_reference": runner.RUNNER_VERSION,
        "prompt_version_reference": runner.PROMPT_VERSION,
        "roundtrip": {
            "reference_questions_exact_structure_equal": q_roundtrip,
            "reference_question_meanings_exact_structure_equal": m_roundtrip,
            "question_count_preserved": len(compact_q["rows"]) == 67,
            "meaning_count_preserved": len(compact_m["rows"]) == len(meanings_doc["meanings"]),
        },
        "block_measurements": {
            "reference_questions_current_runner_form": measure(q_original),
            "reference_questions_compact_candidate": measure(compact_q),
            "reference_question_meanings_current": measure(meanings_doc),
            "reference_question_meanings_compact_candidate": measure(compact_m),
            "system_prompt_unchanged": measure(prompt_text),
            "response_format_unchanged": measure(response_format),
            "finding_type_meanings_unchanged": measure(finding_types),
        },
        "cases": cases,
        "interpretation_guardrail": (
            "This is a byte/character profile of a losslessly reconstructable representation, not a tokenizer benchmark. "
            "Using the compact representation in a model request would still require a versioned prompt/request-contract change, tests, new freeze and explicit qualification authorization."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
