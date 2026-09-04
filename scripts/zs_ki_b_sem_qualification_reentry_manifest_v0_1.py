#!/usr/bin/env python3
"""Model-free re-entry manifest for synthetic SEM qualification after V42.

This module composes existing frozen/canonical qualification content with the
current V25 live-runner constraints. It creates no authorization and performs
no model contact.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_MAIN_COMMIT = "a3bdf89d4aab82e346a1bdec37285743efc993d8"
MANIFEST_VERSION = "ZS-KI-B-SEM-QUALIFICATION-REENTRY-MANIFEST-2026-001_v0.1"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFICATION-REENTRY-PREP-2026-001"
SOURCE_INTEGRITY_BLOB_SHA = "1b7d5f81995036561718885555fe793bd05c15c6"
SOURCE_V25_RUNNER_BLOB_SHA = "9ac29c25b47cbd7762a3d8ee30de7f72e20ae866"
V07_FREEZE_MANIFEST_BLOB_SHA = "e79be6a40bc2bfd7498bc32399301b03a62c2275"
RESIDUAL_ARCHITECTURE_ISSUE = 130

INTEGRITY_PATH = "scripts/zs_ki_b_sem_canonical_binding_integrity_v0_1.py"
V25_RUNNER_PATH = "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"
FREEZE_PATH = "tests/fixtures/zs_ki_b_sem_v07_qualification_freeze_manifest_v0_1.json"
HUMAN_GOLD_PATH = "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
QUALIFICATION_POLICY_PATH = "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"
EXPECTED_HUMAN_GOLD_BLOB_SHA = "704adbd930c042b132a34bb9ddc95b4531f336b2"
EXPECTED_POLICY_BLOB_SHA = "9bc06b2648b05f9bb1d464e019e23f8afd82570b"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("ascii").strip()


def _git_blob_at(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _git_text_blob_sha1(path: Path) -> str:
    try:
        data = path.read_bytes().replace(b"\r\n", b"\n")
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError(f"cannot read re-entry source: {path}") from exc
    if b"\r" in data:
        raise PermissionError("re-entry source contains bare CR bytes")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _require_worktree_blob(path: str, expected: str, label: str) -> None:
    if _git_text_blob_sha1(ROOT / path) != expected:
        raise PermissionError(f"{label} worktree blob mismatch")


def _validate_sources_before_import() -> None:
    checks = {
        ROOT / INTEGRITY_PATH: SOURCE_INTEGRITY_BLOB_SHA,
        ROOT / V25_RUNNER_PATH: SOURCE_V25_RUNNER_BLOB_SHA,
    }
    for path, expected in checks.items():
        if _git_text_blob_sha1(path) != expected:
            raise PermissionError(f"re-entry source blob mismatch: {path.name}")


_validate_sources_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 as integrity
import scripts.zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep as v25


def _stable_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_frozen_supplements() -> dict[str, Any]:
    expected_git = {
        FREEZE_PATH: V07_FREEZE_MANIFEST_BLOB_SHA,
        HUMAN_GOLD_PATH: EXPECTED_HUMAN_GOLD_BLOB_SHA,
        QUALIFICATION_POLICY_PATH: EXPECTED_POLICY_BLOB_SHA,
    }
    for path, expected in expected_git.items():
        if _git_blob_at(BASE_MAIN_COMMIT, path) != expected:
            raise PermissionError(f"bound main artifact changed: {path}")
        _require_worktree_blob(path, expected, path)

    freeze = json.loads((ROOT / FREEZE_PATH).read_text(encoding="utf-8"))
    if freeze.get("status") != "HUMAN_APPROVED_FROZEN":
        raise PermissionError("human-approved qualification freeze missing")
    if freeze.get("model_execution_authorized") is not False:
        raise PermissionError("freeze manifest must not authorize execution")
    artifacts = freeze.get("artifacts", {})
    if artifacts.get("human_gold", {}).get("git_blob_sha") != EXPECTED_HUMAN_GOLD_BLOB_SHA:
        raise PermissionError("freeze human-gold binding mismatch")
    if artifacts.get("human_gold", {}).get("model_visible") is not False:
        raise PermissionError("human gold must remain model-invisible")
    if artifacts.get("qualification_policy", {}).get("git_blob_sha") != EXPECTED_POLICY_BLOB_SHA:
        raise PermissionError("freeze qualification-policy binding mismatch")
    return freeze


def build_reentry_manifest() -> dict[str, Any]:
    _validate_sources_before_import()
    freeze = _validate_frozen_supplements()
    snapshot = integrity.build_binding_snapshot()
    checks = integrity.validate_current_worktree_binding()
    if not checks or not all(checks.values()):
        raise PermissionError("canonical qualification binding is not exact")
    if tuple(snapshot["ordered_case_ids"]) != integrity.EXPECTED_ORDERED_CASE_IDS:
        raise PermissionError("re-entry ordered case IDs changed")
    if len(snapshot["ordered_case_ids"]) != 16:
        raise PermissionError("re-entry requires exact 16-case suite")
    if v25.EXPECTED_MODEL_REQUEST_COUNT != 16 or v25.MAX_TOKENS != 2048:
        raise PermissionError("V25 request bounds changed")
    if v25.RETRY_COUNT != 0 or v25.OUTPUT_REPAIR is not False:
        raise PermissionError("V25 retry/repair boundary changed")
    model_id = v25.v24.v23.v19.EXPECTED_MODEL_ID
    if model_id != "qwen3-14b":
        raise PermissionError("model binding changed")
    if v25.BASE_URL != "http://127.0.0.1:1234/v1":
        raise PermissionError("loopback binding changed")

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "run_type": RUN_TYPE,
        "status": "PREPARED_NOT_AUTHORIZED",
        "base_main_commit": BASE_MAIN_COMMIT,
        "residual_architecture_issue": RESIDUAL_ARCHITECTURE_ISSUE,
        "source_integrity_blob_sha": SOURCE_INTEGRITY_BLOB_SHA,
        "source_v25_runner_blob_sha": SOURCE_V25_RUNNER_BLOB_SHA,
        "qualification_snapshot_sha256": snapshot["qualification_snapshot_sha256"],
        "ordered_case_ids_sha256": snapshot["ordered_case_ids_sha256"],
        "ordered_case_ids": snapshot["ordered_case_ids"],
        "qualification_case_count": 16,
        "human_gold": {
            "path": HUMAN_GOLD_PATH,
            "git_blob_sha": EXPECTED_HUMAN_GOLD_BLOB_SHA,
            "freeze_status": freeze["status"],
            "model_visible": False,
        },
        "qualification_policy": {
            "path": QUALIFICATION_POLICY_PATH,
            "git_blob_sha": EXPECTED_POLICY_BLOB_SHA,
        },
        "canonical_artifacts": snapshot["artifacts"],
        "model": model_id,
        "runner_path": V25_RUNNER_PATH,
        "runner_version": v25.RUNNER_VERSION,
        "required_base_url": v25.BASE_URL,
        "timeout_seconds": v25.TIMEOUT_SECONDS,
        "max_tokens": v25.MAX_TOKENS,
        "expected_model_request_count": v25.EXPECTED_MODEL_REQUEST_COUNT,
        "retry_count": v25.RETRY_COUNT,
        "output_repair": v25.OUTPUT_REPAIR,
        "synthetic_only": True,
        "human_review_required_after_run": True,
        "human_gold_evaluation": "NOT_STARTED",
        "authorization_gate": {
            "state": "CLOSED",
            "explicit_user_single_run_approval_required": True,
            "no_execution_from_manifest": True,
        },
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
        "benchmark_approved": False,
        "pilot_approved": False,
        "production_approved": False,
    }
    manifest["manifest_sha256"] = _stable_sha256(manifest)
    return manifest


def validate_reentry_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    expected = build_reentry_manifest()
    if manifest != expected:
        raise PermissionError("re-entry manifest mismatch")
    return manifest


def build_report() -> dict[str, Any]:
    manifest = build_reentry_manifest()
    return {
        "mode": "MODEL_FREE_QUALIFICATION_REENTRY_PREP",
        "status": "PASS",
        "manifest_sha256": manifest["manifest_sha256"],
        "qualification_case_count": manifest["qualification_case_count"],
        "model": manifest["model"],
        "max_tokens": manifest["max_tokens"],
        "retry_count": manifest["retry_count"],
        "output_repair": manifest["output_repair"],
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
