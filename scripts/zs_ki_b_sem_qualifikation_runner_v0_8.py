#!/usr/bin/env python3
"""Executable, fail-closed v0.7 semantic qualification runner.

Binds the HUMAN_APPROVED_FROZEN 16-case suite, gold and policy. Dry-run is
model-free. --execute is blocked unless a separately versioned explicit model-run
authorization artifact exists and matches this frozen qualification package.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2
from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_5 import build_response_format, chat_completion_structured
from llm.smoketest import canonical_json, parse_model_json, sha256_text

RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V0-7-FROZEN-2026-008"
RUNNER_VERSION = "v0.8"
PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_5"
CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"
EXPECTED_RUN_COUNT = 1
EXPECTED_MODEL_REQUEST_COUNT = 16
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_8.json"

PROMPT_PATH = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_5.txt"
QUESTIONS_PATH = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
FINDING_TYPES_PATH = ROOT / "domains/zukunftscheck/rules/finding_type_meanings_v0_1.json"
SUITE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"
GOLD_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"
FREEZE_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_freeze_manifest_v0_1.json"
AUTH_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_v07_model_run_authorization_v0_1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_git_commit() -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, check=True, capture_output=True, text=True)
    if status.stdout.strip():
        raise RuntimeError("working tree must be clean for auditable qualification run")
    commit = completed.stdout.strip().lower()
    if len(commit) != 40:
        raise RuntimeError("invalid git commit")
    return commit


def _git_blob_sha(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    completed = subprocess.run(["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, check=True, capture_output=True, text=True)
    return completed.stdout.strip().lower()


def validate_frozen_package() -> dict[str, Any]:
    suite, gold, policy, freeze = map(load, (SUITE_PATH, GOLD_PATH, POLICY_PATH, FREEZE_PATH))
    if suite.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("qualification suite is not HUMAN_APPROVED_FROZEN")
    if gold.get("status") != "HUMAN_APPROVED_FROZEN" or gold.get("model_visible") is not False:
        raise ValueError("human gold must be HUMAN_APPROVED_FROZEN and model_visible=false")
    if policy.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("qualification policy is not HUMAN_APPROVED_FROZEN")
    if freeze.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("freeze manifest is not HUMAN_APPROVED_FROZEN")
    if len(suite.get("cases", [])) != 16 or len(gold.get("cases", [])) != 16:
        raise ValueError("frozen suite/gold must contain exactly 16 cases")
    if [c["case_id"] for c in suite["cases"]] != [c["case_id"] for c in gold["cases"]]:
        raise ValueError("frozen suite/gold case ordering mismatch")
    for key, path in (("qualification_suite", SUITE_PATH), ("human_gold", GOLD_PATH), ("qualification_policy", POLICY_PATH)):
        if freeze["artifacts"][key]["git_blob_sha"] != _git_blob_sha(path):
            raise ValueError(f"freeze manifest blob mismatch: {key}")
    return {"suite": suite, "gold": gold, "policy": policy, "freeze": freeze}


def validate_execution_authorization() -> dict[str, Any]:
    if not AUTH_PATH.exists():
        raise PermissionError("explicit model-run authorization artifact is absent")
    auth = load(AUTH_PATH)
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("model-run authorization status is not EXPLICIT_USER_APPROVED")
    if auth.get("run_type") != RUN_TYPE or auth.get("expected_model_request_count") != 16:
        raise PermissionError("model-run authorization does not match runner scope")
    if auth.get("synthetic_only") is not True or auth.get("local_loopback_only") is not True:
        raise PermissionError("model-run authorization must remain synthetic-only and loopback-only")
    if auth.get("single_run_only") is not True or auth.get("retry_count") != 0 or auth.get("output_repair") is not False:
        raise PermissionError("model-run authorization violates frozen run constraints")
    return auth


def build_messages(case: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
    payload = {
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "target_source_location_id": case["target_source_location_id"],
        "source_locations": case["source_locations"],
        "reference_questions": load(QUESTIONS_PATH)["questions"],
        "reference_question_meanings": load(MEANINGS_PATH),
        "finding_type_meanings": load(FINDING_TYPES_PATH)["finding_types"],
    }
    return [{"role": "system", "content": prompt_text}, {"role": "user", "content": canonical_json(payload)}]


def evaluate_boundary(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    allowed = {row["source_location_id"] for row in case["source_locations"]}
    target = case["target_source_location_id"]
    issues = validate_semantic_response_v0_2(response, allowed_source_location_ids=allowed, target_source_location_id=target)
    return {"passed": not issues and response.get("source_location_id") == target, "issues": [i.to_dict() for i in issues]}


def _assignment_set(response: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for proposal in response.get("proposals", []):
        for assignment in proposal.get("assignment_candidates", []):
            result.add((assignment["question_id"], assignment["pf_id"]))
    return result


def _gold_set(case_gold: dict[str, Any], key: str) -> set[tuple[str, str]]:
    return {(row["question_id"], row["pf_id"]) for row in case_gold.get(key, [])}


def evaluate_gold(case_gold: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    actual = _assignment_set(response)
    required = _gold_set(case_gold, "expected_assignments")
    optional = _gold_set(case_gold, "optional_assignments")
    forbidden = _gold_set(case_gold, "forbidden_assignments")
    missing = required - actual
    forbidden_present = forbidden & actual
    spurious = actual - required - optional
    conflict_actual = any(bool(p.get("conflict_candidate_refs")) for p in response.get("proposals", []))
    conflict_expected = case_gold.get("expected_conflict_candidate")
    conflict_match = True if conflict_expected is None else conflict_actual is bool(conflict_expected)
    passed = not missing and not forbidden_present and not spurious and conflict_match
    return {
        "passed": passed,
        "actual_assignments": sorted(actual),
        "missing_required": sorted(missing),
        "forbidden_present": sorted(forbidden_present),
        "spurious_assignments": sorted(spurious),
        "expected_conflict_candidate": conflict_expected,
        "actual_conflict_candidate": conflict_actual,
        "conflict_candidate_match": conflict_match,
    }


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    package = validate_frozen_package()
    base_url = validate_local_base_url(base_url)
    response_format = build_response_format()
    return {
        "mode": "DRY_RUN_SEM_QUALIFICATION_V0_8",
        "manifest": {
            "run_type": RUN_TYPE,
            "runner_version": RUNNER_VERSION,
            "expected_run_count": EXPECTED_RUN_COUNT,
            "observed_run_count": 0,
            "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
            "observed_model_request_count": 0,
            "git_commit": current_git_commit(),
            "prompt_version": PROMPT_VERSION,
            "prompt_sha256": sha256_text(PROMPT_PATH.read_text(encoding="utf-8")),
            "contract_version": CONTRACT_VERSION,
            "meaning_layer": "reference_question_meanings_v0_7.json/67-of-67",
            "meaning_layer_sha256": sha256_text(canonical_json(load(MEANINGS_PATH))),
            "suite_version": package["suite"]["suite_version"],
            "gold_version": package["gold"]["gold_version"],
            "policy_version": package["policy"]["policy_version"],
            "freeze_version": package["freeze"]["freeze_version"],
            "response_format_sha256": sha256_text(canonical_json(response_format)),
            "data_class": "SYNTHETIC_ONLY",
            "retry_count": 0,
            "output_repair": False,
            "remote_cloud": False,
            "real_data": False,
            "base_url": base_url,
            "model": model or None,
            "execution_attempted": False,
            "execution_authorized": AUTH_PATH.exists(),
            "model_qualified": False,
            "benchmark_approved": False,
            "generalisation_approved": False,
            "pilot_approved": False,
            "production_approved": False,
            "phase_f_approved": False,
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
    }


def _persist(payload: dict[str, Any], output: str) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    Path(output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    aggregate = build_dry_run_manifest(model=args.model, base_url=args.base_url)
    if not args.execute:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
        return 0
    try:
        validate_execution_authorization()
    except PermissionError as exc:
        parser.error(str(exc))
    if not args.model.strip():
        parser.error("--model ist zusammen mit --execute erforderlich")

    package = validate_frozen_package()
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    gold_index = {row["case_id"]: row for row in package["gold"]["cases"]}
    aggregate["mode"] = "EXECUTING_SEM_QUALIFICATION_V0_8"
    aggregate["cases"] = []
    manifest = aggregate["manifest"]
    manifest["execution_attempted"] = True
    manifest["execution_authorized"] = True
    manifest["observed_run_count"] = 1

    for case in package["suite"]["cases"]:
        manifest["observed_model_request_count"] += 1
        row: dict[str, Any] = {"case_id": case["case_id"], "model_response_raw": None, "model_response": None}
        aggregate["cases"].append(row)
        try:
            content, envelope = chat_completion_structured(base_url=args.base_url, model=args.model, messages=build_messages(case, prompt_text), temperature=0.0)
        except LocalModelError as exc:
            row["endpoint_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_8"
            _persist(aggregate, args.output)
            return 2
        row["model_response_raw"] = content
        row["provider_envelope_metadata"] = {"id": envelope.get("id"), "model": envelope.get("model"), "created": envelope.get("created"), "usage": envelope.get("usage")}
        try:
            response = parse_model_json(content)
        except (json.JSONDecodeError, ValueError) as exc:
            row["parse_error"] = f"{type(exc).__name__}: {exc}"
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_8"
            _persist(aggregate, args.output)
            return 2
        row["model_response"] = response
        row["boundary_evaluation"] = evaluate_boundary(case, response)
        if not row["boundary_evaluation"]["passed"]:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_8"
            _persist(aggregate, args.output)
            return 2
        row["gold_evaluation"] = evaluate_gold(gold_index[case["case_id"]], response)
        if not row["gold_evaluation"]["passed"]:
            aggregate["mode"] = "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V0_8"
            _persist(aggregate, args.output)
            return 3
        _persist(aggregate, args.output)

    aggregate["mode"] = "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V0_8"
    aggregate["technical_boundary_pass"] = True
    aggregate["frozen_gold_pass"] = True
    aggregate["allowed_conclusion"] = package["policy"]["allowed_conclusion_if_passed"]
    aggregate["forbidden_conclusions"] = package["policy"]["forbidden_conclusions_even_if_passed"]
    _persist(aggregate, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
