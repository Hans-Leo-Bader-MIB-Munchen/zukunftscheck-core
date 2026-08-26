#!/usr/bin/env python3
"""Model-free exact-v0.6 Stage-B payload profiler.

Measures the current SEM runner v0.6 payload on the four known regression/control
cases and compares it with the same payload after deterministic PF Stage-A routing.
Only reference_questions are reduced. The complete meaning layer, finding-type
meanings, system prompt and response format remain unchanged.

This script performs no model or network contact and makes no qualification or
production-routing claim.
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
import scripts.zs_ki_b_sem_pf_router_v0_1 as router
from llm.local_model.structured_output_v0_5 import build_response_format
from llm.smoketest import canonical_json


def measure(text: str) -> dict[str, int]:
    return {"chars": len(text), "utf8_bytes": len(text.encode("utf-8"))}


def build_user_payload(case: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    meanings = runner.load(runner.MEANINGS_PATH)
    finding_types = runner.load(runner.FINDING_TYPES_PATH)["finding_types"]
    return {
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


def target_text(case: dict[str, Any]) -> str:
    target = case["target_source_location_id"]
    for row in case.get("source_locations", []):
        if row.get("source_location_id") == target:
            for key in ("text", "content", "source_text"):
                value = row.get(key)
                if isinstance(value, str) and value.strip():
                    return value
    raise RuntimeError(f"No target source text found for {case['case_id']}")


def main() -> int:
    all_questions = runner.load(runner.QUESTIONS_PATH)["questions"]
    pf_semantics = router.load_pf_semantics()
    prompt_text = runner.PROMPT_PATH.read_text(encoding="utf-8")
    response_format_text = canonical_json(build_response_format())

    rows = []
    for path in runner.CASE_PATHS:
        case = runner.load(path)
        routed = router.route_text(target_text(case), all_questions, pf_semantics)
        selected_ids = set(routed["selected_question_ids"])
        routed_questions = [row for row in all_questions if row["question_id"] in selected_ids]

        full_user = canonical_json(build_user_payload(case, all_questions))
        routed_user = canonical_json(build_user_payload(case, routed_questions))
        full_total_bytes = (
            len(prompt_text.encode("utf-8"))
            + len(full_user.encode("utf-8"))
            + len(response_format_text.encode("utf-8"))
        )
        routed_total_bytes = (
            len(prompt_text.encode("utf-8"))
            + len(routed_user.encode("utf-8"))
            + len(response_format_text.encode("utf-8"))
        )
        reduction = 0.0 if full_total_bytes == 0 else (1 - routed_total_bytes / full_total_bytes) * 100

        rows.append({
            "case_id": case["case_id"],
            "route_mode": routed["mode"],
            "selected_pf_ids": routed["selected_pf_ids"],
            "selected_question_count": routed["selected_question_count"],
            "full_user_payload": measure(full_user),
            "stage_b_user_payload": measure(routed_user),
            "full_total_static_request_bytes": full_total_bytes,
            "stage_b_total_static_request_bytes": routed_total_bytes,
            "total_static_request_byte_reduction_percent": round(reduction, 2),
            "fallback_reasons": routed["fallback_reasons"],
        })

    result = {
        "mode": "MODEL_FREE_EXACT_V0_6_STAGE_B_PAYLOAD_PROFILE_V0_1",
        "model_contact": False,
        "network_contact": False,
        "qualification_claim": False,
        "production_routing_claim": False,
        "known_cases_are_regression_control_only": True,
        "runner_version": runner.RUNNER_VERSION,
        "prompt_version": runner.PROMPT_VERSION,
        "static_blocks": {
            "system_prompt": measure(prompt_text),
            "response_format": measure(response_format_text),
            "meaning_layer": measure(canonical_json(runner.load(runner.MEANINGS_PATH))),
            "finding_type_meanings": measure(canonical_json(runner.load(runner.FINDING_TYPES_PATH)["finding_types"])),
        },
        "cases": rows,
        "interpretation_guardrail": (
            "Byte counts are deterministic serialized-size measurements, not exact model tokenizer counts. "
            "Only reference_questions are reduced; all other v0.6 semantic and schema blocks remain unchanged."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
