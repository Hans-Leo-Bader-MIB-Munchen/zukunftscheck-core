#!/usr/bin/env python3
"""Fully model-free guarded-system qualification runner v0.1.

The runner executes only the HUMAN_APPROVED_FROZEN deterministic 19-case system
suite. It never contacts LM Studio, never calls a model endpoint, never repairs
model output and never changes the separate model-qualification status.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.validation.semantic_runtime_guard_v0_1 import evaluate_semantic_runtime_guard
from core.validation.semantic_system_qualification_evaluator_v0_1 import evaluate_system_case

POLICY_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_policy_v0_1.json"
SYSTEM_SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_suite_v0_1.json"
FREEZE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_v0_1.json"
MODEL_SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
RUNNER_VERSION = "v0.1"
RUN_TYPE = "ZS-KI-B-SEM-GUARDED-SYSTEM-QUALIFIKATION-MODEL-FREE-2026-001"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_frozen_inputs(policy: dict[str, Any], suite: dict[str, Any], freeze: dict[str, Any]) -> None:
    for name, payload in (("policy", policy), ("suite", suite), ("freeze", freeze)):
        if payload.get("status") != "HUMAN_APPROVED_FROZEN":
            raise RuntimeError(f"{name} must be HUMAN_APPROVED_FROZEN")
    if policy.get("execution_authorized") is not False or policy.get("model_run_authorized") is not False:
        raise RuntimeError("frozen policy must not authorize model execution")
    if suite.get("execution_authorized") is not False or suite.get("model_run_authorized") is not False:
        raise RuntimeError("frozen suite must not authorize model execution")
    if freeze.get("model_run_authorized") is not False:
        raise RuntimeError("freeze manifest must not authorize model execution")


def build_gold_complete_response(case: dict[str, Any], gold_case: dict[str, Any]) -> dict[str, Any]:
    target = case["target_source_location_id"]
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target,
        "proposals": [
            {
                "proposal_id": f"P-{target}-SYSQUAL-RUNNER",
                "source_location_id": target,
                "normalized_statement": next(
                    row["original_text"] for row in case["source_locations"]
                    if row["source_location_id"] == target
                ),
                "finding_type_candidate": "NR",
                "evidence_relation_type_candidate": "DIRECT",
                "assignment_candidates": [
                    {
                        "question_id": row["question_id"],
                        "pf_id": row["pf_id"],
                        "assignment_confidence": "CLEAR",
                        "human_review_required": False,
                    }
                    for row in gold_case.get("expected_assignments", [])
                ],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": False,
            }
        ],
    }


def _apply_variant(response: dict[str, Any], variant: str) -> tuple[dict[str, Any], bool]:
    variant_response = copy.deepcopy(response)
    if variant == "GOLD_COMPLETE_REQUIRED_ONLY":
        return variant_response, True
    if variant == "PF2_REMOVE_REQUIRED_2_2":
        variant_response["proposals"][0]["assignment_candidates"] = [
            row for row in variant_response["proposals"][0]["assignment_candidates"]
            if not (row["question_id"] == "2.2" and row["pf_id"] == "PF2")
        ]
        return variant_response, True
    if variant == "TARGET_SOURCE_LOCATION_MISMATCH":
        variant_response["source_location_id"] = "SL-WRONG-999"
        return variant_response, True
    if variant == "UNCLASSIFIED_SYSTEM_STATE":
        return variant_response, False
    raise RuntimeError(f"unknown frozen response_variant: {variant}")


def _guard(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    target = case["target_source_location_id"]
    source_by_id = {row["source_location_id"]: row for row in case["source_locations"]}
    return evaluate_semantic_runtime_guard(
        source_text=source_by_id[target]["original_text"],
        model_response=response,
        allowed_source_location_ids=set(source_by_id),
        target_source_location_id=target,
    )


def run_model_free_system_qualification() -> dict[str, Any]:
    policy = load(POLICY_PATH)
    system_suite = load(SYSTEM_SUITE_PATH)
    freeze = load(FREEZE_PATH)
    model_suite = load(MODEL_SUITE_PATH)
    gold = load(GOLD_PATH)
    _assert_frozen_inputs(policy, system_suite, freeze)

    case_by_id = {row["case_id"]: row for row in model_suite["cases"]}
    gold_by_id = {row["case_id"]: row for row in gold["cases"]}
    case_results: list[dict[str, Any]] = []

    for spec in system_suite["cases"]:
        case = case_by_id[spec["base_case_id"]]
        response = build_gold_complete_response(case, gold_by_id[case["case_id"]])
        variant_response, classified = _apply_variant(response, spec["response_variant"])
        guard_result = _guard(case, variant_response) if classified else None
        evaluation = evaluate_system_case(
            case_spec=spec,
            guard_result=guard_result,
            system_state_classified=classified,
        )
        case_results.append({
            "system_case_id": spec["system_case_id"],
            "base_case_id": spec["base_case_id"],
            "response_variant": spec["response_variant"],
            "expected_behavior": spec["expected_behavior"],
            "evaluation": evaluation,
        })

    passed = sum(row["evaluation"]["case_passed"] is True for row in case_results)
    total = len(case_results)
    system_qualified = passed == total == system_suite["case_count"]

    return {
        "mode": "MODEL_FREE_GUARDED_SYSTEM_QUALIFICATION_V0_1",
        "manifest": {
            "run_type": RUN_TYPE,
            "runner_version": RUNNER_VERSION,
            "data_class": "SYNTHETIC_ONLY",
            "system_case_count": total,
            "system_case_pass_count": passed,
            "model_contact_attempted": False,
            "model_request_count": 0,
            "remote_cloud": False,
            "real_data": False,
            "output_repair": False,
            "model_output_mutation_allowed": False,
            "model_qualified": False,
            "guarded_system_qualified": system_qualified,
            "benchmark_approved": False,
            "generalisation_approved": False,
            "pilot_approved": False,
            "production_approved": False,
            "phase_f_approved": False,
            "policy_version": policy["policy_version"],
            "suite_version": system_suite["suite_version"],
            "freeze_version": freeze["freeze_version"],
        },
        "cases": case_results,
    }


def main() -> int:
    result = run_model_free_system_qualification()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["manifest"]["guarded_system_qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
