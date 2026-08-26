"""Deterministic boundary validation for ZS-KI-B semantic proposals v0.2.

This version adds formal proposal-level provenance and target-coverage checks.
It performs no semantic or fachliche conflict inference and grants no additional
authority to the model.
"""
from __future__ import annotations

import copy
from typing import Any

from core.validation.semantic_boundary import validate_semantic_response as validate_semantic_response_v0_1
from core.validation.validator import ValidationIssue

CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"


def _issue(code: str, rule: str, obj: str, rid: str | None, message: str) -> ValidationIssue:
    return ValidationIssue(code, rule, obj, rid, message)


def validate_semantic_response_v0_2(
    response: dict[str, Any],
    *,
    allowed_source_location_ids: set[str],
    target_source_location_id: str,
) -> list[ValidationIssue]:
    """Validate v0.2 formal invariants without semantic inference."""
    issues: list[ValidationIssue] = []

    if not isinstance(response, dict):
        return [_issue("INVALID_SEMANTIC_RESPONSE", "B-SV001", "SemanticResponse", None, "response muss ein Objekt sein")]

    if response.get("contract_version") != CONTRACT_VERSION:
        issues.append(_issue(
            "SEMANTIC_CONTRACT_VERSION_MISMATCH",
            "B-SV001",
            "SemanticResponse",
            None,
            f"contract_version muss {CONTRACT_VERSION} sein",
        ))

    # Reuse the mature v0.1 checks by validating a normalized compatibility view.
    compatibility = copy.deepcopy(response)
    compatibility["contract_version"] = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1"
    proposals = compatibility.get("proposals")
    if isinstance(proposals, list):
        for proposal in proposals:
            if isinstance(proposal, dict):
                proposal.pop("source_location_id", None)
    issues.extend(validate_semantic_response_v0_1(
        compatibility,
        allowed_source_location_ids=allowed_source_location_ids,
    ))

    top_level = response.get("source_location_id")
    if top_level != target_source_location_id:
        issues.append(_issue(
            "TARGET_SOURCE_LOCATION_MISMATCH",
            "B-SV021",
            "SemanticResponse",
            str(top_level) if top_level is not None else None,
            "top-level source_location_id muss dem deterministisch vorgegebenen target_source_location_id entsprechen",
        ))

    original_proposals = response.get("proposals")
    proposal_source_ids: list[str] = []
    if isinstance(original_proposals, list):
        for proposal in original_proposals:
            if not isinstance(proposal, dict):
                continue
            proposal_id = proposal.get("proposal_id")
            source_id = proposal.get("source_location_id")
            if not isinstance(source_id, str) or not source_id.strip():
                issues.append(_issue(
                    "MISSING_PROPOSAL_SOURCE_LOCATION_REF",
                    "B-SV022",
                    "SemanticProposal",
                    proposal_id if isinstance(proposal_id, str) else None,
                    "proposal.source_location_id fehlt oder ist leer",
                ))
                continue
            proposal_source_ids.append(source_id)
            if source_id not in allowed_source_location_ids:
                issues.append(_issue(
                    "UNKNOWN_PROPOSAL_SOURCE_LOCATION_REF",
                    "B-SV022",
                    "SemanticProposal",
                    proposal_id if isinstance(proposal_id, str) else None,
                    "proposal.source_location_id ist nicht im deterministisch bereitgestellten Kontext",
                ))

    if isinstance(original_proposals, list) and original_proposals and target_source_location_id not in proposal_source_ids:
        issues.append(_issue(
            "TARGET_SOURCE_LOCATION_NOT_COVERED",
            "B-SV023",
            "SemanticResponse",
            target_source_location_id,
            "mindestens ein Proposal muss die top-level Target-SourceLocation referenzieren",
        ))

    # Single-source cases are intentionally strict: every proposal provenance must
    # point to the sole allowed source and therefore equal the target anchor.
    if len(allowed_source_location_ids) == 1:
        sole = next(iter(allowed_source_location_ids))
        for source_id in proposal_source_ids:
            if source_id != sole:
                issues.append(_issue(
                    "SINGLE_SOURCE_PROVENANCE_MISMATCH",
                    "B-SV024",
                    "SemanticProposal",
                    source_id,
                    "Single-Source-Fälle erlauben nur die einzige deterministisch bereitgestellte SourceLocation",
                ))

    return issues


def semantic_response_is_valid_v0_2(
    response: dict[str, Any],
    *,
    allowed_source_location_ids: set[str],
    target_source_location_id: str,
) -> bool:
    return not validate_semantic_response_v0_2(
        response,
        allowed_source_location_ids=allowed_source_location_ids,
        target_source_location_id=target_source_location_id,
    )
