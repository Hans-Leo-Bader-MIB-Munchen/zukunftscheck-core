#!/usr/bin/env python3
"""Additive model-free SEM runtime-binding runner v0.7.

Binds prompt v0.5, semantic contract v0.2, and reference_question_meanings_v0_7.json
with complete human-reviewed model-free coverage of all 67 frozen reference questions.
This block deliberately does not enable model execution. It establishes and verifies
the runtime/qualification binding only. Meaning coverage is not model qualification,
benchmark approval, generalisation approval, real-data approval, pilot approval,
production approval, or Phase-F approval.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_5 as base
from llm.smoketest import canonical_json, sha256_text

_BASE_BUILD_DRY_RUN_MANIFEST = base.build_dry_run_manifest

PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_5"
CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"
BINDING_VERSION = "ZS-DEV-KI-B-SEM-RUNTIME-BINDING-V0-7-2026-001_v0.1"
RUN_TYPE = "ZS-KI-B-SEM-RUNTIME-BINDING-MEANING-LAYER-V0-7-2026-007"
RUNNER_VERSION = "v0.7"
EXPECTED_RUN_COUNT = 0
EXPECTED_MODEL_REQUEST_COUNT = 0
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_5.txt"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_question_meanings_v0_7.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
CONTRACT_SCHEMA_PATH = ROOT / "domains" / "zukunftscheck" / "schema" / "b_semantic_contract_v0_2.schema.json"
RUNNER_PATH = Path(__file__).resolve()
CASE_PATHS = base.CASE_PATHS
MEANING_LAYER_LABEL = "reference_question_meanings_v0_7.json/67-of-67-human-reviewed-model-free-coverage"
EXPECTED_REFERENCE_QUESTION_COUNT = 67


def _bind_base() -> None:
    base.PROMPT_VERSION = PROMPT_VERSION
    base.CONTRACT_VERSION = CONTRACT_VERSION
    base.RUN_TYPE = RUN_TYPE
    base.RUNNER_VERSION = RUNNER_VERSION
    base.EXPECTED_RUN_COUNT = EXPECTED_RUN_COUNT
    base.EXPECTED_MODEL_REQUEST_COUNT = EXPECTED_MODEL_REQUEST_COUNT
    base.PROMPT_PATH = PROMPT_PATH
    base.QUESTIONS_PATH = QUESTIONS_PATH
    base.MEANINGS_PATH = MEANINGS_PATH
    base.FINDING_TYPES_PATH = FINDING_TYPES_PATH
    base.CASE_PATHS = CASE_PATHS


def load(path: Path) -> dict[str, Any]:
    return base.load(path)


def current_git_commit() -> str:
    return base.current_git_commit()


def validate_runtime_binding() -> dict[str, Any]:
    """Fail closed if the declared v0.7 runtime bundle is internally inconsistent."""
    questions_doc = load(QUESTIONS_PATH)
    meanings_doc = load(MEANINGS_PATH)
    contract_doc = load(CONTRACT_SCHEMA_PATH)
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

    questions = questions_doc.get("questions")
    meanings = meanings_doc.get("meanings")
    if not isinstance(questions, list) or len(questions) != EXPECTED_REFERENCE_QUESTION_COUNT:
        raise ValueError("reference snapshot must contain exactly 67 questions")
    if meanings_doc.get("schema_version") != "v0.7":
        raise ValueError("meaning layer schema_version must be v0.7")
    if not isinstance(meanings, list) or len(meanings) != EXPECTED_REFERENCE_QUESTION_COUNT:
        raise ValueError("Meaning Layer v0.7 must contain exactly 67 entries")

    canonical_pf = {row.get("question_id"): row.get("pf_id") for row in questions if isinstance(row, dict)}
    meaning_pf = {row.get("question_id"): row.get("pf_id") for row in meanings if isinstance(row, dict)}
    if len(canonical_pf) != EXPECTED_REFERENCE_QUESTION_COUNT or len(meaning_pf) != EXPECTED_REFERENCE_QUESTION_COUNT:
        raise ValueError("reference and meaning question_ids must each be unique and complete")
    if meaning_pf != canonical_pf:
        raise ValueError("Meaning Layer v0.7 question_id/PF binding must exactly match the frozen 67er snapshot")

    if contract_doc.get("$id") != CONTRACT_VERSION:
        raise ValueError("semantic contract schema id does not match CONTRACT_VERSION")
    if "reference_question_meanings_v0_7.json" not in prompt_text:
        raise ValueError("prompt does not explicitly bind Meaning Layer v0.7")
    if CONTRACT_VERSION not in prompt_text:
        raise ValueError("prompt does not explicitly bind semantic contract v0.2")

    return {
        "binding_version": BINDING_VERSION,
        "reference_question_count": len(canonical_pf),
        "meaning_question_count": len(meaning_pf),
        "coverage": "67/67",
    }


def build_messages(case: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
    """Build the prospective qualification payload without contacting any model."""
    validate_runtime_binding()
    _bind_base()
    return base.build_messages(case, prompt_text)


def evaluate_boundary(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    return base.evaluate_boundary(case, response)


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    binding = validate_runtime_binding()
    _bind_base()
    result = _BASE_BUILD_DRY_RUN_MANIFEST(model=model, base_url=base_url)
    result["mode"] = "DRY_RUN_SEM_RUNTIME_BINDING_V0_7"
    manifest = result["manifest"]
    manifest.update({
        "binding_version": BINDING_VERSION,
        "runner_sha256": sha256_text(RUNNER_PATH.read_text(encoding="utf-8")),
        "contract_schema": "b_semantic_contract_v0_2.schema.json",
        "contract_schema_sha256": sha256_text(canonical_json(load(CONTRACT_SCHEMA_PATH))),
        "meaning_layer": MEANING_LAYER_LABEL,
        "meaning_layer_schema_version": "v0.7",
        "meaning_layer_sha256": sha256_text(canonical_json(load(MEANINGS_PATH))),
        "meaning_layer_reference_question_count": binding["reference_question_count"],
        "meaning_layer_entry_count": binding["meaning_question_count"],
        "meaning_layer_coverage": binding["coverage"],
        "meaning_layer_full_reference_coverage": True,
        "meaning_layer_model_qualified": False,
        "model_execution_enabled": False,
        "benchmark_approved": False,
        "generalisation_approved": False,
        "real_data_approved": False,
        "pilot_approved": False,
        "production_approved": False,
        "phase_f_approved": False,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    args = parser.parse_args()

    validate_runtime_binding()
    if args.execute:
        parser.error(
            "model execution is disabled in ZS-DEV-KI-B-SEM-RUNTIME-BINDING-V0-7-2026-001; "
            "a separately versioned and explicitly approved qualification step is required"
        )
    print(json.dumps(build_dry_run_manifest(model=args.model, base_url=args.base_url), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
