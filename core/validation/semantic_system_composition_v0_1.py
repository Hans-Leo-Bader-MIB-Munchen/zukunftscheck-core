from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2
from core.validation.semantic_completeness_profile_engine_v0_1 import evaluate_completeness_profile
from core.validation.semantic_completeness_profile_loader_v0_1 import validate_profile_set

COMPOSITION_VERSION = "semantic-system-composition-v0.1"
TECHNICAL_BOUNDARY_STOP = "TECHNICAL_BOUNDARY_STOP"
FAIL_CLOSED_STOP = "FAIL_CLOSED_STOP"
UNKNOWN_STATE_STOP = "UNKNOWN_STATE_STOP"
SEMANTIC_COMPLETENESS_STOP = "SEMANTIC_COMPLETENESS_STOP"
NO_COMPLETENESS_ASSESSMENT = "NO_COMPLETENESS_ASSESSMENT"
NO_COMPLETENESS_STOP = "NO_COMPLETENESS_STOP"
UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED = "UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED"
ALLOWED_TRIGGER_STATES = {"ACTIVE", "INACTIVE", "UNKNOWN"}

# Structural shape/type failures are system-state failures, not semantic/provenance
# boundary violations. The frozen v0.2 qualification policy distinguishes these
# explicitly from TECHNICAL_BOUNDARY_STOP.
MALFORMED_BOUNDARY_CODES = {
    "INVALID_SEMANTIC_RESPONSE",
    "MISSING_SEMANTIC_PROPOSALS",
    "INVALID_PROPOSAL",
    "INVALID_ASSIGNMENT_CANDIDATES",
    "INVALID_ASSIGNMENT_CANDIDATE",
}


def _base_result(*, target_source_location_id: Any, pf_id: Any) -> dict[str, Any]:
    return {
        "composition_version": COMPOSITION_VERSION,
        "target_source_location_id": target_source_location_id,
        "pf_id": pf_id,
        "decision_authority": "NONE",
        "global_downstream_authority": "NONE",
        "automatic_semantic_repair": False,
        "auto_assignment_performed": False,
        "model_output_mutated": False,
        "model_qualification_changed": False,
    }


def _unknown_state(*, target_source_location_id: Any, pf_id: Any, reason: str) -> dict[str, Any]:
    return {
        **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
        "behavior": UNKNOWN_STATE_STOP,
        "stop_class": UNKNOWN_STATE_STOP,
        "stop_code": UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED,
        "human_review_required": True,
        "completeness_assessed": False,
        "reason": reason,
        "boundary_passed": True,
        "boundary_issues": [],
        "completeness_result": None,
    }


def _profile_for_pf(profile_set: dict[str, Any], pf_id: str) -> dict[str, Any] | None:
    matches = [profile for profile in profile_set["profiles"] if profile.get("pf_id") == pf_id]
    if len(matches) != 1:
        return None
    return matches[0]


def _issue_row(issue: Any) -> dict[str, Any]:
    if hasattr(issue, "to_dict"):
        row = issue.to_dict()
        if isinstance(row, dict):
            return row
    values = getattr(issue, "__dict__", None)
    return dict(values) if isinstance(values, dict) else {"code": None, "message": str(issue)}


