from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.validation.semantic_qualification_oracle_harness_v0_1 import build_qualification_oracle_bundle
from core.validation.semantic_system_composition_v0_1 import evaluate_semantic_system_composition

HARNESS_VERSION = "semantic-system-qualification-execution-harness-v0.1"
MODEL_CONTACT_AUTHORIZED = False
DECISION_AUTHORITY = "NONE"
EXPECTED_SUITE_VERSION = "ZS-KI-B-SEM-SYSTEMQUALIFIKATION-SUITE-2026-002_v0.2"
EXPECTED_CASE_COUNT = 29


def _assignment(question_id: str, pf_id: str) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "pf_id": pf_id,
        "assignment_confidence": "UNCERTAIN",
        "human_review_required": True,
    }


def _response(
    groups: list[tuple[str, list[list[str]]]],
    *,
    target_source_location_id: str,
) -> dict[str, Any]:
    proposals = []
    for index, (source_location_id, assignments) in enumerate(groups, start=1):
        proposals.append({
            "proposal_id": f"Q-P-{index}",
            "source_location_id": source_location_id,
            "normalized_statement": "synthetic qualification input",
            "finding_type_candidate": "NR",
            "evidence_relation_type_candidate": "DIRECT",
            "assignment_candidates": [_assignment(pair[0], pair[1]) for pair in assignments],
            "conflict_candidate_refs": [],
            "gap_notes": [],
            "uncertainty_notes": [],
            "human_review_required": True,
        })
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target_source_location_id,
        "proposals": proposals,
    }


