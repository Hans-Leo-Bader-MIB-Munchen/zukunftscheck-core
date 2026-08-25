"""Deterministic boundary validation for ZS-KI-B semantic proposals v0.1.

This module validates only the formal boundary between a future semantic adapter
and the already existing deterministic ZS-KI-B core. It performs no semantic or
fachliche inference and makes no approval, status or stage decision.
"""
from __future__ import annotations

from typing import Any, Iterable

from .validator import CODELISTS, QUESTION_TO_PF, ValidationIssue

CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1"

TOP_LEVEL_KEYS = {"contract_version", "source_location_id", "proposals"}
PROPOSAL_KEYS = {
    "proposal_id",
    "normalized_statement",
    "finding_type_candidate",
    "evidence_relation_type_candidate",
    "derivation_note",
    "assignment_candidates",
    "conflict_candidate_refs",
    "gap_notes",
    "uncertainty_notes",
    "human_review_required",
}
ASSIGNMENT_KEYS = {
    "question_id",
    "pf_id",
    "assignment_confidence",
    "human_review_required",
}

# These keys are deliberately outside the semantic model's authority. Their
# appearance anywhere in a model response is rejected fail-closed.
FORBIDDEN_MODEL_FIELDS = {
    "question_status",
    "conflict_status",
    "human_content_confirmation",
    "human_decision_id",
    "actor_type",
    "decision_scope",
    "decision_value",
    "governance_approval",
    "governance_approval_state",
    "approval_state",
    "original_text",
    "run_manifest",
    "final_result",
    "stage",
    "stage_open",
    "stage1_open",
    "stage2_open",
}


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_keys(nested)


