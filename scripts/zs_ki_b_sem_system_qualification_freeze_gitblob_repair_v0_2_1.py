from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_frozen_v0_2.json"
DEFAULT_OUTPUT = ROOT / "tests/fixtures/zs_ki_b_sem_system_qualification_freeze_manifest_gitblob_repair_candidate_v0_2_1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_bytes(commit: str, path: str, *, root: Path = ROOT) -> bytes:
    blob_sha = subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=root,
        text=True,
    ).strip()
    return subprocess.check_output(
        ["git", "cat-file", "blob", blob_sha],
        cwd=root,
    )


def canonical_sha256(commit: str, path: str, *, root: Path = ROOT) -> str:
    return hashlib.sha256(git_blob_bytes(commit, path, root=root)).hexdigest()


def build_repair_candidate(source: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    if source.get("status") != "HUMAN_APPROVED_FROZEN":
        raise ValueError("source manifest must be HUMAN_APPROVED_FROZEN")
    if source.get("hash_algorithm") != "SHA-256":
        raise ValueError("source manifest must use SHA-256")

    approved_commit = source.get("approved_main_commit")
    if not isinstance(approved_commit, str) or not approved_commit:
        raise ValueError("source manifest requires approved_main_commit")

    result = deepcopy(source)
    result["freeze_version"] = "ZS-KI-B-SEM-SYSTEMQUALIFIKATION-FREEZE-2026-002_v0.2.1-GITBLOB-REPAIR-CANDIDATE"
    result["status"] = "TECHNICAL_REPAIR_CANDIDATE"
    result["repair_of"] = source["freeze_version"]
    result["repair_reason"] = (
        "The v0.2 SHA-256 values were materialized from checked-out worktree bytes. "
        "On platforms with line-ending conversion this is not reproducible. This candidate "
        "re-materializes SHA-256 over the canonical Git blob bytes at the original approved_main_commit."
    )
    result["hash_basis"] = "CANONICAL_GIT_BLOB_BYTES"
    result["hash_basis_commit"] = approved_commit
    result["hash_materialization_command_semantics"] = "git rev-parse <commit>:<path> + git cat-file blob <blob_sha> + SHA-256"
    result["hashes_materialized"] = True
    result["execution_authorized"] = False
    result["model_contact_authorized"] = False
    result["decision_authority"] = "NONE"
    result["technical_repair_only"] = True
    result["semantic_scope_changed"] = False
    result["artifact_paths_changed"] = False
    result["human_reapproval_required_before_replacing_frozen_manifest"] = True
    result["guarded_system_qualification_status"] = source.get("guarded_system_qualification_status")
    result["model_qualification_status_preserved"] = source.get("model_qualification_status_preserved")

    for artifact in result["artifacts"]:
        path = artifact["path"]
        artifact["sha256"] = canonical_sha256(approved_commit, path, root=root)

    result["next_gate"] = (
        "Verify canonical Git-blob hashes model-free on at least the current Windows checkout and "
        "against repository blob bytes, then obtain explicit human approval before creating a "
        "replacement HUMAN_APPROVED_FROZEN manifest. No model contact is authorized."
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build platform-independent v0.2.1 Git-blob hash repair candidate.")
    parser.add_argument("--source", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--write", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = load(args.source)
    result = build_repair_candidate(source)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    args.write.write_text(payload, encoding="utf-8", newline="\n")
    print(args.write.relative_to(ROOT))
    for artifact in result["artifacts"]:
        print(artifact["role"], artifact["sha256"], artifact["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