def evaluate_semantic_system_composition(
    *,
    model_response: Any,
    allowed_source_location_ids: Any,
    target_source_location_id: Any,
    pf_id: Any,
    trigger_state: Any,
    profile_set: Any,
) -> dict[str, Any]:
    """Compose Boundary v0.2 and Generic Completeness Engine v0.1 deterministically.

    Boundary is always attempted first. The layer performs no semantic inference,
    repair or assignment generation and grants no downstream decision authority.
    Human Gold and the qualification oracle are intentionally absent from runtime
    inputs; they may only be used offline to derive and test the declarative profiles.
    """
    original = deepcopy(model_response)

    # Boundary v0.2 is the first substantive gate. An inability to execute the
    # boundary itself remains a technical boundary stop.
    try:
        boundary_issues = validate_semantic_response_v0_2(
            model_response,
            allowed_source_location_ids=allowed_source_location_ids,
            target_source_location_id=target_source_location_id,
        )
    except Exception as exc:
        return {
            **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
            "behavior": TECHNICAL_BOUNDARY_STOP,
            "stop_class": TECHNICAL_BOUNDARY_STOP,
            "stop_code": "BOUNDARY_EVALUATION_FAILED",
            "human_review_required": True,
            "completeness_assessed": False,
            "reason": type(exc).__name__,
            "boundary_passed": False,
            "boundary_issues": [],
            "completeness_result": None,
        }

    if model_response != original:
        raise RuntimeError("generic system composition must not mutate model output")

    if boundary_issues:
        rows = [_issue_row(issue) for issue in boundary_issues]
        codes = [row.get("code") for row in rows if isinstance(row, dict)]
        malformed = any(code in MALFORMED_BOUNDARY_CODES for code in codes)
        behavior = FAIL_CLOSED_STOP if malformed else TECHNICAL_BOUNDARY_STOP
        stop_code = (
            "TARGET_SOURCE_LOCATION_MISMATCH"
            if "TARGET_SOURCE_LOCATION_MISMATCH" in codes
            else next((code for code in codes if isinstance(code, str) and code), "BOUNDARY_REVIEW_REQUIRED")
        )
        return {
            **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
            "behavior": behavior,
            "stop_class": behavior,
            "stop_code": stop_code,
            "human_review_required": True,
            "completeness_assessed": False,
            "reason": "MALFORMED_SYSTEM_STATE" if malformed else "BOUNDARY_VALIDATION_FAILED",
            "boundary_passed": False,
            "boundary_issues": rows,
            "completeness_result": None,
        }

    # Everything below this point is system-state interpretation after a passed
    # formal boundary and therefore fails closed as UNKNOWN_STATE_STOP.
    if not isinstance(pf_id, str) or not pf_id:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason="INVALID_PF_ID",
        )
    if not isinstance(target_source_location_id, str) or not target_source_location_id:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason="INVALID_TARGET_SOURCE_LOCATION_ID",
        )
    if not isinstance(trigger_state, str) or trigger_state not in ALLOWED_TRIGGER_STATES:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason="INVALID_TRIGGER_STATE",
        )
    if trigger_state == "UNKNOWN":
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason="UNKNOWN_TRIGGER_STATE",
        )

    try:
        validated_profiles = validate_profile_set(profile_set)
    except Exception as exc:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason=f"INVALID_PROFILE_SET:{type(exc).__name__}",
        )

    profile = _profile_for_pf(validated_profiles, pf_id)
    if profile is None or profile.get("runtime_enabled") is not True:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason="PROFILE_NOT_UNIQUELY_RUNTIME_ENABLED",
        )

    if trigger_state == "INACTIVE":
        return {
            **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
            "behavior": NO_COMPLETENESS_ASSESSMENT,
            "stop_class": None,
            "stop_code": None,
            "human_review_required": False,
            "completeness_assessed": False,
            "reason": "TRIGGER_INACTIVE",
            "boundary_passed": True,
            "boundary_issues": [],
            "completeness_result": None,
        }

    try:
        completeness = evaluate_completeness_profile(
            profile=profile,
            trigger_active=True,
            model_response=model_response,
            target_source_location_id=target_source_location_id,
        )
    except Exception as exc:
        return _unknown_state(
            target_source_location_id=target_source_location_id,
            pf_id=pf_id,
            reason=f"COMPLETENESS_EVALUATION_FAILED:{type(exc).__name__}",
        )

    if model_response != original:
        raise RuntimeError("generic system composition must not mutate model output")

    if completeness.get("completeness_stop_required") is True:
        return {
            **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
            "behavior": SEMANTIC_COMPLETENESS_STOP,
            "stop_class": SEMANTIC_COMPLETENESS_STOP,
            "stop_code": completeness.get("stop_code"),
            "human_review_required": True,
            "completeness_assessed": True,
            "reason": "MISSING_REQUIRED_ASSIGNMENTS",
            "boundary_passed": True,
            "boundary_issues": [],
            "completeness_result": completeness,
        }

    return {
        **_base_result(target_source_location_id=target_source_location_id, pf_id=pf_id),
        "behavior": NO_COMPLETENESS_STOP,
        "stop_class": None,
        "stop_code": None,
        "human_review_required": False,
        "completeness_assessed": True,
        "reason": "REQUIRED_ASSIGNMENTS_PRESENT_FOR_TARGET",
        "boundary_passed": True,
        "boundary_issues": [],
        "completeness_result": completeness,
    }