def validate_semantic_response(
    response: dict[str, Any],
    *,
    allowed_source_location_ids: set[str],
) -> list[ValidationIssue]:
    """Validate B-SV001..B-SV020 without performing semantic inference."""
    issues: list[ValidationIssue] = []

    def add(code: str, rule: str, obj: str, rid: str | None, msg: str) -> None:
        issues.append(ValidationIssue(code, rule, obj, rid, msg))

    if not isinstance(response, dict):
        add("INVALID_SEMANTIC_RESPONSE", "B-SV001", "SemanticResponse", None,
            "response muss ein Objekt sein")
        return issues

    # B-SV001 / B-SV003 / B-SV014: exact contract and authority boundary.
    if response.get("contract_version") != CONTRACT_VERSION:
        add("SEMANTIC_CONTRACT_VERSION_MISMATCH", "B-SV001", "SemanticResponse", None,
            f"contract_version muss {CONTRACT_VERSION} sein")

    extra_top = set(response) - TOP_LEVEL_KEYS
    if extra_top:
        add("SEMANTIC_TOP_LEVEL_FIELD_FORBIDDEN", "B-SV003", "SemanticResponse", None,
            f"unzulässige Top-Level-Felder: {sorted(extra_top)}")

    forbidden = sorted(set(_walk_keys(response)) & FORBIDDEN_MODEL_FIELDS)
    if forbidden:
        add("MODEL_AUTHORITY_VIOLATION", "B-SV014", "SemanticResponse", None,
            f"Modellausgabe enthält geschützte Felder: {forbidden}")

    # B-SV002: only a caller-provided immutable source-location context may be referenced.
    source_location_id = response.get("source_location_id")
    if not isinstance(source_location_id, str) or not source_location_id.strip():
        add("MISSING_SOURCE_LOCATION_REF", "B-SV002", "SemanticResponse", None,
            "source_location_id fehlt oder ist leer")
    elif source_location_id not in allowed_source_location_ids:
        add("UNKNOWN_SOURCE_LOCATION_REF", "B-SV002", "SemanticResponse", source_location_id,
            "source_location_id ist nicht im deterministisch bereitgestellten Kontext")

    proposals = response.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        add("MISSING_SEMANTIC_PROPOSALS", "B-SV004", "SemanticResponse", None,
            "proposals muss eine nichtleere Liste sein")
        return issues

    seen_proposal_ids: set[str] = set()
    for proposal in proposals:
        if not isinstance(proposal, dict):
            add("INVALID_PROPOSAL", "B-SV004", "SemanticProposal", None,
                "jeder proposal-Eintrag muss ein Objekt sein")
            continue

        proposal_id = proposal.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            add("MISSING_PROPOSAL_ID", "B-SV004", "SemanticProposal", None,
                "proposal_id fehlt oder ist leer")
            proposal_id = None
        elif proposal_id in seen_proposal_ids:
            add("DUPLICATE_PROPOSAL_ID", "B-SV004", "SemanticProposal", proposal_id,
                "proposal_id ist doppelt")
        else:
            seen_proposal_ids.add(proposal_id)

        extra_proposal = set(proposal) - PROPOSAL_KEYS
        if extra_proposal:
            add("PROPOSAL_FIELD_FORBIDDEN", "B-SV005", "SemanticProposal", proposal_id,
                f"unzulässige Proposal-Felder: {sorted(extra_proposal)}")

        statement = proposal.get("normalized_statement")
        if not isinstance(statement, str) or not statement.strip():
            add("MISSING_NORMALIZED_STATEMENT", "B-SV006", "SemanticProposal", proposal_id,
                "normalized_statement fehlt oder ist leer")

        finding_type = proposal.get("finding_type_candidate")
        if finding_type not in CODELISTS["finding_type"]:
            add("INVALID_FINDING_TYPE_CANDIDATE", "B-SV007", "SemanticProposal", proposal_id,
                "finding_type_candidate ist nicht in der bestehenden Feststellungsarten-Codeliste")

        relation_type = proposal.get("evidence_relation_type_candidate")
        if relation_type not in CODELISTS["evidence_relation_type"]:
            add("INVALID_EVIDENCE_RELATION_CANDIDATE", "B-SV008", "SemanticProposal", proposal_id,
                "evidence_relation_type_candidate ist unzulässig")
        if relation_type == "DERIVED" and not str(proposal.get("derivation_note") or "").strip():
            add("MISSING_DERIVATION_PATH", "B-SV009", "SemanticProposal", proposal_id,
                "DERIVED benötigt derivation_note")

        for list_field, rule in (
            ("conflict_candidate_refs", "B-SV015"),
            ("gap_notes", "B-SV016"),
            ("uncertainty_notes", "B-SV017"),
        ):
            value = proposal.get(list_field)
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                add("INVALID_CANDIDATE_NOTE_LIST", rule, "SemanticProposal", proposal_id,
                    f"{list_field} muss eine Liste nichtleerer Strings sein")

        proposal_review = proposal.get("human_review_required")
        if not isinstance(proposal_review, bool):
            add("INVALID_REVIEW_FLAG", "B-SV018", "SemanticProposal", proposal_id,
                "human_review_required muss boolean sein")

        assignments = proposal.get("assignment_candidates")
        if not isinstance(assignments, list):
            add("INVALID_ASSIGNMENT_CANDIDATES", "B-SV010", "SemanticProposal", proposal_id,
                "assignment_candidates muss eine Liste sein")
            continue

        seen_assignments: set[tuple[str, str]] = set()
        for assignment in assignments:
            if not isinstance(assignment, dict):
                add("INVALID_ASSIGNMENT_CANDIDATE", "B-SV010", "AssignmentCandidate", proposal_id,
                    "Assignment-Kandidat muss ein Objekt sein")
                continue

            extra_assignment = set(assignment) - ASSIGNMENT_KEYS
            if extra_assignment:
                add("ASSIGNMENT_FIELD_FORBIDDEN", "B-SV010", "AssignmentCandidate", proposal_id,
                    f"unzulässige Assignment-Felder: {sorted(extra_assignment)}")

            question_id = assignment.get("question_id")
            pf_id = assignment.get("pf_id")
            pair = (str(question_id), str(pf_id))
            if pair in seen_assignments:
                add("DUPLICATE_ASSIGNMENT_CANDIDATE", "B-SV011", "AssignmentCandidate", proposal_id,
                    "gleiche question_id/pf_id-Kombination mehrfach vorgeschlagen")
            else:
                seen_assignments.add(pair)

            if question_id not in QUESTION_TO_PF:
                add("UNKNOWN_QUESTION_ID", "B-SV011", "AssignmentCandidate", proposal_id,
                    "question_id ist nicht im eingefrorenen 67er-Snapshot")
            elif pf_id != QUESTION_TO_PF[question_id]:
                add("PF_QUESTION_MISMATCH", "B-SV012", "AssignmentCandidate", proposal_id,
                    "pf_id passt nicht zur question_id")

            confidence = assignment.get("assignment_confidence")
            if confidence not in CODELISTS["assignment_confidence"]:
                add("INVALID_ASSIGNMENT_CONFIDENCE", "B-SV013", "AssignmentCandidate", proposal_id,
                    "assignment_confidence ist unzulässig")

            assignment_review = assignment.get("human_review_required")
            if not isinstance(assignment_review, bool):
                add("INVALID_REVIEW_FLAG", "B-SV018", "AssignmentCandidate", proposal_id,
                    "human_review_required muss boolean sein")
            elif confidence == "UNCERTAIN" and assignment_review is not True:
                add("MISSING_REVIEW_FLAG", "B-SV019", "AssignmentCandidate", proposal_id,
                    "UNCERTAIN erfordert human_review_required=true")

        # Candidate conflicts, gaps or uncertainties can never be self-confirming.
        has_review_trigger = any([
            bool(proposal.get("conflict_candidate_refs")),
            bool(proposal.get("gap_notes")),
            bool(proposal.get("uncertainty_notes")),
            any(
                isinstance(a, dict) and a.get("assignment_confidence") == "UNCERTAIN"
                for a in assignments
            ),
        ])
        if has_review_trigger and proposal_review is not True:
            add("MISSING_PROPOSAL_REVIEW_FLAG", "B-SV020", "SemanticProposal", proposal_id,
                "Konflikt-, Lücken- oder Unsicherheitskandidaten erfordern human_review_required=true")

    return issues


def semantic_response_is_valid(
    response: dict[str, Any],
    *,
    allowed_source_location_ids: set[str],
) -> bool:
    return not validate_semantic_response(
        response,
        allowed_source_location_ids=allowed_source_location_ids,
    )
