from __future__ import annotations

from copy import deepcopy
from typing import Any

AUDIT_VERSION = "semantic-completeness-audit-v0.2"
PF2_REQUIRED_SCOPE_ASSIGNMENTS = (("2.1", "PF2"), ("2.2", "PF2"))
PF2_SCOPE_MARKERS = (
    "ausschließlich",
    "einschließlich",
    "ausgenommen",
    "mit ausnahme",
    "nur",
)
PF2_SCOPE_CONTEXT_TERMS = (
    "betrachtet",
    "rathaus",
    "vorplatz",
    "gebäude",
    "grundstück",
    "liegenschaft",
    "bereich",
    "fläche",
    "standort",
    "parkplatz",
)


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
    """Fail closed on explicit PF2 scope language when required PF2 dimensions are missing.

    v0.2 remains deterministic and model-free. It does not infer or add assignments.
    It only raises a human-review stop when explicit scope language occurs in a PF2-like
    spatial/object context and one or more predeclared required PF2 assignments are absent.
    """
    original_snapshot = deepcopy(model_response)
    normalized_text = source_text.casefold() if isinstance(source_text, str) else ""
    matched_markers = [
        marker for marker in PF2_SCOPE_MARKERS if marker.casefold() in normalized_text
    ]
    matched_context_terms = [
        term for term in PF2_SCOPE_CONTEXT_TERMS if term.casefold() in normalized_text
    ]
    assignments = _assignment_pairs(model_response)

    required = set(PF2_REQUIRED_SCOPE_ASSIGNMENTS)
    missing_required = sorted(required - assignments)
    pf2_scope_context_detected = bool(matched_markers and matched_context_terms)
    possible_omission = bool(pf2_scope_context_detected and missing_required)

    if model_response != original_snapshot:
        raise RuntimeError("semantic completeness audit must not mutate model output")

    return {
        "audit_version": AUDIT_VERSION,
        "scope": "PF2_EXPLICIT_SCOPE_MARKERS_WITH_CONTEXT",
        "matched_markers": matched_markers,
        "matched_context_terms": matched_context_terms,
        "pf2_scope_context_detected": pf2_scope_context_detected,
        "required_assignments": [list(pair) for pair in PF2_REQUIRED_SCOPE_ASSIGNMENTS],
        "observed_assignments": sorted([list(pair) for pair in assignments]),
        "missing_required_assignments": [list(pair) for pair in missing_required],
        "possible_multi_assignment_omission": possible_omission,
        "human_review_required": possible_omission,
        "stop_automatic_downstream_use": possible_omission,
        "auto_assignment_performed": False,
        "model_output_mutated": False,
        "candidate_missing_dimension": "PF2_SCOPE_MEMBERSHIP_OR_EXCLUSION" if possible_omission else None,
        "candidate_question_id": None,
        "decision_authority": "NONE",
    }
