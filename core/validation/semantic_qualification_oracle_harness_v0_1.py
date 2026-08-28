from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

HARNESS_VERSION = "semantic-qualification-oracle-harness-v0.1"
QUALIFICATION_ONLY = True
MODEL_CONTACT_AUTHORIZED = False
DECISION_AUTHORITY = "NONE"


def _pairs(items: Iterable[dict[str, Any]]) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for item in items:
        question_id = item.get("question_id")
        pf_id = item.get("pf_id")
        if not isinstance(question_id, str) or not isinstance(pf_id, str):
            raise ValueError("gold assignments require string question_id and pf_id")
        pairs.append((question_id, pf_id))
    return tuple(pairs)


def qualification_case_by_pf(gold: dict[str, Any], pf_id: str) -> dict[str, Any]:
    if gold.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("qualification oracle requires HUMAN_APPROVED_FROZEN gold")
    if gold.get("model_visible") is not False:
        raise ValueError("qualification oracle must remain model-invisible")
    suffix = f"-Q-{pf_id}-SYN-001"
    matches = [case for case in gold.get("cases", []) if case.get("case_id", "").endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one frozen qualification case for {pf_id}")
    return deepcopy(matches[0])


def required_pairs(case: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    expected = case.get("expected_assignments")
    if not isinstance(expected, list) or not expected:
        raise ValueError("qualification case requires non-empty expected_assignments")
    return _pairs(expected)


def optional_pairs(case: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    optional = case.get("optional_assignments", [])
    if not isinstance(optional, list):
        raise ValueError("optional_assignments must be a list")
    return _pairs(optional)


def generate_negative_variants(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate deterministic qualification-only omission variants from frozen Human Gold.

    The variants are test inputs only. They grant no runtime profile, trigger policy,
    model qualification, semantic repair, or execution authority.
    """
    required = list(required_pairs(case))
    optional = list(optional_pairs(case))
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("qualification case requires case_id")

    variants: list[dict[str, Any]] = []

    variants.append({
        "variant_id": f"{case_id}::OMIT_ALL_REQUIRED",
        "source_case_id": case_id,
        "variant_kind": "OMIT_ALL_REQUIRED",
        "assignments": [list(pair) for pair in optional],
        "missing_required_assignments": [list(pair) for pair in required],
    })

    for omitted in required:
        kept = [pair for pair in required if pair != omitted] + optional
        variants.append({
            "variant_id": f"{case_id}::OMIT_ONE::{omitted[0]}::{omitted[1]}",
            "source_case_id": case_id,
            "variant_kind": "OMIT_ONE_REQUIRED",
            "assignments": [list(pair) for pair in kept],
            "missing_required_assignments": [list(omitted)],
        })

    if len(required) > 1:
        kept = [required[0]] + optional
        variants.append({
            "variant_id": f"{case_id}::OMIT_MULTIPLE_REQUIRED",
            "source_case_id": case_id,
            "variant_kind": "OMIT_MULTIPLE_REQUIRED",
            "assignments": [list(pair) for pair in kept],
            "missing_required_assignments": [list(pair) for pair in required[1:]],
        })

    return variants


def build_qualification_oracle_bundle(gold: dict[str, Any], pf_ids: tuple[str, ...] = ("PF2", "PF9", "PF12")) -> dict[str, Any]:
    cases = []
    for pf_id in pf_ids:
        case = qualification_case_by_pf(gold, pf_id)
        cases.append({
            "pf_id": pf_id,
            "source_case_id": case["case_id"],
            "required_assignments": [list(pair) for pair in required_pairs(case)],
            "optional_assignments": [list(pair) for pair in optional_pairs(case)],
            "negative_variants": generate_negative_variants(case),
        })
    return {
        "harness_version": HARNESS_VERSION,
        "qualification_only": QUALIFICATION_ONLY,
        "model_contact_authorized": MODEL_CONTACT_AUTHORIZED,
        "decision_authority": DECISION_AUTHORITY,
        "human_gold_runtime_dependency": False,
        "runtime_profiles_created": False,
        "runtime_trigger_policies_created": False,
        "model_qualification_changed": False,
        "automatic_semantic_repair": False,
        "auto_assignment_performed": False,
        "cases": cases,
    }
