"""Deterministic preparation and evaluation helpers for ZS-KI-B smoke test v0.1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from core.validation.semantic_boundary import validate_semantic_response

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_smoketest_system_v0_1.txt"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]
    finding_types = json.loads(FINDING_TYPES_PATH.read_text(encoding="utf-8"))["finding_types"]
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    target_id = case["target_source_location_id"]
    locations = case["source_locations"]
    target = next(row for row in locations if row["source_location_id"] == target_id)

    compact_questions = [
        {"question_id": row["question_id"], "pf_id": row["pf_id"], "question": row["question"]}
        for row in questions
    ]
    user_payload = {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location": target,
        "allowed_context_source_locations": locations,
        "reference_questions": compact_questions,
        "finding_type_meanings": finding_types,
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": canonical_json(user_payload)},
    ]


def parse_model_json(content: str) -> dict[str, Any]:
    """Fail closed: no fence stripping, repair, coercion or semantic retry."""
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("Modellantwort muss ein JSON-Objekt sein")
    return value


def _failed_boundary_evaluation(
    *,
    boundary_issues: list[Any],
    target_source_match: bool,
    expectations: dict[str, Any],
) -> dict[str, Any]:
    group_results = [
        {"allowed_group": group, "hits": [], "passed": False}
        for group in expectations["required_question_groups"]
    ]
    criteria = {
        "boundary_pass": False,
        "target_source_match": target_source_match,
        "question_groups_pass": False,
        "conflict_candidate_pass": False,
        "gap_or_uncertainty_pass": False,
    }
    return {
        "passed": False,
        "criteria": criteria,
        "boundary_issues": [issue.to_dict() for issue in boundary_issues],
        "question_group_results": group_results,
        "conflict_hits": [],
        "observed_question_ids": [],
        "observed_conflict_refs": [],
        "has_gap_or_uncertainty": False,
    }


def evaluate_smoke(
    response: dict[str, Any],
    *,
    case: dict[str, Any],
    expectations: dict[str, Any],
) -> dict[str, Any]:
    allowed_ids = {row["source_location_id"] for row in case["source_locations"]}
    boundary_issues = validate_semantic_response(
        response,
        allowed_source_location_ids=allowed_ids,
    )
    target_source_match = (
        isinstance(response, dict)
        and response.get("source_location_id") == expectations["target_source_location_id"]
    )

    # Untrusted model containers are never iterated after a boundary failure.
    # This converts structurally invalid but parseable JSON into a deterministic FAIL.
    if boundary_issues:
        return _failed_boundary_evaluation(
            boundary_issues=boundary_issues,
            target_source_match=target_source_match,
            expectations=expectations,
        )

    question_ids: set[str] = set()
    conflict_refs: set[str] = set()
    has_gap_or_uncertainty = False
    proposals = response.get("proposals", [])
    if not isinstance(proposals, list):
        return _failed_boundary_evaluation(
            boundary_issues=boundary_issues,
            target_source_match=target_source_match,
            expectations=expectations,
        )

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        assignments = proposal.get("assignment_candidates", [])
        if isinstance(assignments, list):
            for assignment in assignments:
                if isinstance(assignment, dict) and isinstance(assignment.get("question_id"), str):
                    question_ids.add(assignment["question_id"])
        refs = proposal.get("conflict_candidate_refs", [])
        if isinstance(refs, list):
            conflict_refs.update(ref for ref in refs if isinstance(ref, str))
        has_gap_or_uncertainty = has_gap_or_uncertainty or bool(proposal.get("gap_notes")) or bool(
            proposal.get("uncertainty_notes")
        )

    group_results = []
    for group in expectations["required_question_groups"]:
        hit = sorted(set(group) & question_ids)
        group_results.append({"allowed_group": group, "hits": hit, "passed": bool(hit)})

    conflict_hits = sorted(set(expectations["required_conflict_ref_any"]) & conflict_refs)
    criteria = {
        "boundary_pass": True,
        "target_source_match": target_source_match,
        "question_groups_pass": all(item["passed"] for item in group_results),
        "conflict_candidate_pass": bool(conflict_hits),
        "gap_or_uncertainty_pass": (
            has_gap_or_uncertainty if expectations.get("require_gap_or_uncertainty_note") else True
        ),
    }
    return {
        "passed": all(criteria.values()),
        "criteria": criteria,
        "boundary_issues": [],
        "question_group_results": group_results,
        "conflict_hits": conflict_hits,
        "observed_question_ids": sorted(question_ids),
        "observed_conflict_refs": sorted(conflict_refs),
        "has_gap_or_uncertainty": has_gap_or_uncertainty,
    }
