from __future__ import annotations

from typing import Any

EVALUATOR_VERSION = "semantic-system-qualification-evaluator-v0.1"
UNKNOWN_SYSTEM_STATE_STOP_CODE = "UNKNOWN_SYSTEM_STATE_REVIEW_REQUIRED"
SEMANTIC_COMPLETENESS_STOP_CODE = "SEMANTIC_COMPLETENESS_REVIEW_REQUIRED"


def _first_issue_code(rows: list[dict[str, Any]] | None) -> str | None:
    for row in rows or []:
        code = row.get("code")
        if isinstance(code, str) and code:
            return code
    return None


def _guard_stop_code(guard_result: dict[str, Any]) -> str:
    direct = _first_issue_code(guard_result.get("issues"))
    if direct:
        return direct
    completeness = guard_result.get("completeness_audit")
    if isinstance(completeness, dict) and completeness.get("stop_automatic_downstream_use") is True:
        return SEMANTIC_COMPLETENESS_STOP_CODE
    return UNKNOWN_SYSTEM_STATE_STOP_CODE


def classify_system_outcome(
    *,
    guard_result: dict[str, Any] | None,
    system_state_classified: bool = True,
) -> dict[str, Any]:
    """Normalize runtime-guard output into one fail-closed system outcome.

    This layer grants no semantic authority and performs no model-output repair.
    Unknown/unclassified states and formal-boundary failures require human review.
    """
    if not system_state_classified or guard_result is None:
        return {
            "evaluator_version": EVALUATOR_VERSION,
            "actual_behavior": "FAIL_CLOSED_STOP",
            "stop_code": UNKNOWN_SYSTEM_STATE_STOP_CODE,
            "human_review_required": True,
            "automatic_downstream_use_allowed": False,
            "model_output_mutated": False,
            "decision_authority": "NONE",
        }

    if guard_result.get("boundary_passed") is not True:
        return {
            "evaluator_version": EVALUATOR_VERSION,
            "actual_behavior": "FAIL_CLOSED_STOP",
            "stop_code": _first_issue_code(guard_result.get("boundary_issues")) or UNKNOWN_SYSTEM_STATE_STOP_CODE,
            "human_review_required": True,
            "automatic_downstream_use_allowed": False,
            "model_output_mutated": bool(guard_result.get("model_output_mutated")),
            "decision_authority": "NONE",
        }

    if guard_result.get("automatic_downstream_use_allowed") is not True:
        return {
            "evaluator_version": EVALUATOR_VERSION,
            "actual_behavior": "FAIL_CLOSED_STOP",
            "stop_code": _guard_stop_code(guard_result),
            "human_review_required": True,
            "automatic_downstream_use_allowed": False,
            "model_output_mutated": bool(guard_result.get("model_output_mutated")),
            "decision_authority": "NONE",
        }

    return {
        "evaluator_version": EVALUATOR_VERSION,
        "actual_behavior": "PASS_THROUGH",
        "stop_code": None,
        "human_review_required": False,
        "automatic_downstream_use_allowed": True,
        "model_output_mutated": bool(guard_result.get("model_output_mutated")),
        "decision_authority": "NONE",
    }


def evaluate_system_case(
    *,
    case_spec: dict[str, Any],
    guard_result: dict[str, Any] | None,
    system_state_classified: bool = True,
) -> dict[str, Any]:
    outcome = classify_system_outcome(
        guard_result=guard_result,
        system_state_classified=system_state_classified,
    )
    expected_behavior = case_spec.get("expected_behavior")
    expected_stop_code = case_spec.get("expected_stop_code") or case_spec.get("expected_boundary_code")

    checks = {
        "behavior_matches": outcome["actual_behavior"] == expected_behavior,
        "stop_code_matches": True,
        "human_review_matches": True,
        "downstream_use_matches": True,
        "no_model_output_mutation": outcome["model_output_mutated"] is False,
    }

    if expected_behavior == "FAIL_CLOSED_STOP":
        checks["stop_code_matches"] = outcome["stop_code"] == expected_stop_code
        if "human_review_required" in case_spec:
            checks["human_review_matches"] = (
                outcome["human_review_required"] is case_spec["human_review_required"]
            )
        if "automatic_downstream_use_allowed" in case_spec:
            checks["downstream_use_matches"] = (
                outcome["automatic_downstream_use_allowed"]
                is case_spec["automatic_downstream_use_allowed"]
            )

    return {
        "system_case_id": case_spec.get("system_case_id"),
        "expected_behavior": expected_behavior,
        **outcome,
        "checks": checks,
        "case_passed": all(checks.values()),
        "model_qualification_changed": False,
    }
