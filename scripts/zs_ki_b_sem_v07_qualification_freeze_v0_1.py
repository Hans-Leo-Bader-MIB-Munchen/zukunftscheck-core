#!/usr/bin/env python3
"""Validate the human-approved frozen v0.7 SEM qualification bundle without model contact."""
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

FREEZE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_freeze_manifest_v0_1.json"
EXPECTED_STATUS = "HUMAN_APPROVED_FROZEN"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    completed = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip().lower()


def current_git_commit() -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, check=True, capture_output=True, text=True)
    if status.stdout.strip():
        raise RuntimeError("working tree must be clean for auditable freeze validation")
    return completed.stdout.strip().lower()


def validate_freeze_bundle() -> dict[str, Any]:
    freeze = load(FREEZE_PATH)
    if freeze.get("status") != EXPECTED_STATUS:
        raise ValueError("freeze manifest must be HUMAN_APPROVED_FROZEN")
    if freeze.get("model_execution_authorized") is not False:
        raise ValueError("freeze must not authorize model execution")

    artifacts = freeze.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("freeze artifacts missing")

    for name, spec in artifacts.items():
        path = ROOT / str(spec.get("path"))
        if not path.exists():
            raise ValueError(f"{name}: frozen artifact missing")
        expected_sha = str(spec.get("git_blob_sha", ""))
        if git_blob_sha(path) != expected_sha:
            raise ValueError(f"{name}: frozen artifact blob hash mismatch")

    suite = load(ROOT / artifacts["qualification_suite"]["path"])
    gold = load(ROOT / artifacts["human_gold"]["path"])
    policy = load(ROOT / artifacts["qualification_policy"]["path"])

    if suite.get("status") != EXPECTED_STATUS or gold.get("status") != EXPECTED_STATUS or policy.get("status") != EXPECTED_STATUS:
        raise ValueError("suite, gold and policy must all be HUMAN_APPROVED_FROZEN")
    if gold.get("model_visible") is not False:
        raise ValueError("frozen human gold must remain model_visible=false")
    if len(suite.get("cases", [])) != 16 or len(gold.get("cases", [])) != 16:
        raise ValueError("frozen suite and gold must contain exactly 16 cases")
    suite_ids = [row.get("case_id") for row in suite["cases"]]
    gold_ids = [row.get("case_id") for row in gold["cases"]]
    if suite_ids != gold_ids or len(set(suite_ids)) != 16:
        raise ValueError("frozen suite/gold case ids must be identical and unique")

    preconditions = policy.get("preconditions_for_future_execution", {})
    criteria = policy.get("pass_criteria", {})
    if preconditions.get("explicit_user_model_run_approval_required") is not True:
        raise ValueError("future execution must require explicit user approval")
    if preconditions.get("qualification_evaluator_must_enforce_optional_and_spurious_assignments") is not True:
        raise ValueError("future evaluator must enforce optional/spurious assignments")
    if preconditions.get("qualification_evaluator_must_enforce_expected_conflict_candidate") is not True:
        raise ValueError("future evaluator must enforce expected_conflict_candidate")
    if criteria.get("spurious_assignments_outside_required_or_optional_allowed") != 0:
        raise ValueError("frozen policy must allow zero spurious assignments")
    if criteria.get("expected_conflict_candidate_mismatches_allowed") != 0:
        raise ValueError("frozen policy must allow zero conflict-candidate mismatches")

    return {
        "freeze_version": freeze["freeze_version"],
        "status": freeze["status"],
        "case_count": len(suite_ids),
        "pf_coverage": freeze["qualification_pf_coverage"],
        "challenge_case_count": freeze["challenge_case_count"],
        "model_execution_authorized": freeze["model_execution_authorized"],
    }


def build_manifest() -> dict[str, Any]:
    validated = validate_freeze_bundle()
    return {
        "mode": "VALIDATED_SEM_V0_7_QUALIFICATION_FREEZE_MODEL_FREE",
        "manifest": {
            **validated,
            "git_commit": current_git_commit(),
            "expected_run_count": 0,
            "expected_model_request_count": 0,
            "observed_run_count": 0,
            "observed_model_request_count": 0,
            "execution_attempted": False,
            "model_qualified": False,
            "benchmark_approved": False,
            "generalisation_approved": False,
            "real_data_approved": False,
            "pilot_approved": False,
            "production_approved": False,
            "phase_f_approved": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    validate_freeze_bundle()
    if args.execute:
        parser.error("model execution is disabled in the frozen pre-run block; a separately versioned executable qualification runner and explicit model-run approval are required")
    print(json.dumps(build_manifest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
