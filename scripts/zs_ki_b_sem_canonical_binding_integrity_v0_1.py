#!/usr/bin/env python3
"""Canonical, platform-independent content bindings for future SEM authorization.

This module is strictly model-free. It performs no HTTP, localhost, preflight,
model loading, model generation or authorization. Canonical artifact identity is
anchored to immutable Git blob bytes at the explicitly bound source commit.
Worktree verification normalizes text line endings to LF so CRLF/LF checkout
settings do not change the binding.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BASE_COMMIT = "db5c2d929b76f4970057958f262ddc2c662664a8"
HASH_SEMANTICS = "UTF8_TEXT_LF_NORMALIZED_SHA256_OVER_CANONICAL_GIT_BLOB_BYTES_V0_1"
RUN_TYPE = "ZS-DEV-KI-B-SEM-CANONICAL-BINDING-INTEGRITY-REPAIR-2026-001"
RUNNER_VERSION = "canonical-binding-integrity-v0.1"

ARTIFACT_PATHS: tuple[tuple[str, str], ...] = (
    ("qualification_suite", "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"),
    ("reference_questions", "domains/zukunftscheck/rules/reference_questions_v0_1.json"),
    ("reference_question_meanings", "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"),
    ("finding_type_meanings", "domains/zukunftscheck/rules/finding_type_meanings_v0_1.json"),
    ("system_prompt", "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt"),
    ("response_schema", "domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json"),
)

RUNNER_BINDING_PATHS: tuple[tuple[str, str], ...] = (
    ("authorization_prep_v21", "scripts/zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep.py"),
    ("persistent_consumption_prep_v22", "scripts/zs_ki_b_sem_qualifikation_runner_v2_2_persistent_consumption_prep.py"),
)

EXPECTED_ORDERED_CASE_IDS: tuple[str, ...] = (
    "ZS-KI-B-SEM-V07-Q-PF1-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF2-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF3-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF4-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF5-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF6-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF7-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF8-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF9-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF10-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF11-SYN-001",
    "ZS-KI-B-SEM-V07-Q-PF12-SYN-001",
    "ZS-KI-B-SEM-V07-Q-CHALLENGE-DOC-SYN-001",
    "ZS-KI-B-SEM-V07-Q-CHALLENGE-UNSUPPORTED-SYN-001",
    "ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001",
    "ZS-KI-B-SEM-V07-Q-CHALLENGE-POSSIBLE-DATE-SYN-001",
)


def canonicalize_utf8_text_bytes(data: bytes) -> bytes:
    """Return UTF-8 bytes with CRLF and bare CR normalized to LF.

    No JSON reformatting, key sorting, whitespace collapsing or semantic repair is
    performed. Therefore every content change other than text line-ending encoding
    remains binding-relevant.
    """
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def canonical_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(canonicalize_utf8_text_bytes(data)).hexdigest()


def canonical_worktree_sha256(path: Path) -> str:
    return canonical_sha256_bytes(path.read_bytes())


def _git(*args: str, root: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def git_blob_oid(commit: str, path: str, *, root: Path = ROOT) -> str:
    return _git("rev-parse", f"{commit}:{path}", root=root).decode("ascii").strip()


def git_blob_bytes(commit: str, path: str, *, root: Path = ROOT) -> bytes:
    return _git("cat-file", "blob", git_blob_oid(commit, path, root=root), root=root)


def canonical_git_blob_sha256(commit: str, path: str, *, root: Path = ROOT) -> str:
    """SHA-256 over immutable repository blob bytes, with explicit text LF semantics."""
    return canonical_sha256_bytes(git_blob_bytes(commit, path, root=root))


def _ordered_case_ids_from_bytes(data: bytes) -> tuple[str, ...]:
    suite = json.loads(canonicalize_utf8_text_bytes(data).decode("utf-8"))
    cases = suite.get("cases")
    if not isinstance(cases, list):
        raise ValueError("qualification suite cases must be a list")
    ids = tuple(case.get("case_id") for case in cases if isinstance(case, dict))
    if len(ids) != len(cases) or any(not isinstance(case_id, str) for case_id in ids):
        raise ValueError("qualification suite contains an invalid case_id")
    return ids


def _stable_json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_binding_snapshot(*, root: Path = ROOT) -> dict[str, Any]:
    artifacts: list[dict[str, str]] = []
    for role, path in ARTIFACT_PATHS:
        artifacts.append(
            {
                "role": role,
                "path": path,
                "git_blob_oid": git_blob_oid(SOURCE_BASE_COMMIT, path, root=root),
                "canonical_sha256": canonical_git_blob_sha256(SOURCE_BASE_COMMIT, path, root=root),
            }
        )

    runners: list[dict[str, str]] = []
    for role, path in RUNNER_BINDING_PATHS:
        runners.append(
            {
                "role": role,
                "path": path,
                "git_blob_oid": git_blob_oid(SOURCE_BASE_COMMIT, path, root=root),
                "canonical_sha256": canonical_git_blob_sha256(SOURCE_BASE_COMMIT, path, root=root),
            }
        )

    suite_path = dict(ARTIFACT_PATHS)["qualification_suite"]
    ordered_case_ids = _ordered_case_ids_from_bytes(git_blob_bytes(SOURCE_BASE_COMMIT, suite_path, root=root))
    if ordered_case_ids != EXPECTED_ORDERED_CASE_IDS:
        raise PermissionError("bound source commit does not contain the expected ordered 16-case suite")

    case_order_sha256 = _stable_json_sha256(list(ordered_case_ids))
    qualification_snapshot = {
        "source_base_commit": SOURCE_BASE_COMMIT,
        "hash_semantics": HASH_SEMANTICS,
        "artifacts": artifacts,
        "runner_bindings": runners,
        "ordered_case_ids": list(ordered_case_ids),
        "ordered_case_ids_sha256": case_order_sha256,
    }
    qualification_snapshot_sha256 = _stable_json_sha256(qualification_snapshot)

    return {
        **qualification_snapshot,
        "qualification_snapshot_sha256": qualification_snapshot_sha256,
    }


def validate_current_worktree_binding(*, root: Path = ROOT) -> dict[str, bool]:
    snapshot = build_binding_snapshot(root=root)
    checks: dict[str, bool] = {}
    for artifact in snapshot["artifacts"]:
        path = root / artifact["path"]
        checks[f"artifact_{artifact['role']}_exact"] = (
            path.is_file() and canonical_worktree_sha256(path) == artifact["canonical_sha256"]
        )

    suite_path = root / dict(ARTIFACT_PATHS)["qualification_suite"]
    current_ids = _ordered_case_ids_from_bytes(suite_path.read_bytes()) if suite_path.is_file() else ()
    checks["ordered_case_ids_exact"] = current_ids == EXPECTED_ORDERED_CASE_IDS
    checks["ordered_case_count_16"] = len(current_ids) == 16
    return checks


def build_integrity_report(*, root: Path = ROOT) -> dict[str, Any]:
    snapshot = build_binding_snapshot(root=root)
    checks = validate_current_worktree_binding(root=root)
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_CANONICAL_BINDING_INTEGRITY_REPAIR",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "run_type": RUN_TYPE,
        "runner_version": RUNNER_VERSION,
        "hash_semantics": HASH_SEMANTICS,
        "source_base_commit": SOURCE_BASE_COMMIT,
        "checks": checks,
        "binding_snapshot": snapshot,
        "binding_ready_for_future_single_use_authorization": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "preflight_authorized": False,
        "authorization_artifact_created": False,
        "model_qualified": False,
    }


def validate_execution_authorization() -> dict[str, Any]:
    raise PermissionError("canonical binding integrity repair is model-free; no execution authorization exists")


def main() -> int:
    report = build_integrity_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
