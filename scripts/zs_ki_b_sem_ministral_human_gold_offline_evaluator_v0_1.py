#!/usr/bin/env python3
"""Model-free offline Human-Gold evaluator for the preserved V2.5 Ministral result.

This module MUST NOT contact LM Studio, localhost, an API, or any model. It reads
one already-existing V2.5 result JSON, evaluates all 16 frozen cases against the
frozen Human Gold and qualification policy, and emits one audit report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_VERSION = "ZS-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATOR-2026-001_v0.1"
WORK_BLOCK = "ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001"
EXPECTED_V25_RUNNER_VERSION = "v2.5-max-tokens-binding-prep"
EXPECTED_V25_RUNNER_BLOB = "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866"
EXPECTED_CASE_COUNT = 16

SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"
EXPECTED_GOLD_BLOB = "704adbd930c042b132a34bb9ddc95b4531f336b2"
EXPECTED_POLICY_BLOB = "9bc06b2648b05f9bb1d464e019e23f8afd82570b"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for frozen artifact: {path}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def validate_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    suite, gold, policy = map(_load, (SUITE_PATH, GOLD_PATH, POLICY_PATH))
    if gold.get("status") != "HUMAN_APPROVED_FROZEN" or gold.get("model_visible") is not False:
        raise ValueError("Human Gold is not the frozen model-invisible artifact")
    if policy.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("qualification policy is not HUMAN_APPROVED_FROZEN")
    if _git_blob_sha1(GOLD_PATH) != EXPECTED_GOLD_BLOB:
        raise ValueError("Frozen Human Gold blob mismatch")
    if _git_blob_sha1(POLICY_PATH) != EXPECTED_POLICY_BLOB:
        raise ValueError("Frozen qualification policy blob mismatch")
    if len(suite.get("cases", [])) != EXPECTED_CASE_COUNT or len(gold.get("cases", [])) != EXPECTED_CASE_COUNT:
        raise ValueError("frozen suite/gold must contain exactly 16 cases")
    suite_ids = [row.get("case_id") for row in suite["cases"]]
    gold_ids = [row.get("case_id") for row in gold["cases"]]
    if suite_ids != gold_ids or len(set(suite_ids)) != EXPECTED_CASE_COUNT:
        raise ValueError("frozen suite/gold case ordering or uniqueness mismatch")
    return suite, gold, policy


def _assignment_set(response: dict[str, Any]) -> set[tuple[str, str]]:
    actual: set[tuple[str, str]] = set()
    proposals = response.get("proposals", [])
    if not isinstance(proposals, list):
        return actual
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        assignments = proposal.get("assignment_candidates", [])
        if not isinstance(assignments, list):
            continue
        for assignment in assignments:
            if isinstance(assignment, dict):
                question_id = assignment.get("question_id")
                pf_id = assignment.get("pf_id")
                if isinstance(question_id, str) and isinstance(pf_id, str):
                    actual.add((question_id, pf_id))
    return actual


def _gold_set(case_gold: dict[str, Any], key: str) -> set[tuple[str, str]]:
    rows = case_gold.get(key, [])
    if not isinstance(rows, list):
        raise ValueError(f"invalid Human Gold field {key}")
    return {(row["question_id"], row["pf_id"]) for row in rows}


def evaluate_gold(case_gold: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Exact semantic interpretation carried forward from runner v0.8."""
    actual = _assignment_set(response)
    required = _gold_set(case_gold, "expected_assignments")
    optional = _gold_set(case_gold, "optional_assignments")
    forbidden = _gold_set(case_gold, "forbidden_assignments")
    missing = required - actual
    forbidden_present = forbidden & actual
    spurious = actual - required - optional
    conflict_actual = any(
        isinstance(p, dict) and bool(p.get("conflict_candidate_refs"))
        for p in response.get("proposals", [])
    )
    conflict_expected = case_gold.get("expected_conflict_candidate")
    conflict_match = True if conflict_expected is None else conflict_actual is bool(conflict_expected)
    return {
        "passed": not missing and not forbidden_present and not spurious and conflict_match,
        "actual_assignments": [list(row) for row in sorted(actual)],
        "required_assignments": [list(row) for row in sorted(required)],
        "optional_assignments": [list(row) for row in sorted(optional)],
        "forbidden_assignments": [list(row) for row in sorted(forbidden)],
        "missing_required": [list(row) for row in sorted(missing)],
        "forbidden_present": [list(row) for row in sorted(forbidden_present)],
        "spurious_assignments": [list(row) for row in sorted(spurious)],
        "expected_conflict_candidate": conflict_expected,
        "actual_conflict_candidate": conflict_actual,
        "conflict_candidate_match": conflict_match,
    }


