#!/usr/bin/env python3
"""Model-free payload profiler for the SEM v0.6 regression/control request.

This script performs no model, network, tool, web, MCP, remote or cloud call.
It measures serialized payload sizes for the current full request and for a
strictly diagnostic calibrated-scope variant containing only question_ids that
already exist in reference_question_meanings_v0_2.json.

The calibrated-scope variant is NOT a qualification runner and NOT a production
routing policy. The known R16/R18/R21/R22 cases remain regression/control only.
No Human-Gold labels are read or encoded here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_4.txt"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_question_meanings_v0_2.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
CASE_PATHS = [
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r16_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r18_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r21_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r22_syn_v0_1.json",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def metric(value: str) -> dict[str, int]:
    return {"chars": len(value), "utf8_bytes": len(value.encode("utf-8"))}


def build_user_payload(
    case: dict[str, Any],
    questions: list[dict[str, Any]],
    meanings: dict[str, Any],
    finding_types: dict[str, Any],
) -> dict[str, Any]:
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


def main() -> int:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    questions_doc = load(QUESTIONS_PATH)
    meanings_doc = load(MEANINGS_PATH)
    finding_types = load(FINDING_TYPES_PATH)["finding_types"]
    cases = [load(path) for path in CASE_PATHS]

    all_questions = questions_doc["questions"]
    calibrated_ids = [row["question_id"] for row in meanings_doc["meanings"]]
    calibrated_id_set = set(calibrated_ids)
    calibrated_questions = [row for row in all_questions if row["question_id"] in calibrated_id_set]

    if len(calibrated_questions) != len(calibrated_ids):
        raise RuntimeError("Meaning-layer question_ids do not resolve uniquely against reference questions")

    static_blocks = {
        "system_prompt": metric(prompt),
        "reference_questions_full": metric(canonical_json(all_questions)),
        "reference_questions_calibrated_scope": metric(canonical_json(calibrated_questions)),
        "meaning_layer_v0_2": metric(canonical_json(meanings_doc)),
        "finding_type_meanings": metric(canonical_json(finding_types)),
    }

    rows = []
    for case in cases:
        full_payload = build_user_payload(case, all_questions, meanings_doc, finding_types)
        calibrated_payload = build_user_payload(case, calibrated_questions, meanings_doc, finding_types)
        full_serialized = canonical_json(full_payload)
        calibrated_serialized = canonical_json(calibrated_payload)
        reduction = 1.0 - (len(calibrated_serialized.encode("utf-8")) / len(full_serialized.encode("utf-8")))
        rows.append(
            {
                "case_id": case["case_id"],
                "source_location_count": len(case["source_locations"]),
                "full_user_payload": metric(full_serialized),
                "calibrated_scope_user_payload": metric(calibrated_serialized),
                "utf8_byte_reduction_percent": round(reduction * 100.0, 2),
            }
        )

    result = {
        "mode": "MODEL_FREE_SEM_PAYLOAD_PROFILE_V0_1",
        "model_contact": False,
        "network_contact": False,
        "human_gold_used": False,
        "qualification_claim": False,
        "production_routing_claim": False,
        "reference_question_count_full": len(all_questions),
        "reference_question_count_calibrated_scope": len(calibrated_questions),
        "calibrated_scope_question_ids": calibrated_ids,
        "static_blocks": static_blocks,
        "cases": rows,
        "interpretation_guardrail": (
            "The calibrated-scope profile is only a payload-size upper-bound experiment for the already-calibrated "
            "R16/R18/R21/R22 neighborhood. It must not be used as an independent qualification benchmark or as a "
            "general production router without a separately specified deterministic routing rule and independent holdout validation."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
