from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2
from core.validation.semantic_completeness_audit_v0_1 import audit_pf2_scope_completeness

RUNTIME_GUARD_VERSION = "semantic-runtime-guard-v0.1"


def evaluate_semantic_runtime_guard(
    *,
    source_text: str,
    model_response: dict[str, Any],
    allowed_source_location_ids: set[str],
    target_source_location_id: str,
) -> dict[str, Any]:
    """Deterministic post-model guard combining formal boundary and completeness audit.

    The guard never mutates or repairs the model response. A formal boundary issue
    blocks downstream use. If the formal boundary passes, the narrow PF2 completeness
    audit may additionally require human review and block automatic downstream use.
    """
    original = deepcopy(model_response)

    boundary_issues = validate_semantic_response_v0_2(
        model_response,
        allowed_source_location_ids=allowed_source_location_ids,
        target_source_location_id=target_source_location_id,
    )
    boundary_passed = not boundary_issues

    completeness = None
    if boundary_passed:
        completeness = audit_pf2_scope_completeness(
            source_text=source_text,
            model_response=model_response,
        )

    completeness_stop = bool(
        completeness and completeness.get("stop_automatic_downstream_use") is True
    )
    automatic_downstream_use_allowed = boundary_passed and not completeness_stop

    if model_response != original:
        raise RuntimeError("semantic runtime guard must not mutate model output")

    return {
        "runtime_guard_version": RUNTIME_GUARD_VERSION,
        "boundary_passed": boundary_passed,
        "boundary_issues": [issue.__dict__ for issue in boundary_issues],
        "completeness_audit": completeness,
        "human_review_required": completeness_stop,
        "automatic_downstream_use_allowed": automatic_downstream_use_allowed,
        "model_output_mutated": False,
        "decision_authority": "NONE",
    }
