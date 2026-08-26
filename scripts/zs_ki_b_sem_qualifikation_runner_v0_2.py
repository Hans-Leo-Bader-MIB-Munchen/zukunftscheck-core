#!/usr/bin/env python3
"""One-shot local SEM qualification runner v0.2 for R16/R18/R21/R22.

Uses the proven v0.1 execution/boundary path unchanged, but freezes execution to
SEM prompt v0.2 and a distinct second qualification run identifier.
"""
from __future__ import annotations

import scripts.zs_ki_b_sem_qualifikation_runner_v0_1 as base

PROMPT_VERSION = "zs_ki_b_sem_qualifikation_system_v0_2"
PROMPT_SHA256 = "9280e064c2504677f1e7e9e408990532046aaed087caf41a241a718a89d85b40"
PROMPT_PATH = base.ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_2.txt"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-ONE-RUN-2026-002"
RUNNER_VERSION = "v0.2"
DEFAULT_OUTPUT = "zs_ki_b_sem_qualifikation_result_v0_2.json"


def configure_base() -> None:
    base.PROMPT_VERSION = PROMPT_VERSION
    base.PROMPT_SHA256 = PROMPT_SHA256
    base.PROMPT_PATH = PROMPT_PATH
    base.RUN_TYPE = RUN_TYPE
    base.RUNNER_VERSION = RUNNER_VERSION
    base.DEFAULT_OUTPUT = DEFAULT_OUTPUT


def main() -> int:
    configure_base()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
