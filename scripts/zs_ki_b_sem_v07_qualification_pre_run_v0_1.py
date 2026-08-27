#!/usr/bin/env python3
"""Model-free pre-run validator for the first broad v0.7 SEM qualification suite."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.smoketest import canonical_json, sha256_text
import scripts.zs_ki_b_sem_qualifikation_runner_v0_7 as runtime

PRE_RUN_VERSION = "ZS-DEV-KI-B-SEM-V0-7-QUALIFIKATION-PRE-RUN-2026-001_v0.1"
SUITE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_qualification_suite_draft_v0_1.json"
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_draft_v0_1.json"
POLICY_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_qualification_policy_draft_v0_1.json"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
EXPECTED_PFS = {f"PF{i}" for i in range(1, 13)}
EXPECTED_CASE_COUNT = 16


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_git_commit() -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, check=True, capture_output=True, text=True)
    if status.stdout.strip():
        raise RuntimeError("working tree must be clean for auditable pre-run")
    return completed.stdout.strip().lower()


def _validate_assignment(assignment: dict[str, Any], canonical_pf: dict[str, str], case_id: str) -> str:
    qid = assignment.get("question_id")
    pf_id = assignment.get("pf_id")
    if qid not in canonical_pf or canonical_pf[qid] != pf_id:
        raise ValueError(f"{case_id}: invalid gold question/PF binding")
    return pf_id


def validate_pre_run_bundle() -> dict[str, Any]:
    runtime_binding = runtime.validate_runtime_binding()
    suite = load(SUITE_PATH)
    gold = load(GOLD_PATH)
    policy = load(POLICY_PATH)
    questions = load(QUESTIONS_PATH)["questions"]
    canonical_pf = {row["question_id"]: row["pf_id"] for row in questions}

    if suite.get("data_class") != "SYNTHETIC_ONLY" or gold.get("data_class") != "SYNTHETIC_ONLY":
        raise ValueError("qualification suite and gold must be SYNTHETIC_ONLY")
    cases = suite.get("cases")
    gold_cases = gold.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ValueError("qualification suite must contain exactly 16 cases")
    if not isinstance(gold_cases, list) or len(gold_cases) != EXPECTED_CASE_COUNT:
        raise ValueError("human-gold draft must contain exactly 16 cases")

    case_ids = [case.get("case_id") for case in cases]
    gold_ids = [case.get("case_id") for case in gold_cases]
    if len(set(case_ids)) != EXPECTED_CASE_COUNT or case_ids != gold_ids:
        raise ValueError("suite/gold case ids must be unique and identically ordered")

    suite_pfs: set[str] = set()
    challenge_count = 0
    for case, expected in zip(cases, gold_cases):
        case_id = str(case.get("case_id"))
        if case.get("data_class") != "SYNTHETIC_ONLY":
            raise ValueError(f"{case_id}: data_class must be SYNTHETIC_ONLY")
        locations = case.get("source_locations")
        if not isinstance(locations, list) or not locations:
            raise ValueError(f"{case_id}: source_locations missing")
        if case.get("target_source_location_id") not in {row.get("source_location_id") for row in locations}:
            raise ValueError(f"{case_id}: target source location missing")
        if any(key.startswith("expected_") or key.startswith("forbidden_") for key in case):
            raise ValueError(f"{case_id}: gold information must not be model-visible")
        assignments = expected.get("expected_assignments")
        if not isinstance(assignments, list) or not assignments:
            raise ValueError(f"{case_id}: expected assignments missing")
        for assignment in assignments:
            suite_pfs.add(_validate_assignment(assignment, canonical_pf, case_id))
        forbidden = expected.get("forbidden_assignments", [])
        if not isinstance(forbidden, list):
            raise ValueError(f"{case_id}: forbidden_assignments must be a list")
        for assignment in forbidden:
            _validate_assignment(assignment, canonical_pf, case_id)
        if "CHALLENGE" in case_id:
            challenge_count += 1

    if suite_pfs != EXPECTED_PFS:
        raise ValueError("qualification suite must span PF1-PF12 in its gold expectations")
    if challenge_count != 4:
        raise ValueError("qualification suite must contain exactly four explicit challenge cases")
    if gold.get("model_visible") is not False:
        raise ValueError("human gold must be explicitly model_visible=false")
    if gold.get("status") != "DRAFT_NOT_HUMAN_APPROVED":
        raise ValueError("this pre-run block requires unapproved draft gold")
    if policy.get("status") != "DRAFT_NOT_HUMAN_APPROVED":
        raise ValueError("qualification policy must remain draft until explicit human approval")
    criteria = policy.get("pass_criteria", {})
    if criteria.get("model_requests_expected") != EXPECTED_CASE_COUNT:
        raise ValueError("qualification policy model request count must equal suite case count")
    if criteria.get("parse_success_required") != "16/16" or criteria.get("contract_and_boundary_pass_required") != "16/16":
        raise ValueError("qualification policy must require 16/16 parse and boundary success")
    if policy.get("preconditions_for_future_execution", {}).get("explicit_user_model_run_approval_required") is not True:
        raise ValueError("qualification policy must require explicit user model-run approval")

    return {
        "runtime_binding": runtime_binding["binding_version"],
        "case_count": len(cases),
        "challenge_case_count": challenge_count,
        "pf_coverage": "12/12",
        "human_gold_status": gold["status"],
        "policy_status": policy["status"],
    }


def build_manifest() -> dict[str, Any]:
    validation = validate_pre_run_bundle()
    runtime_manifest = runtime.build_dry_run_manifest(model="", base_url="http://127.0.0.1:1234/v1")["manifest"]
    return {
        "mode": "DRY_RUN_SEM_V0_7_QUALIFICATION_PRE_RUN",
        "manifest": {
            "pre_run_version": PRE_RUN_VERSION,
            "git_commit": current_git_commit(),
            "runtime_binding_version": validation["runtime_binding"],
            "runner_version": runtime_manifest["runner_version"],
            "prompt_version": runtime_manifest["prompt_version"],
            "contract_version": runtime_manifest["contract_version"],
            "meaning_layer_schema_version": runtime_manifest["meaning_layer_schema_version"],
            "meaning_layer_coverage": runtime_manifest["meaning_layer_coverage"],
            "qualification_suite": SUITE_PATH.name,
            "qualification_suite_sha256": sha256_text(canonical_json(load(SUITE_PATH))),
            "human_gold": GOLD_PATH.name,
            "human_gold_sha256": sha256_text(canonical_json(load(GOLD_PATH))),
            "human_gold_status": validation["human_gold_status"],
            "human_gold_model_visible": False,
            "qualification_policy": POLICY_PATH.name,
            "qualification_policy_sha256": sha256_text(canonical_json(load(POLICY_PATH))),
            "qualification_policy_status": validation["policy_status"],
            "qualification_case_count": validation["case_count"],
            "qualification_challenge_case_count": validation["challenge_case_count"],
            "qualification_pf_coverage": validation["pf_coverage"],
            "expected_run_count": 0,
            "expected_model_request_count": 0,
            "observed_run_count": 0,
            "observed_model_request_count": 0,
            "execution_attempted": False,
            "model_execution_enabled": False,
            "data_class": "SYNTHETIC_ONLY",
            "retry_count": 0,
            "output_repair": False,
            "tools": False,
            "web": False,
            "MCP": False,
            "remote_cloud": False,
            "real_data": False,
            "model_qualified": False,
            "benchmark_approved": False,
            "generalisation_approved": False,
            "pilot_approved": False,
            "production_approved": False,
            "phase_f_approved": False
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    validate_pre_run_bundle()
    if args.execute:
        parser.error("model execution is disabled in the v0.7 qualification pre-run block; human-gold approval and a separately versioned executable qualification runner are required")
    print(json.dumps(build_manifest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
