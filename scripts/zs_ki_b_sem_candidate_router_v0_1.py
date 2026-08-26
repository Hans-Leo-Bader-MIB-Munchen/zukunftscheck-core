#!/usr/bin/env python3
"""Conservative model-free candidate-router prototype for ZS-KI-B SEM.

Purpose:
- reduce reference-question payload only when deterministic lexical evidence is
  sufficiently clear and supported by the existing calibrated meaning layer;
- fail closed to the complete 67-question set when evidence is weak, broad or
  points outside the calibrated PF neighborhood;
- perform no model call and use no Human-Gold labels.

This is a diagnostic prototype, not a production routing policy and not an
independent qualification benchmark. Known R16/R18/R21/R22 cases are used only
as regression/control inputs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_question_meanings_v0_2.json"
CASE_PATHS = [
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r16_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r18_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r21_syn_v0_1.json",
    ROOT / "tests" / "fixtures" / "zs_ki_b_sem_r22_syn_v0_1.json",
]

STOPWORDS = {
    "aber", "alle", "als", "auch", "auf", "aus", "bei", "beim", "bereits", "der", "die", "das",
    "dem", "den", "des", "ein", "eine", "einer", "eines", "einem", "einen", "für", "gegen", "gibt",
    "im", "in", "ist", "mit", "nach", "nicht", "noch", "nur", "oder", "sind", "soll", "und", "von",
    "vor", "welche", "welcher", "welches", "wer", "wie", "wird", "zu", "zum", "zur", "zwischen",
    "bestehen", "besteht", "liegen", "liegt", "vorhanden", "erforderlich", "konkret", "dokumentiert",
}

# Conservative thresholds. These are generic lexical thresholds, not case-specific rules.
MIN_SCORE = 2
MAX_SELECTED_QUESTIONS = 18
MIN_TOKEN_LENGTH = 4


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text.lower()))
    return {token for token in tokens if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS}


def source_text(case: dict[str, Any]) -> str:
    rows = case["source_locations"]
    parts: list[str] = []
    for row in rows:
        parts.extend(
            [
                str(row.get("section_or_heading") or ""),
                str(row.get("page_reference") or ""),
                str(row.get("original_text") or ""),
            ]
        )
    return " ".join(parts)


def meaning_text_by_question(meanings_doc: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in meanings_doc.get("meanings", []):
        result[row["question_id"]] = " ".join(
            [
                str(row.get("positive_scope") or ""),
                str(row.get("negative_scope") or ""),
                str(row.get("disambiguation_notes") or ""),
            ]
        )
    return result


def route(case: dict[str, Any], questions: list[dict[str, Any]], meanings_doc: dict[str, Any]) -> dict[str, Any]:
    src_tokens = tokenize(source_text(case))
    meaning_texts = meaning_text_by_question(meanings_doc)
    calibrated_ids = set(meaning_texts)

    scored: list[dict[str, Any]] = []
    for row in questions:
        question_tokens = tokenize(str(row["question"]))
        meaning_tokens = tokenize(meaning_texts.get(row["question_id"], ""))
        direct_overlap = sorted(src_tokens & question_tokens)
        meaning_overlap = sorted(src_tokens & meaning_tokens)
        # Direct question-text overlap counts twice; meaning-layer overlap counts once.
        score = 2 * len(direct_overlap) + len(meaning_overlap)
        if score > 0:
            scored.append(
                {
                    "question_id": row["question_id"],
                    "pf_id": row["pf_id"],
                    "score": score,
                    "direct_overlap": direct_overlap,
                    "meaning_overlap": meaning_overlap,
                    "meaning_backed": bool(meaning_overlap) and row["question_id"] in calibrated_ids,
                }
            )

    scored.sort(key=lambda item: (-item["score"], item["question_id"]))
    strong = [item for item in scored if item["score"] >= MIN_SCORE]
    meaning_backed = [item for item in strong if item["meaning_backed"]]
    lexical_only = [item for item in strong if not item["meaning_backed"]]

    fallback_reasons: list[str] = []
    if not strong:
        fallback_reasons.append("no_candidate_meets_min_score")
    if len(strong) > MAX_SELECTED_QUESTIONS:
        fallback_reasons.append("candidate_set_too_broad")
    if strong and not meaning_backed:
        fallback_reasons.append("no_meaning_backed_candidate")

    meaning_backed_pfs = {item["pf_id"] for item in meaning_backed}
    lexical_only_external_pfs = sorted({item["pf_id"] for item in lexical_only if item["pf_id"] not in meaning_backed_pfs})
    if lexical_only_external_pfs:
        fallback_reasons.append("lexical_only_candidate_outside_meaning_backed_pf")

    if fallback_reasons:
        selected_ids = [row["question_id"] for row in questions]
        mode = "FULL_67_FAIL_CLOSED"
    else:
        # Reduction is anchored only in PFs that have at least one calibrated
        # meaning-layer overlap. Lexical-only evidence may support a PF already
        # anchored this way, but may never introduce a new PF on its own.
        selected_ids = [row["question_id"] for row in questions if row["pf_id"] in meaning_backed_pfs]
        if len(selected_ids) > MAX_SELECTED_QUESTIONS:
            selected_ids = [row["question_id"] for row in questions]
            fallback_reasons.append("pf_expansion_exceeds_max_selected_questions")
            mode = "FULL_67_FAIL_CLOSED"
        else:
            mode = "REDUCED_MEANING_BACKED_PF_EXPANDED"

    return {
        "case_id": case["case_id"],
        "mode": mode,
        "source_tokens": sorted(src_tokens),
        "strong_candidates": strong,
        "meaning_backed_candidates": meaning_backed,
        "lexical_only_strong_candidates": lexical_only,
        "selected_question_count": len(selected_ids),
        "selected_question_ids": selected_ids,
        "fallback_reasons": fallback_reasons,
    }


def main() -> int:
    questions = load(QUESTIONS_PATH)["questions"]
    meanings_doc = load(MEANINGS_PATH)
    cases = [load(path) for path in CASE_PATHS]

    results = [route(case, questions, meanings_doc) for case in cases]
    output = {
        "mode": "MODEL_FREE_CONSERVATIVE_SEM_CANDIDATE_ROUTER_V0_1",
        "model_contact": False,
        "network_contact": False,
        "human_gold_used": False,
        "qualification_claim": False,
        "production_routing_claim": False,
        "question_count_full": len(questions),
        "thresholds": {
            "min_score": MIN_SCORE,
            "max_selected_questions": MAX_SELECTED_QUESTIONS,
            "min_token_length": MIN_TOKEN_LENGTH,
        },
        "cases": results,
        "guardrail": (
            "Reduced routing requires at least one calibrated meaning-layer overlap per selected PF. "
            "Lexical-only evidence may not introduce an additional PF. Weak, empty, broad or cross-PF ambiguous "
            "evidence fails closed to all 67 questions. This prototype must not be treated as production routing "
            "or independent semantic qualification without holdout validation."
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
