#!/usr/bin/env python3
"""Model-free pre-run package for one future synthetic Ministral qualification run.

This module records no approval, creates no executable authorization and performs
no model contact. It freezes the current main commit, the qualification re-entry
manifest and the relevant authorization/gate/consumption source chain.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_MAIN_COMMIT = "28c582ab3b075298c5ca029f74005e1a8928fa9d"
PACKAGE_VERSION = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-PRERUN-PACKAGE-2026-001_v0.1"
RUN_TYPE = "ZS-KI-B-SEM-MINISTRAL-QUALIFICATION-SYNTHETIC-ONE-RUN-2026-001"
REENTRY_PATH = "scripts/zs_ki_b_sem_qualification_reentry_manifest_v0_1.py"
REENTRY_BLOB_SHA = "1f11af89eb75349d2c3cf098800c397ad4f0d9a6"
EXPECTED_RUNTIME_MODEL_ID = "ministral-3-14b-instruct-2512"
EXPECTED_MODEL_REPOSITORY = "mistralai/Ministral-3-14B-Instruct-2512-GGUF"
RESIDUAL_ARCHITECTURE_ISSUE = 130

SECURITY_SOURCE_PATHS: tuple[tuple[str, str], ...] = (
    ("v25_live_runner", "scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py"),
    ("v26_one_shot_authorization", "scripts/zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep.py"),
    ("v27_approval_ceremony", "scripts/zs_ki_b_sem_approval_ceremony_v2_7_architecture_prep.py"),
    ("v28_execution_gate", "scripts/zs_ki_b_sem_execution_gate_v2_8_integration_prep.py"),
    ("v29_run_authorization_transform", "scripts/zs_ki_b_sem_run_authorization_v2_9_transform_prep.py"),
    ("v30_proof_enforcing_live_gate", "scripts/zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep.py"),
    ("v31_authority_state_atomic_consume", "scripts/zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep.py"),
    ("v32_external_state_atomic_consume", "scripts/zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep.py"),
    ("v33_canonical_store_toctou", "scripts/zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep.py"),
    ("v42_authority_root_attestation", "scripts/zs_ki_b_sem_external_trust_anchor_provenance_authority_attestation_v4_2_prep.py"),
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("ascii").strip()


def _blob_at(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _text_blob_sha1(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise PermissionError(f"bare CR in source: {path}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _stable_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_reentry_source_before_import() -> None:
    if _blob_at(BASE_MAIN_COMMIT, REENTRY_PATH) != REENTRY_BLOB_SHA:
        raise PermissionError("bound main re-entry blob changed")
    if _text_blob_sha1(ROOT / REENTRY_PATH) != REENTRY_BLOB_SHA:
        raise PermissionError("worktree re-entry blob changed")


_validate_reentry_source_before_import()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import scripts.zs_ki_b_sem_qualification_reentry_manifest_v0_1 as reentry


def _security_bindings() -> list[dict[str, str]]:
    bindings: list[dict[str, str]] = []
    for role, path in SECURITY_SOURCE_PATHS:
        oid = _blob_at(BASE_MAIN_COMMIT, path)
        if not oid or len(oid) != 40:
            raise PermissionError(f"invalid Git blob for {role}")
        bindings.append({"role": role, "path": path, "git_blob_sha": oid})
    return bindings


def build_prerun_package() -> dict[str, Any]:
    _validate_reentry_source_before_import()
    reentry_manifest = reentry.build_reentry_manifest()
    if reentry_manifest["status"] != "PREPARED_NOT_AUTHORIZED":
        raise PermissionError("re-entry manifest is not in non-authorized state")
    if reentry_manifest["runtime_model_id"] != EXPECTED_RUNTIME_MODEL_ID:
        raise PermissionError("runtime model ID changed")
    if reentry_manifest["model_repository"] != EXPECTED_MODEL_REPOSITORY:
        raise PermissionError("model repository changed")
    if reentry_manifest["qualification_case_count"] != 16:
        raise PermissionError("qualification case count changed")
    if reentry_manifest["max_tokens"] != 2048 or reentry_manifest["retry_count"] != 0:
        raise PermissionError("request bounds changed")
    if reentry_manifest["output_repair"] is not False:
        raise PermissionError("output repair must remain false")

    package = {
        "prerun_package_version": PACKAGE_VERSION,
        "status": "PREPARED_NOT_AUTHORIZED",
        "run_type": RUN_TYPE,
        "bound_main_commit": BASE_MAIN_COMMIT,
        "data_class": "SYNTHETIC_ONLY",
        "runtime_model_id": EXPECTED_RUNTIME_MODEL_ID,
        "model_repository": EXPECTED_MODEL_REPOSITORY,
        "expected_model_request_count": 16,
        "required_base_url": reentry_manifest["required_base_url"],
        "request_timeout_seconds": reentry_manifest["timeout_seconds"],
        "max_tokens": 2048,
        "retry_count": 0,
        "output_repair": False,
        "automatic_retry_authorized": False,
        "automatic_rerun_authorized": False,
        "qualification_snapshot_sha256": reentry_manifest["qualification_snapshot_sha256"],
        "ordered_case_ids_sha256": reentry_manifest["ordered_case_ids_sha256"],
        "ordered_case_ids": reentry_manifest["ordered_case_ids"],
        "reentry_manifest": {
            "path": REENTRY_PATH,
            "git_blob_sha": REENTRY_BLOB_SHA,
            "manifest_version": reentry_manifest["manifest_version"],
            "manifest_sha256": reentry_manifest["manifest_sha256"],
        },
        "human_gold": reentry_manifest["human_gold"],
        "qualification_policy": reentry_manifest["qualification_policy"],
        "canonical_artifacts": reentry_manifest["canonical_artifacts"],
        "security_source_bindings": _security_bindings(),
        "residual_architecture_issue": RESIDUAL_ARCHITECTURE_ISSUE,
        "authorization_gate": {
            "state": "CLOSED",
            "explicit_user_single_run_approval_required": True,
            "separate_authorization_artifact_required": True,
            "authorization_must_be_consumed_before_first_possible_model_contact": True,
            "no_execution_from_prerun_package": True,
        },
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
        "benchmark_approved": False,
        "generalisation_approved": False,
        "real_data": False,
        "pilot_approved": False,
        "production_approved": False,
        "phase_f_approved": False,
    }
    package["prerun_package_sha256"] = _stable_sha256(package)
    return package


def validate_prerun_package(package: dict[str, Any]) -> dict[str, Any]:
    expected = build_prerun_package()
    if package != expected:
        raise PermissionError("pre-run package mismatch")
    return package


def build_report() -> dict[str, Any]:
    package = build_prerun_package()
    return {
        "mode": "MODEL_FREE_MINISTRAL_QUALIFICATION_PRERUN_PREP",
        "status": "PASS",
        "prerun_package_sha256": package["prerun_package_sha256"],
        "runtime_model_id": package["runtime_model_id"],
        "qualification_case_count": len(package["ordered_case_ids"]),
        "security_binding_count": len(package["security_source_bindings"]),
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
