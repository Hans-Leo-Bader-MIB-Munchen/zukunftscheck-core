from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.validation.semantic_system_qualification_execution_harness_v0_1 import (
    execute_frozen_system_qualification_once,
)

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_suite_frozen_v0_2.json"
GOLD_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
PROFILE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_generic_system_composition_profiles_v0_1.json"
EXPECTED_COMMIT = "e68dbf656dc47138dfda9f4f6297c28a44edda97"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute exactly one second model-free frozen 29-case system qualification pass.")
    parser.add_argument("--authorize-execution", action="store_true", help="Required explicit execution gate.")
    parser.add_argument("--evaluated-commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not args.authorize_execution:
        parser.error("--authorize-execution is required")
    if args.evaluated_commit != EXPECTED_COMMIT:
        parser.error(f"evaluated commit must be exactly {EXPECTED_COMMIT}")

    report = execute_frozen_system_qualification_once(
        suite=load(SUITE_PATH),
        gold=load(GOLD_PATH),
        profile_set=load(PROFILE_PATH),
        evaluated_commit=args.evaluated_commit,
        execution_authorized=True,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["qualification_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
