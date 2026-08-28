from __future__ import annotations

from copy import deepcopy
from typing import Any

ENGINE_VERSION = "semantic-completeness-profile-engine-v0.1"
STOP_CLASS = "SEMANTIC_COMPLETENESS_STOP"
DEFAULT_STOP_CODE = "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED"


def _assignment_pairs_for_target(
    model_response: dict[str, Any],
    *,
    target_source_location_id: str,
) -> set[tuple[str, str]]:
    """Collect assignments only from proposals anchored to the target source location."""
    pairs: set[tuple[str, str]] = set()
    proposals = model_response.get("proposals")
    if not isinstance(proposals, list):
        return pairs
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        if proposal.get("source_location_id") != target_source_location_id:
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


def _required_pairs(profile: dict[str, Any]) -> set[tuple[str, str]]:
    required = profile.get("required_assignments")
    if not isinstance(required, list):
        raise ValueError("profile.required_assignments must be a list")
    pairs: set[tuple[str, str]] = set()
    for item in required:
        if not isinstance(item, dict):
            raise ValueError("required assignment must be an object")
        question_id = item.get("question_id")
        pf_id = item.get("pf_id")
        if not isinstance(question_id, str) or not isinstance(pf_id, str):
            raise ValueError("required assignment requires string question_id and pf_id")
        pairs.add((question_id, pf_id))
    if not pairs:
        raise ValueError("profile.required_assignments must not be empty")
    return pairs


def evaluate_completeness_profile(
    *,
    profile: dict[str, Any],
    trigger_active: bool,
    model_response: dict[str, Any],
    target_source_location_id: str,
) -> dict[str, Any]:
    """Evaluate one declarative completeness profile without semantic inference.

    The caller is responsible for evaluating the profile-specific trigger policy and
    for combining this component result with Boundary/Unknown-State/other guards.
    This engine never grants global downstream-use authority. It only reports whether
    this completeness profile requires a stop for the specified target source.
    """
    original = deepcopy(model_response)

    profile_id = profile.get("profile_id")
    pf_id = profile.get("pf_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("profile.profile_id must be a non-empty string")
    if not isinstance(pf_id, str) or not pf_id:
        raise ValueError("profile.pf_id must be a non-empty string")
    if not isinstance(trigger_active, bool):
        raise ValueError("trigger_active must be bool")
    if not isinstance(target_source_location_id, str) or not target_source_location_id:
        raise ValueError("target_source_location_id must be a non-empty string")
    if profile.get("decision_authority", "NONE") != "NONE":
        raise ValueError("completeness profile may not have decision authority")

    required = _required_pairs(profile)
    if any(required_pf_id != pf_id for _, required_pf_id in required):
        raise ValueError("all required assignments must match profile.pf_id")

    observed = _assignment_pairs_for_target(
        model_response,
        target_source_location_id=target_source_location_id,
    )
    completeness_evaluated = trigger_active
    missing = sorted(required - observed) if completeness_evaluated else []
    stop = bool(completeness_evaluated and missing)

    if model_response != original:
        raise RuntimeError("generic completeness engine must not mutate model output")

    return {
        "engine_version": ENGINE_VERSION,
        "profile_id": profile_id,
        "pf_id": pf_id,
        "target_source_location_id": target_source_location_id,
        "trigger_active": trigger_active,
        "completeness_evaluated": completeness_evaluated,
        "required_assignments": [list(pair) for pair in sorted(required)],
        "observed_assignments": [list(pair) for pair in sorted(observed)],
        "missing_required_assignments": [list(pair) for pair in missing],
        "completeness_stop_required": stop,
        "completeness_downstream_blocked": stop,
        "stop_class": STOP_CLASS if stop else None,
        "stop_code": profile.get("stop_code", DEFAULT_STOP_CODE) if stop else None,
        "human_review_required": stop,
        "review_metadata": {
            "profile_id": profile_id,
            "pf_id": pf_id,
            "target_source_location_id": target_source_location_id,
            "missing_required_assignments": [list(pair) for pair in missing],
            "trigger_policy_type": (
                profile.get("trigger_policy", {}).get("type")
                if isinstance(profile.get("trigger_policy"), dict)
                else None
            ),
            "review_class": STOP_CLASS if stop else None,
        },
        "auto_assignment_performed": False,
        "semantic_repair_performed": False,
        "model_output_mutated": False,
        "decision_authority": "NONE",
        "global_downstream_authority": "NONE",
        "model_qualification_changed": False,
    }
