from __future__ import annotations

from copy import deepcopy
from typing import Any

AUDIT_VERSION = "semantic-completeness-audit-v0.1"
PF2_SCOPE_MARKERS = ("ausschließlich", "einschließlich", "ausgenommen")


def _assignment_pairs(model_response: dict[str, Any]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    proposals = model_response.get("proposals")
    if not isinstance(proposals, list):
        return pairs
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        assignments = proposal.get("assignment_candidates")
        if not isinstance(assignments, list):
            continue
        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue
            question_id = assignment.get("question_id")
            pf_id = assignment.get("pf_id")
            if isinstance(question_id, str) and isinstance(pf_id, str):
                pairs.add((question_id, pf_id))
    return pairs


def audit_pf2_scope_completeness(*, source_text: str, model_response: dict[str, Any]) -> dict[str, Any]:
    """Flag possible PF2 multi-assignment omission without changing model output.

    Narrow v0.1 prototype:
    - deterministic and model-free;
    - only evaluates explicit PF2 inclusion/exclusion markers;
    - only activates when the model already proposed at least one PF2 assignment;
    - never adds, removes, rewrites or infers an assignment candidate.
    """
    original_snapshot = deepcopy(model_response)
    normalized_text = source_text.casefold() if isinstance(source_text, str) else ""
    matched_markers = [marker for marker in PF2_SCOPE_MARKERS if marker in normalized_text]
    assignments = _assignment_pairs(model_response)
    has_pf2_assignment = any(pf_id == "PF2" for _, pf_id in assignments)
    has_22 = ("2.2", "PF2") in assignments

    possible_omission = bool(matched_markers and has_pf2_assignment and not has_22)

    if model_response != original_snapshot:
        raise RuntimeError("semantic completeness audit must not mutate model output")

    return {
        "audit_version": AUDIT_VERSION,
        "scope": "PF2_EXPLICIT_SCOPE_MARKERS_ONLY",
        "matched_markers": matched_markers,
        "observed_assignments": sorted([list(pair) for pair in assignments]),
        "possible_multi_assignment_omission": possible_omission,
        "human_review_required": possible_omission,
        "stop_automatic_downstream_use": possible_omission,
        "auto_assignment_performed": False,
        "model_output_mutated": False,
        "candidate_missing_dimension": "PF2_SCOPE_MEMBERSHIP_OR_EXCLUSION" if possible_omission else None,
        "candidate_question_id": None,
        "decision_authority": "NONE",
    }