def evaluate_boundary(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    allowed = {row["source_location_id"] for row in case["source_locations"]}
    target = case["target_source_location_id"]
    issues = validate_semantic_response_v0_2(
        response,
        allowed_source_location_ids=allowed,
        target_source_location_id=target,
    )
    rendered = [issue.to_dict() for issue in issues]
    return {
        "passed": not rendered and response.get("source_location_id") == target,
        "issues": rendered,
    }


def _parse_preserved_response(case_row: dict[str, Any]) -> dict[str, Any]:
    if isinstance(case_row.get("model_response"), dict):
        return case_row["model_response"]
    raw = case_row.get("model_response_raw")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("missing preserved model_response_raw")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("preserved model response JSON root is not an object")
    return parsed


def _count_issue_code(case_reports: list[dict[str, Any]], code: str) -> int:
    return sum(
        1
        for row in case_reports
        for issue in row.get("boundary_evaluation", {}).get("issues", [])
        if issue.get("code") == code
    )


def evaluate_result(result: dict[str, Any]) -> dict[str, Any]:
    suite, gold, policy = validate_frozen_inputs()
    if result.get("status") != "AWAITING_HUMAN_REVIEW":
        raise ValueError("input is not a preserved V2.5 AWAITING_HUMAN_REVIEW result")
    if result.get("runner_version") != EXPECTED_V25_RUNNER_VERSION:
        raise ValueError("input runner_version is not the frozen V2.5 runner")
    if result.get("authorized_runner_blob_oid") != EXPECTED_V25_RUNNER_BLOB:
        raise ValueError("input authorized_runner_blob_oid does not match frozen V2.5 runner")
    if result.get("expected_model_request_count") != EXPECTED_CASE_COUNT or result.get("observed_model_request_count") != EXPECTED_CASE_COUNT:
        raise ValueError("input does not record exactly 16/16 model requests")
    if result.get("retry_count") != 0 or result.get("output_repair") is not False:
        raise ValueError("input violates no-retry/no-repair qualification bounds")
    if result.get("automatic_retry_authorized") is not False or result.get("automatic_rerun_authorized") is not False:
        raise ValueError("input permits automatic retry/rerun")

    input_cases = result.get("cases")
    if not isinstance(input_cases, list) or len(input_cases) != EXPECTED_CASE_COUNT:
        raise ValueError("input must contain exactly 16 preserved cases")
    input_index: dict[str, dict[str, Any]] = {}
    for row in input_cases:
        if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
            raise ValueError("invalid preserved case row")
        if row["case_id"] in input_index:
            raise ValueError(f"duplicate preserved case_id: {row['case_id']}")
        input_index[row["case_id"]] = row

    suite_index = {row["case_id"]: row for row in suite["cases"]}
    gold_index = {row["case_id"]: row for row in gold["cases"]}
    ordered_ids = [row["case_id"] for row in suite["cases"]]
    if set(input_index) != set(ordered_ids):
        raise ValueError("preserved result case IDs differ from frozen 16-case suite")

    case_reports: list[dict[str, Any]] = []
    parse_success = 0
    for case_id in ordered_ids:  # deliberately never stops at first case FAIL
        row: dict[str, Any] = {"case_id": case_id, "parse_passed": False}
        try:
            response = _parse_preserved_response(input_index[case_id])
            row["parse_passed"] = True
            parse_success += 1
            row["boundary_evaluation"] = evaluate_boundary(suite_index[case_id], response)
            row["gold_evaluation"] = evaluate_gold(gold_index[case_id], response)
            row["case_passed"] = row["boundary_evaluation"]["passed"] and row["gold_evaluation"]["passed"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            row["parse_error"] = f"{type(exc).__name__}: {exc}"
            row["boundary_evaluation"] = {"passed": False, "issues": []}
            row["gold_evaluation"] = {"passed": False, "not_evaluated_due_to_parse_error": True}
            row["case_passed"] = False
        case_reports.append(row)

    required_total = sum(len(_gold_set(gold_index[cid], "expected_assignments")) for cid in ordered_ids)
    missing_required_total = sum(len(row["gold_evaluation"].get("missing_required", [])) for row in case_reports)
    spurious_total = sum(len(row["gold_evaluation"].get("spurious_assignments", [])) for row in case_reports)
    forbidden_total = sum(len(row["gold_evaluation"].get("forbidden_present", [])) for row in case_reports)
    conflict_mismatches = sum(
        1 for row in case_reports
        if row["gold_evaluation"].get("conflict_candidate_match") is False
    )
    challenge_ids = list(policy.get("challenge_semantics", {}).keys())
    challenge_pass_count = sum(1 for row in case_reports if row["case_id"] in challenge_ids and row["case_passed"])
    boundary_pass_count = sum(1 for row in case_reports if row["boundary_evaluation"]["passed"])
    case_pass_count = sum(1 for row in case_reports if row["case_passed"])

    criteria = {
        "model_requests_16_of_16": result.get("observed_model_request_count") == EXPECTED_CASE_COUNT,
        "parse_success_16_of_16": parse_success == EXPECTED_CASE_COUNT,
        "contract_and_boundary_pass_16_of_16": boundary_pass_count == EXPECTED_CASE_COUNT,
        "required_gold_assignments_present_100_percent": missing_required_total == 0 and required_total > 0,
        "spurious_assignments_zero": spurious_total == 0,
        "forbidden_gold_assignments_zero": forbidden_total == 0,
        "expected_conflict_candidate_mismatches_zero": conflict_mismatches == 0,
        "challenge_cases_4_of_4": len(challenge_ids) == 4 and challenge_pass_count == 4,
        "model_authority_violations_zero": _count_issue_code(case_reports, "MODEL_AUTHORITY_VIOLATION") == 0,
        "unknown_question_ids_zero": _count_issue_code(case_reports, "UNKNOWN_QUESTION_ID") == 0,
        "unexpected_pf_question_mismatches_zero": _count_issue_code(case_reports, "PF_QUESTION_MISMATCH") == 0,
        "retry_zero": result.get("retry_count") == 0,
        "repair_false": result.get("output_repair") is False,
    }
    qualification_passed = all(criteria.values()) and case_pass_count == EXPECTED_CASE_COUNT

    return {
        "work_block": WORK_BLOCK,
        "evaluator_version": EVALUATOR_VERSION,
        "evaluation_mode": "OFFLINE_MODEL_FREE_HUMAN_GOLD_EVALUATION",
        "model_contact_attempted": False,
        "localhost_preflight_attempted": False,
        "retry_attempted": False,
        "output_repair_attempted": False,
        "automatic_rerun_attempted": False,
        "source_result": {
            "status": result.get("status"),
            "runner_version": result.get("runner_version"),
            "authorized_git_commit": result.get("authorized_git_commit"),
            "authorized_runner_blob_oid": result.get("authorized_runner_blob_oid"),
            "qualification_snapshot_sha256": result.get("qualification_snapshot_sha256"),
            "expected_model_request_count": result.get("expected_model_request_count"),
            "observed_model_request_count": result.get("observed_model_request_count"),
            "retry_count": result.get("retry_count"),
            "output_repair": result.get("output_repair"),
        },
        "frozen_bindings": {
            "human_gold_blob": EXPECTED_GOLD_BLOB,
            "qualification_policy_blob": EXPECTED_POLICY_BLOB,
            "v25_runner_blob": EXPECTED_V25_RUNNER_BLOB,
        },
        "policy_version": policy.get("policy_version"),
        "gold_version": gold.get("gold_version"),
        "summary": {
            "cases_evaluated": len(case_reports),
            "case_pass_count": case_pass_count,
            "case_fail_count": EXPECTED_CASE_COUNT - case_pass_count,
            "parse_success_count": parse_success,
            "boundary_pass_count": boundary_pass_count,
            "required_assignment_count": required_total,
            "missing_required_count": missing_required_total,
            "spurious_assignment_count": spurious_total,
            "forbidden_assignment_count": forbidden_total,
            "conflict_candidate_mismatch_count": conflict_mismatches,
            "challenge_pass_count": challenge_pass_count,
            "challenge_case_count": len(challenge_ids),
        },
        "policy_criteria": criteria,
        "cases": case_reports,
        "qualification_result": "PASS" if qualification_passed else "FAIL",
        "model_qualified": bool(qualification_passed),
        "benchmark_approved": False,
        "generalisation_approved": False,
        "real_data_approved": False,
        "pilot_approved": False,
        "production_approved": False,
        "phase_f_approved": False,
        "allowed_conclusion": policy.get("allowed_conclusion_if_passed") if qualification_passed else None,
        "forbidden_conclusions_even_if_passed": policy.get("forbidden_conclusions_even_if_passed", []),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline-only evaluator for one preserved V2.5 Ministral result JSON")
    parser.add_argument("result", type=Path, help="existing V2.5 result JSON; no model contact is performed")
    parser.add_argument("--output", type=Path, default=None, help="audit report path; defaults beside input")
    args = parser.parse_args()
    result = _load(args.result)
    report = evaluate_result(result)
    output = args.output or args.result.with_name(args.result.stem + "_human_gold_offline_report_v0_1.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["qualification_result"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
