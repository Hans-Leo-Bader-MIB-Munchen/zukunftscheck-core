from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_system_qualification_freeze_manifest_candidate_v0_2.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "FREEZE_CANDIDATE":
        raise ValueError("freeze preparation requires FREEZE_CANDIDATE manifest")
    if data.get("hash_algorithm") != "SHA-256":
        raise ValueError("freeze preparation requires SHA-256")
    if data.get("execution_authorized") is not False:
        raise ValueError("freeze candidate may not authorize execution")
    if data.get("model_contact_authorized") is not False:
        raise ValueError("freeze candidate may not authorize model contact")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("freeze candidate requires non-empty artifacts list")
    return data


def materialize_hashes(manifest: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    result = deepcopy(manifest)
    seen_paths: set[str] = set()
    for artifact in result["artifacts"]:
        if not isinstance(artifact, dict):
            raise ValueError("artifact entry must be an object")
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError("artifact path must be a non-empty string")
        if path_value in seen_paths:
            raise ValueError(f"duplicate artifact path: {path_value}")
        seen_paths.add(path_value)
        artifact_path = root / path_value
        if not artifact_path.is_file():
            raise FileNotFoundError(path_value)
        artifact["sha256"] = sha256_file(artifact_path)

    result["hashes_materialized"] = True
    result["status"] = "HASH_BOUND_FREEZE_CANDIDATE"
    result["execution_authorized"] = False
    result["model_contact_authorized"] = False
    result["decision_authority"] = "NONE"
    result["final_freeze_requires_explicit_human_approval"] = True
    result["next_gate"] = (
        "Run model-free freeze tests and obtain explicit human approval before creating "
        "HUMAN_APPROVED_FROZEN copies."
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize SHA-256 hashes for the v0.2 system-qualification freeze candidate.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--write", type=Path, default=None, help="Optional output path. Without this flag, JSON is printed only.")
    args = parser.parse_args()

    candidate = load_manifest(args.manifest)
    materialized = materialize_hashes(candidate)
    payload = json.dumps(materialized, indent=2, ensure_ascii=False) + "\n"

    if args.write is None:
        print(payload, end="")
    else:
        args.write.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
