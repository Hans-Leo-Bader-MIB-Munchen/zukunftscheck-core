#!/usr/bin/env python3
"""Model-free PF router prototype for a two-stage SEM payload.

Stage A chooses PF groups deterministically from aggregate reference-question
vocabulary plus an explicit PF-level routing-semantics table. Stage B (not
implemented here) would expose all questions from the selected PF groups to the
semantic model.

Guardrails:
- no model/network/tool call;
- no dependency on prior R16/R18/R21/R22 labels;
- no case-specific routing rules;
- if routing evidence is weak, broad, tied, or contains relevant semantic
  evidence below the selection threshold, fail closed to all PFs/all 67 questions;
- no production or qualification claim.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
PF_SEMANTICS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "pf_routing_semantics_v0_1.json"
HOLDOUT_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_pf_router_holdout_v0_1.json"

MIN_TOKEN_LENGTH = 4
MIN_PF_SCORE = 3
MAX_SELECTED_PFS = 3
MIN_MARGIN = 1
QUESTION_TOKEN_WEIGHT = 1
SEMANTIC_TOKEN_WEIGHT = 2
SEMANTIC_PHRASE_WEIGHT = 3

STOPWORDS = {
    "aber", "alle", "als", "auch", "auf", "aus", "bei", "beim", "bereits", "der", "die", "das",
    "dem", "den", "des", "ein", "eine", "einer", "eines", "einem", "einen", "für", "gegen", "gibt",
    "im", "in", "ist", "mit", "nach", "nicht", "noch", "nur", "oder", "sind", "soll", "und", "von",
    "vor", "welche", "welcher", "welches", "wer", "wie", "wird", "zu", "zum", "zur", "zwischen",
    "bestehen", "besteht", "liegen", "liegt", "vorhanden", "erforderlich", "konkret", "dokumentiert",
    "frage", "fragen", "welchen", "welchem", "welcher", "welches", "welche"
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text.lower()))


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text.lower()))
    return {token for token in tokens if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS}


def build_pf_profiles(questions: list[dict[str, Any]]) -> dict[str, set[str]]:
    profiles: dict[str, set[str]] = defaultdict(set)
    for row in questions:
        profiles[row["pf_id"]].update(tokenize(row["question"]))
    return dict(profiles)


def load_pf_semantics() -> dict[str, dict[str, Any]]:
    doc = load(PF_SEMANTICS_PATH)
    result: dict[str, dict[str, Any]] = {}
    for row in doc["pf_semantics"]:
        pf = row["pf_id"]
        if pf in result:
            raise RuntimeError(f"duplicate PF semantics: {pf}")
        result[pf] = {
            "tokens": set(str(token).lower() for token in row.get("tokens", [])),
            "phrases": [normalize(str(phrase)) for phrase in row.get("phrases", [])],
        }
    return result


def questions_by_pf(questions: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for row in questions:
        result[row["pf_id"]].append(row["question_id"])
    return dict(result)


def route_text(text: str, questions: list[dict[str, Any]], pf_semantics: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    src = tokenize(text)
    normalized = normalize(text)
    profiles = build_pf_profiles(questions)
    grouped = questions_by_pf(questions)
    semantics = pf_semantics if pf_semantics is not None else load_pf_semantics()
    pf_order = sorted(grouped, key=lambda pf: int(pf[2:]))

    if set(semantics) != set(pf_order):
        raise RuntimeError("PF routing semantics must cover exactly all PF groups")

    scored = []
    for pf in pf_order:
        question_overlap = sorted(src & profiles[pf])
        semantic_token_overlap = sorted(src & semantics[pf]["tokens"])
        semantic_phrase_overlap = sorted(
            phrase for phrase in semantics[pf]["phrases"] if phrase and phrase in normalized
        )
        score = (
            QUESTION_TOKEN_WEIGHT * len(question_overlap)
            + SEMANTIC_TOKEN_WEIGHT * len(semantic_token_overlap)
            + SEMANTIC_PHRASE_WEIGHT * len(semantic_phrase_overlap)
        )
        scored.append({
            "pf_id": pf,
            "score": score,
            "question_overlap": question_overlap,
            "semantic_token_overlap": semantic_token_overlap,
            "semantic_phrase_overlap": semantic_phrase_overlap,
        })
    scored.sort(key=lambda row: (-row["score"], int(row["pf_id"][2:])))

    strong = [row for row in scored if row["score"] >= MIN_PF_SCORE]
    strong_ids = {row["pf_id"] for row in strong}
    fallback: list[str] = []
    if not strong:
        fallback.append("no_pf_meets_min_score")
    if len(strong) > MAX_SELECTED_PFS:
        fallback.append("too_many_strong_pfs")

    # A semantic phrase, or at least two explicit semantic-token matches, is
    # material evidence even when the aggregate score stays below MIN_PF_SCORE.
    # Such evidence may not be silently discarded by a reduced route.
    below_threshold_semantic = [
        row for row in scored
        if row["pf_id"] not in strong_ids
        and (row["semantic_phrase_overlap"] or len(row["semantic_token_overlap"]) >= 2)
    ]
    if below_threshold_semantic:
        fallback.append("semantic_evidence_below_selection_threshold")

    if strong:
        cutoff = strong[-1]["score"]
        next_score = next((row["score"] for row in scored if row["pf_id"] not in strong_ids), 0)
        if cutoff - next_score < MIN_MARGIN and next_score > 0:
            fallback.append("insufficient_score_margin")

    if fallback:
        selected_pfs = pf_order
        selected_question_ids = [row["question_id"] for row in questions]
        mode = "FULL_FAIL_CLOSED"
    else:
        selected_pfs = [row["pf_id"] for row in strong]
        selected_question_ids = [qid for pf in selected_pfs for qid in grouped[pf]]
        mode = "REDUCED_PF_STAGE_A"

    return {
        "mode": mode,
        "source_tokens": sorted(src),
        "pf_scores": scored,
        "below_threshold_semantic_evidence": below_threshold_semantic,
        "selected_pf_ids": selected_pfs,
        "selected_pf_count": len(selected_pfs),
        "selected_question_ids": selected_question_ids,
        "selected_question_count": len(selected_question_ids),
        "fallback_reasons": fallback,
    }


def main() -> int:
    questions = load(QUESTIONS_PATH)["questions"]
    semantics = load_pf_semantics()
    holdouts = load(HOLDOUT_PATH)["cases"]
    rows = []
    for case in holdouts:
        routed = route_text(case["text"], questions, semantics)
        rows.append({
            "case_id": case["case_id"],
            "expected_pf_ids": case["expected_pf_ids"],
            **routed,
        })
    result = {
        "mode": "MODEL_FREE_TWO_STAGE_PF_ROUTER_V0_1",
        "model_contact": False,
        "network_contact": False,
        "qualification_claim": False,
        "production_routing_claim": False,
        "pf_routing_semantics_version": "v0.1",
        "thresholds": {
            "min_pf_score": MIN_PF_SCORE,
            "max_selected_pfs": MAX_SELECTED_PFS,
            "min_margin": MIN_MARGIN,
            "min_token_length": MIN_TOKEN_LENGTH,
            "question_token_weight": QUESTION_TOKEN_WEIGHT,
            "semantic_token_weight": SEMANTIC_TOKEN_WEIGHT,
            "semantic_phrase_weight": SEMANTIC_PHRASE_WEIGHT,
        },
        "holdout_cases": rows,
        "guardrail": "Stage A only limits PF groups when deterministic PF-level lexical/phrase evidence is strong and bounded and no material semantic evidence is left below threshold; otherwise all 12 PFs/all 67 questions are retained. Stage B is not executed here."
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
