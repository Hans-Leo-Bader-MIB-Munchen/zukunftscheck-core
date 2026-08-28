#!/usr/bin/env python3
"""Runner v1.3.1: provenance-only correction layer over v1.3.

This layer does not change the frozen suite, Human Gold, semantic boundary,
generic composition profiles, prompt, model scope, retry policy or repair policy.
It corrects two provenance defects observed in the consumed v1.3 one-shot run:
1. inherited execution mode labels still ended in V0_9;
2. model_contact_performed remained false after generation requests occurred.

The historical v1.3 runner and its preserved execution result remain untouched.
No model execution is authorized by this module.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v1_3 as v13

RUNNER_VERSION = "v1.3.1"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-3-1-PROVENANCE-CORRECTED-2026-014"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v1_3_1.json"

_MODE_MAP = {
    "PRECONDITION_FAILED_SEM_QUALIFICATION_V0_9": "PRECONDITION_FAILED_SEM_QUALIFICATION_V1_3_1",
    "EXECUTING_SEM_QUALIFICATION_V0_9": "EXECUTING_SEM_QUALIFICATION_V1_3_1",
    "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_SEM_QUALIFICATION_V1_3_1",
    "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_FAILED_GOLD_SEM_QUALIFICATION_V1_3_1",
    "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V0_9": "EXECUTED_ONCE_PASSED_FROZEN_SEM_QUALIFICATION_V1_3_1",
}

_ORIGINAL_PERSIST = v13.v11.v10.v09._persist


def normalize_execution_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize only runner provenance metadata; never alter case/model content."""
    mode = payload.get("mode")
    if isinstance(mode, str) and mode in _MODE_MAP:
        payload["mode"] = _MODE_MAP[mode]

    manifest = payload.get("manifest")
    if isinstance(manifest, dict):
        manifest["run_type"] = RUN_TYPE
        manifest["runner_version"] = RUNNER_VERSION
        observed = manifest.get("observed_model_request_count")
        manifest["model_contact_performed"] = isinstance(observed, int) and observed > 0

    return payload


def _persist(payload: dict[str, Any], output: str) -> None:
    normalize_execution_provenance(payload)
    _ORIGINAL_PERSIST(payload, output)


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    payload = v13.build_dry_run_manifest(model=model, base_url=base_url)
    payload["mode"] = "DRY_RUN_SEM_QUALIFICATION_V1_3_1"
    manifest = payload["manifest"]
    manifest["run_type"] = RUN_TYPE
    manifest["runner_version"] = RUNNER_VERSION
    manifest["model_contact_performed"] = False
    manifest["provenance_correction_only"] = True
    return payload


def validate_execution_authorization(model: str) -> dict[str, Any]:
    """Fail closed: v1.3 authorization cannot silently authorize v1.3.1."""
    auth = v13.load(v13.AUTH_PATH)
    if auth.get("status") != "EXPLICIT_USER_APPROVED":
        raise PermissionError("v1.3.1 model run is not explicitly authorized")
    if auth.get("runner_version") != RUNNER_VERSION or auth.get("run_type") != RUN_TYPE:
        raise PermissionError("v1.3.1 requires a separately matching authorization artifact")
    return v13.validate_execution_authorization(model)


def _install_bindings() -> None:
    v13._configure()
    v13.v11.v10.v09._persist = _persist
    v13.v11.v10.v09.RUN_TYPE = RUN_TYPE
    v13.v11.v10.v09.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.v10.v09.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.v10.v09.base.RUN_TYPE = RUN_TYPE
    v13.v11.v10.v09.base.RUNNER_VERSION = RUNNER_VERSION
    v13.v11.v10.v09.base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    v13.v11.validate_execution_authorization = validate_execution_authorization
    v13.v11.build_dry_run_manifest = build_dry_run_manifest
    v13.v11.v10.validate_execution_authorization = validate_execution_authorization
    v13.v11.v10.build_dry_run_manifest = build_dry_run_manifest


def main() -> int:
    _install_bindings()
    return v13.v11.main()


if __name__ == "__main__":
    raise SystemExit(main())
