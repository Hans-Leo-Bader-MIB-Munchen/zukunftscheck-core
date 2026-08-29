#!/usr/bin/env python3
"""Model-free authorization integration prep for the future executable runner."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v2_0_assembly_prep as v20
import scripts.zs_ki_b_sem_qualifikation_runner_v1_9_readiness_prep as v19
import scripts.zs_ki_b_sem_qualifikation_runner_v1_8_prep as v18
import scripts.zs_ki_b_sem_canonical_binding_integrity_v0_1 as integrity

RUNNER_VERSION = "v2.1-authorization-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-1-AUTHORIZATION-INTEGRATION-PREP-2026-022"
EXPECTED_MODEL_REQUEST_COUNT = 16


def _canonical_binding_payload() -> dict[str, Any]:
    snapshot = integrity.build_binding_snapshot()
    return {
        "source_base_commit": snapshot["source_base_commit"],
        "hash_semantics": snapshot["hash_semantics"],
        "bound_artifacts": snapshot["artifacts"],
        "bound_runner_preparations": snapshot["runner_bindings"],
        "ordered_case_ids": snapshot["ordered_case_ids"],
        "ordered_case_ids_sha256": snapshot["ordered_case_ids_sha256"],
        "qualification_snapshot_sha256": snapshot["qualification_snapshot_sha256"],
    }


def build_authorization_template() -> dict[str, Any]:
    binding = _canonical_binding_payload()
    return {
        "status": "NOT_AUTHORIZED_TEMPLATE",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "model_repository": v19.EXPECTED_MODEL_REPOSITORY,
        "runtime_model_id": v19.EXPECTED_MODEL_ID,
        "model": v19.EXPECTED_MODEL_ID,
        "prompt_version": v19.EXPECTED_PROMPT,
        "prompt_sha256": v19.EXPECTED_PROMPT_SHA256,
        "contract_version": v19.EXPECTED_CONTRACT,
        "output_mode_version": v19.EXPECTED_OUTPUT_MODE,
        "response_format_sha256": v19.EXPECTED_RESPONSE_FORMAT_SHA256,
        "expected_model_request_count": EXPECTED_MODEL_REQUEST_COUNT,
        **binding,
        "required_base_url": v19.EXPECTED_BASE_URL,
        "required_request_timeout_seconds": v19.EXPECTED_TIMEOUT_SECONDS,
        "max_tokens": v19.EXPECTED_MAX_TOKENS,
        "stream": False,
        "synthetic_only": True,
        "local_loopback_only": True,
        "single_run_only": True,
        "retry_count": 0,
        "output_repair": False,
        "remote_cloud": False,
        "real_data": False,
        "authorization_consumed": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
    }


def _authorization_matches(auth: dict[str, Any]) -> bool:
    expected = build_authorization_template()
    return (
        auth.get("status") == "EXPLICIT_USER_APPROVED"
        and auth.get("runner_version") == expected["runner_version"]
        and auth.get("run_type") == expected["run_type"]
        and auth.get("model_repository") == expected["model_repository"]
        and auth.get("runtime_model_id") == expected["runtime_model_id"]
        and auth.get("model") == expected["model"]
        and auth.get("prompt_version") == expected["prompt_version"]
        and auth.get("prompt_sha256") == expected["prompt_sha256"]
        and auth.get("contract_version") == expected["contract_version"]
        and auth.get("output_mode_version") == expected["output_mode_version"]
        and auth.get("response_format_sha256") == expected["response_format_sha256"]
        and auth.get("expected_model_request_count") == EXPECTED_MODEL_REQUEST_COUNT
        and auth.get("source_base_commit") == expected["source_base_commit"]
        and auth.get("hash_semantics") == expected["hash_semantics"]
        and auth.get("bound_artifacts") == expected["bound_artifacts"]
        and auth.get("bound_runner_preparations") == expected["bound_runner_preparations"]
        and auth.get("ordered_case_ids") == expected["ordered_case_ids"]
        and auth.get("ordered_case_ids_sha256") == expected["ordered_case_ids_sha256"]
        and auth.get("qualification_snapshot_sha256") == expected["qualification_snapshot_sha256"]
        and auth.get("required_base_url") == expected["required_base_url"]
        and auth.get("required_request_timeout_seconds") == expected["required_request_timeout_seconds"]
        and auth.get("max_tokens") == expected["max_tokens"]
        and auth.get("stream") is False
        and auth.get("synthetic_only") is True
        and auth.get("local_loopback_only") is True
        and auth.get("single_run_only") is True
        and auth.get("retry_count") == 0
        and auth.get("output_repair") is False
        and auth.get("remote_cloud") is False
        and auth.get("real_data") is False
        and auth.get("authorization_consumed") is False
        and auth.get("execution_authorized") is True
        and auth.get("model_run_authorized") is True
        and auth.get("model_contact_authorized") is True
    )


def validate_execution_authorization(auth: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(auth, dict) or not _authorization_matches(auth):
        raise PermissionError(
            "v2.1 authorization prep has no valid explicit single-use model-contact authorization"
        )
    return auth


def _current_binding_is_exact() -> bool:
    assembly = v20.build_assembly_report()
    integrity_checks = integrity.validate_current_worktree_binding()
    return (
        assembly.get("status") == "PASS"
        and assembly.get("assembly_ready") is True
        and assembly.get("ready_to_execute") is False
        and all(assembly.get("checks", {}).values())
        and bool(integrity_checks)
        and all(integrity_checks.values())
    )


def _frozen_case_ids() -> list[str]:
    suite = v18.v17.load(v18.v17.SUITE_PATH)
    case_ids = [case.get("case_id") for case in suite.get("cases", [])]
    if tuple(case_ids) != integrity.EXPECTED_ORDERED_CASE_IDS:
        raise PermissionError("frozen qualification suite is not the exact ordered authorized 16-case suite")
    return case_ids


def execute_once(*, transport, authorization: dict[str, Any] | None = None):
    """Model-free integration boundary using only an explicitly injected transport.

    The authorization is consumed in-memory before the first transport call. A future
    live executable runner must additionally persist that consumed state atomically
    before model contact; V21 creates no authorization artifact and performs no I/O.
    """
    auth = validate_execution_authorization(authorization)
    if not _current_binding_is_exact():
        raise PermissionError("current prompt/schema/content binding no longer matches the authorized V21 design")
    case_ids = _frozen_case_ids()

    auth["authorization_consumed"] = True

    results = []
    for case_id in case_ids:
        request = v18.build_candidate_request_preview(case_id=case_id)
        results.append(
            transport(
                base_url=v20.BASE_URL,
                payload=request,
                timeout_seconds=v20.TIMEOUT_SECONDS,
                case_id=case_id,
            )
        )
    return results


def build_authorization_report() -> dict[str, Any]:
    assembly = v20.build_assembly_report()
    template = build_authorization_template()
    case_ids = _frozen_case_ids()
    integrity_checks = integrity.validate_current_worktree_binding()
    bound_roles = {row["role"] for row in template["bound_artifacts"]}
    checks = {
        "v20_assembly_pass": assembly.get("status") == "PASS",
        "v20_not_ready_to_execute": assembly.get("ready_to_execute") is False,
        "runtime_model_id_exact": template["runtime_model_id"] == v19.EXPECTED_MODEL_ID,
        "prompt_hash_exact": template["prompt_sha256"] == v19.EXPECTED_PROMPT_SHA256,
        "response_format_hash_exact": template["response_format_sha256"] == v19.EXPECTED_RESPONSE_FORMAT_SHA256,
        "expected_request_count_16": template["expected_model_request_count"] == 16,
        "frozen_suite_count_16": len(case_ids) == 16,
        "frozen_suite_order_exact": tuple(case_ids) == integrity.EXPECTED_ORDERED_CASE_IDS,
        "canonical_content_binding_exact": bool(integrity_checks) and all(integrity_checks.values()),
        "suite_content_hash_bound": "qualification_suite" in bound_roles,
        "reference_questions_content_hash_bound": "reference_questions" in bound_roles,
        "meaning_layer_content_hash_bound": "reference_question_meanings" in bound_roles,
        "finding_type_meanings_content_hash_bound": "finding_type_meanings" in bound_roles,
        "system_prompt_content_hash_bound": "system_prompt" in bound_roles,
        "response_schema_content_hash_bound": "response_schema" in bound_roles,
        "source_commit_bound": template["source_base_commit"] == integrity.SOURCE_BASE_COMMIT,
        "ordered_case_ids_hash_bound": len(template["ordered_case_ids_sha256"]) == 64,
        "qualification_snapshot_hash_bound": len(template["qualification_snapshot_sha256"]) == 64,
        "loopback_only": template["local_loopback_only"] is True,
        "synthetic_only": template["synthetic_only"] is True,
        "single_run_only": template["single_run_only"] is True,
        "max_tokens_exact": template["max_tokens"] == 1024,
        "stream_false": template["stream"] is False,
        "timeout_exact": template["required_request_timeout_seconds"] == 1800.0,
        "retry_zero": template["retry_count"] == 0,
        "output_repair_false": template["output_repair"] is False,
        "template_not_authorized": template["status"] == "NOT_AUTHORIZED_TEMPLATE",
        "execution_not_authorized": template["execution_authorized"] is False,
        "model_contact_not_authorized": template["model_contact_authorized"] is False,
        "authorization_not_consumed": template["authorization_consumed"] is False,
        "execution_path_revalidates_current_binding": _current_binding_is_exact(),
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_AUTHORIZATION_RUNNER_INTEGRATION_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "checks": checks,
        "authorization_binding_ready": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "authorization_artifact_created": False,
        "future_live_runner_must_persist_consumption_before_model_contact": True,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def main() -> int:
    report = build_authorization_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