def _oracle_by_pf(gold: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bundle = build_qualification_oracle_bundle(gold)
    if bundle.get("model_contact_authorized") is not False:
        raise ValueError("qualification oracle must remain model-free")
    return {row["pf_id"]: row for row in bundle["cases"]}


def _negative_variant(oracle: dict[str, Any], kind: str, omitted: list[str] | None = None) -> dict[str, Any]:
    matches = []
    for variant in oracle["negative_variants"]:
        if variant.get("variant_kind") != kind:
            continue
        if omitted is not None and variant.get("missing_required_assignments") != [omitted]:
            continue
        matches.append(variant)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one oracle variant for {kind}")
    return matches[0]


def materialize_frozen_system_cases(
    *,
    suite: dict[str, Any],
    gold: dict[str, Any],
) -> list[dict[str, Any]]:
    """Materialize the frozen 29 synthetic case specs without executing composition.

    Human Gold is used only here as an offline qualification source through the
    frozen oracle harness. It is never passed into semantic system composition.
    """
    if suite.get("suite_version") != EXPECTED_SUITE_VERSION:
        raise ValueError("unexpected system qualification suite version")
    if suite.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("execution harness requires HUMAN_APPROVED_FROZEN suite")
    if suite.get("model_contact_authorized") is not False:
        raise ValueError("model contact must remain forbidden")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ValueError("frozen suite must contain exactly 29 cases")

    oracle = _oracle_by_pf(gold)
    materialized: list[dict[str, Any]] = []

    for spec in cases:
        case = deepcopy(spec)
        pf_id = case.get("pf_id")
        family = case.get("case_family")
        target = case.get("target_source_location_id", "SL-001")
        allowed = {target}
        trigger_state = "ACTIVE"

        if isinstance(pf_id, str) and pf_id in oracle:
            pf_oracle = oracle[pf_id]
            required = deepcopy(pf_oracle["required_assignments"])
            optional = deepcopy(pf_oracle["optional_assignments"])

            if family == "COMPLETE_REQUIRED_SET":
                assignments = required
                response = _response([(target, assignments)], target_source_location_id=target)
            elif family == "OMIT_ALL_REQUIRED":
                variant = _negative_variant(pf_oracle, "OMIT_ALL_REQUIRED")
                response = _response([(target, deepcopy(variant["assignments"]))], target_source_location_id=target)
            elif family == "OMIT_ONE_REQUIRED":
                omitted = case.get("omitted_assignment")
                if not isinstance(omitted, list):
                    raise ValueError("OMIT_ONE_REQUIRED requires omitted_assignment")
                variant = _negative_variant(pf_oracle, "OMIT_ONE_REQUIRED", omitted)
                response = _response([(target, deepcopy(variant["assignments"]))], target_source_location_id=target)
            elif family == "OMIT_MULTIPLE_REQUIRED":
                variant = _negative_variant(pf_oracle, "OMIT_MULTIPLE_REQUIRED")
                response = _response([(target, deepcopy(variant["assignments"]))], target_source_location_id=target)
            elif family == "OPTIONAL_PRESENT_REQUIRED_MISSING":
                preserved = case.get("preserved_optional_assignment")
                if preserved not in optional:
                    raise ValueError("preserved optional assignment is not frozen oracle optional data")
                response = _response([(target, [deepcopy(preserved)])], target_source_location_id=target)
            elif family == "MULTI_PROPOSAL_SAME_SOURCE":
                split = 1 if len(required) > 1 else len(required)
                response = _response(
                    [(target, required[:split]), (target, required[split:])],
                    target_source_location_id=target,
                )
            elif family == "MULTI_SOURCE_PROVENANCE":
                other = case.get("other_source_location_id")
                if not isinstance(other, str) or other == target:
                    raise ValueError("multi-source case requires distinct other source")
                allowed = {target, other}
                split = 1 if len(required) > 1 else len(required)
                response = _response(
                    [(target, required[:split]), (other, required[split:])],
                    target_source_location_id=target,
                )
            elif family == "INACTIVE_TRIGGER_AUTHORITY":
                trigger_state = "INACTIVE"
                response = _response([(target, required[:1])], target_source_location_id=target)
            else:
                raise ValueError(f"unsupported PF case family: {family}")
        elif family == "TECHNICAL_BOUNDARY_STOP":
            pf_id = "PF9"
            pf_oracle = oracle[pf_id]
            required = deepcopy(pf_oracle["required_assignments"])
            target = "SL-A"
            allowed = {"SL-A", "SL-B"}
            response = _response([("SL-B", required)], target_source_location_id="SL-B")
        elif family == "MALFORMED_NESTED_TYPE":
            pf_id = "PF9"
            required = deepcopy(oracle[pf_id]["required_assignments"])
            target = "SL-001"
            allowed = {target}
            response = _response([(target, required)], target_source_location_id=target)
            malformed_path = case.get("malformed_path")
            if malformed_path == "proposals":
                response["proposals"] = "malformed"
            elif malformed_path == "proposals[].assignment_candidates":
                response["proposals"][0]["assignment_candidates"] = "malformed"
            elif malformed_path == "proposals[].assignment_candidates[]":
                response["proposals"][0]["assignment_candidates"] = ["malformed"]
            else:
                raise ValueError("unsupported malformed_path")
        elif family == "UNKNOWN_STATE_STOP":
            pf_id = "PF99"
            required = deepcopy(oracle["PF9"]["required_assignments"])
            target = "SL-001"
            allowed = {target}
            response = _response([(target, required)], target_source_location_id=target)
        else:
            raise ValueError(f"unsupported qualification case family: {family}")

        materialized.append({
            "system_case_id": case["system_case_id"],
            "case_spec": case,
            "pf_id": pf_id,
            "trigger_state": trigger_state,
            "target_source_location_id": target,
            "allowed_source_location_ids": allowed,
            "model_response": response,
            "data_class": "SYNTHETIC_ONLY",
            "model_contact_authorized": False,
        })

    ids = [row["system_case_id"] for row in materialized]
    if len(ids) != EXPECTED_CASE_COUNT or len(set(ids)) != EXPECTED_CASE_COUNT:
        raise ValueError("materialization must preserve exactly 29 unique frozen case ids")
    return materialized


def execute_frozen_system_qualification_once(
    *,
    suite: dict[str, Any],
    gold: dict[str, Any],
    profile_set: dict[str, Any],
    evaluated_commit: str,
    execution_authorized: bool,
) -> dict[str, Any]:
    """Execute one caller-authorized model-free qualification pass over all 29 cases."""
    if execution_authorized is not True:
        raise PermissionError("explicit external execution authorization is required")
    if not isinstance(evaluated_commit, str) or not evaluated_commit:
        raise ValueError("evaluated_commit is required")

    cases = materialize_frozen_system_cases(suite=suite, gold=gold)
    results = []
    for row in cases:
        before = deepcopy(row["model_response"])
        composition = evaluate_semantic_system_composition(
            model_response=row["model_response"],
            allowed_source_location_ids=row["allowed_source_location_ids"],
            target_source_location_id=row["target_source_location_id"],
            pf_id=row["pf_id"],
            trigger_state=row["trigger_state"],
            profile_set=profile_set,
        )
        spec = row["case_spec"]
        checks = {
            "behavior_matches": composition.get("behavior") == spec.get("expected_behavior"),
            "stop_code_matches": True,
            "global_downstream_authority_none": composition.get("global_downstream_authority") == "NONE",
            "decision_authority_none": composition.get("decision_authority") == "NONE",
            "model_output_not_mutated": row["model_response"] == before and composition.get("model_output_mutated") is False,
            "model_qualification_unchanged": composition.get("model_qualification_changed") is False,
            "no_auto_assignment": composition.get("auto_assignment_performed") is False,
        }
        expected_code = spec.get("expected_code")
        if expected_code is not None:
            checks["stop_code_matches"] = composition.get("stop_code") == expected_code
        expected_authority = spec.get("global_downstream_authority")
        if expected_authority is not None:
            checks["declared_global_authority_matches"] = composition.get("global_downstream_authority") == expected_authority

        results.append({
            "system_case_id": row["system_case_id"],
            "case_family": spec.get("case_family"),
            "expected_behavior": spec.get("expected_behavior"),
            "actual_behavior": composition.get("behavior"),
            "expected_code": expected_code,
            "actual_code": composition.get("stop_code"),
            "checks": checks,
            "case_passed": all(checks.values()),
        })

    passed = sum(1 for row in results if row["case_passed"])
    return {
        "harness_version": HARNESS_VERSION,
        "suite_version": suite["suite_version"],
        "evaluated_commit": evaluated_commit,
        "data_class": "SYNTHETIC_ONLY",
        "model_contact_authorized": False,
        "model_contact_observed": False,
        "decision_authority": "NONE",
        "model_qualification_changed": False,
        "case_count": len(results),
        "passed_case_count": passed,
        "failed_case_count": len(results) - passed,
        "qualification_passed": passed == len(results) == EXPECTED_CASE_COUNT,
        "results": results,
    }
