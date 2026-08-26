#!/usr/bin/env python3
"""Model-free coverage matrix for reference-question meaning calibration.

Reads the authoritative reference-question catalog and the currently leading meaning
layer. It does not create or infer new meanings and performs no model/network contact.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_2.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    question_doc = load(QUESTIONS)
    meaning_doc = load(MEANINGS)

    questions = question_doc["questions"]
    meanings = meaning_doc["meanings"]
    meanings_by_id = {row["question_id"]: row for row in meanings}
    calibrated_by_pf: dict[str, list[str]] = {}
    for row in meanings:
        calibrated_by_pf.setdefault(row["pf_id"], []).append(row["question_id"])

    matrix = []
    for row in questions:
        qid = row["question_id"]
        pf_id = row["pf_id"]
        calibrated = qid in meanings_by_id
        same_pf_calibrated = sorted(calibrated_by_pf.get(pf_id, []))

        if calibrated:
            primary_status = "CALIBRATED_EXISTING"
        elif same_pf_calibrated:
            primary_status = "NEIGHBORHOOD_REVIEW_REQUIRED"
        else:
            primary_status = "UNCALIBRATED"

        matrix.append({
            "question_id": qid,
            "pf_id": pf_id,
            "question": row["question"],
            "primary_status": primary_status,
            "existing_meaning": calibrated,
            "same_pf_calibrated_question_ids": same_pf_calibrated,
            "cross_pf_disambiguation_required": False,
            "cross_pf_disambiguation_basis": "NOT_ASSESSED_IN_V0_1",
        })

    counts: dict[str, int] = {}
    for row in matrix:
        counts[row["primary_status"]] = counts.get(row["primary_status"], 0) + 1

    result = {
        "mode": "MODEL_FREE_SEM_MEANING_COVERAGE_MATRIX_V0_1",
        "model_contact": False,
        "network_contact": False,
        "new_meanings_created": False,
        "question_count": len(questions),
        "existing_meaning_count": len(meanings),
        "status_counts": counts,
        "matrix": matrix,
        "guardrail": (
            "NEIGHBORHOOD_REVIEW_REQUIRED only means that an uncalibrated question shares a PF "
            "with at least one already calibrated question. CROSS-PF disambiguation is deliberately "
            "not inferred in v0.1 and remains NOT_ASSESSED."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
