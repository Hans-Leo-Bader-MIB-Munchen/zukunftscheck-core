#!/usr/bin/env python3
"""Additive SEM qualification runner v0.6 for meaning-layer v0.2 regression/control.

Reuses the validated v0.5 execution and boundary mechanics while explicitly binding
prompt v0.4 and reference_question_meanings_v0_2.json. The known R16/R18/R21/R22
cases remain regression/control cases only; this runner does not turn them into an
independent generalisation benchmark. Dry run makes no model contact.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_5 as base

_BASE_BUILD_DRY_RUN_MANIFEST = base.build_dry_run_manifest

PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_4"
CONTRACT_VERSION = "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-MEANING-LAYER-V0-2-REGRESSION-2026-006"
RUNNER_VERSION = "v0.6"
EXPECTED_RUN_COUNT = 1
EXPECTED_MODEL_REQUEST_COUNT = 4
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_6.json"
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_4.txt"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"
MEANINGS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_question_meanings_v0_2.json"
FINDING_TYPES_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "finding_type_meanings_v0_1.json"
CASE_PATHS = base.CASE_PATHS
MEANING_LAYER_LABEL = "reference_question_meanings_v0_2.json/R16-R18-R21-R22-neighbor-limited"


def _bind_base() -> None:
    base.PROMPT_VERSION = PROMPT_VERSION
    base.CONTRACT_VERSION = CONTRACT_VERSION
    base.RUN_TYPE = RUN_TYPE
    base.RUNNER_VERSION = RUNNER_VERSION
    base.EXPECTED_RUN_COUNT = EXPECTED_RUN_COUNT
    base.EXPECTED_MODEL_REQUEST_COUNT = EXPECTED_MODEL_REQUEST_COUNT
    base.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    base.PROMPT_PATH = PROMPT_PATH
    base.QUESTIONS_PATH = QUESTIONS_PATH
    base.MEANINGS_PATH = MEANINGS_PATH
    base.FINDING_TYPES_PATH = FINDING_TYPES_PATH
    base.CASE_PATHS = CASE_PATHS
    # v0.5 main() calls its own module-level builder. Rebind that call site to
    # the v0.6 wrapper so standalone dry-runs/executions report the v0.2 label.
    base.build_dry_run_manifest = build_dry_run_manifest


def load(path: Path) -> dict[str, Any]:
    return base.load(path)


def current_git_commit() -> str:
    return base.current_git_commit()


def build_messages(case: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
    _bind_base()
    return base.build_messages(case, prompt_text)


def evaluate_boundary(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    return base.evaluate_boundary(case, response)


def build_dry_run_manifest(*, model: str = "", base_url: str = "http://127.0.0.1:1234/v1") -> dict[str, Any]:
    _bind_base()
    result = _BASE_BUILD_DRY_RUN_MANIFEST(model=model, base_url=base_url)
    result["manifest"]["meaning_layer"] = MEANING_LAYER_LABEL
    return result


def main() -> int:
    _bind_base()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
