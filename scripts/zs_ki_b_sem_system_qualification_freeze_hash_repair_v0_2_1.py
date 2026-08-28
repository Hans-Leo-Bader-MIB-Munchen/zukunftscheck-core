#!/usr/bin/env python3
"""Generate a technical repair candidate for the v0.2 system-qualification freeze.

This script does not grant execution or model authority and does not overwrite the
historical HUMAN_APPROVED_FROZEN v0.2 manifest. It derives a v0.2.1 repair
candidate from that manifest, replaces policy/suite bindings with the actually
approved frozen artifacts, and materializes SHA-256 values from the current
checked-out bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_frozen_v0_2.json"
OUTPUT = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_repair_candidate_v0_2_1.json"

FROZEN_PATHS = {
    "policy": "tests/fixtures/zs_ki_b_sem_system_qualification_policy_frozen_v0_2.json",
    "suite": "tests/fixtures/zs_ki_b_sem_system_qualification_suite_frozen_v0_2.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_repair_candidate() -> dict[str, Any]:
    source = load(SOURCE)
    candidate = dict(source)
    candidate["freeze_version"] = "ZS-KI-B-SEM-SYSTEMQUALIFIKATION-FREEZE-2026-002_v0.2.1-REPAIR-CANDIDATE"
    candidate["status"] = "TECHNICAL_REPAIR_CANDIDATE"
    candidate["source_frozen_manifest"] = SOURCE.relative_to(ROOT).as_posix()
    candidate["source_frozen_manifest_sha256"] = sha256_file(SOURCE)
    candidate["repair_reason"] = (
        "Correct broken SHA-256 materialization and bind policy/suite to the actual "
        "HUMAN_APPROVED_FROZEN artifacts. No semantic scope, authority or execution state changes."
    )
    candidate["hash_materialization_basis"] = (
        "Computed from checked-out repository bytes by "
        "scripts/zs_ki_b_sem_system_qualification_freeze_hash_repair_v0_2_1.py."
    )
    candidate["hashes_materialized"] = True
    candidate["technical_repair_only"] = True
    candidate["human_reapproval_required_before_frozen_status"] = True

    repaired = []
    for artifact in source["artifacts"]:
        row = dict(artifact)
        if row["role"] in FROZEN_PATHS:
            row["path"] = FROZEN_PATHS[row["role"]]
        path = ROOT / row["path"]
        if not path.is_file():
            raise FileNotFoundError(row["path"])
        row["sha256"] = sha256_file(path)
        repaired.append(row)
    candidate["artifacts"] = repaired

    candidate["approval_records"] = {
        "policy_frozen": FROZEN_PATHS["policy"],
        "suite_frozen": FROZEN_PATHS["suite"],
    }
    candidate["execution_authorized"] = False
    candidate["model_contact_authorized"] = False
    candidate["model_qualification_status_preserved"] = "NOT_QUALIFIED"
    candidate["decision_authority"] = "NONE"
    candidate["note"] = (
        "Technical repair candidate only. It is not HUMAN_APPROVED_FROZEN until separately approved. "
        "No execution, model contact, benchmark/generalisation, pilot, production or Phase F authority is granted."
    )
    return candidate


def main() -> int:
    candidate = build_repair_candidate()
    OUTPUT.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT.relative_to(ROOT).as_posix())
    for artifact in candidate["artifacts"]:
        print(f"{artifact['role']} {artifact['sha256']} {artifact['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
