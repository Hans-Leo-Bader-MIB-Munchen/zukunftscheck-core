import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_manifest_candidate_v0_1.json"

RUNNER_VERSION = "v0.1-prep-only"
MODE = "DEVELOPMENT_PREP_ONLY"


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError(f"bare CR rejected for bound artifact: {path}")
    return data


def git_blob_sha1(path: Path) -> str:
    data = canonical_bytes(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_manifest_fail_closed(manifest: dict) -> None:
    required_false_flags = [
        "qualification_claim_allowed",
        "execution_authorized",
        "model_contact_authorized",
        "preflight_authorized",
        "automatic_retry_authorized",
        "automatic_rerun_authorized",
        "output_repair_authorized",
    ]
    if manifest.get("mode") != MODE:
        raise RuntimeError("manifest mode mismatch")
    if manifest.get("data_class") != "SYNTHETIC_ONLY":
        raise RuntimeError("manifest data_class mismatch")
    for flag in required_false_flags:
        if manifest.get(flag) is not False:
            raise RuntimeError(f"fail-closed authorization violation: {flag}")
    if manifest.get("hard_stop") != "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION":
        raise RuntimeError("hard_stop mismatch")
    if manifest.get("expected_case_count") != 24:
        raise RuntimeError("expected_case_count mismatch")
    if manifest.get("expected_model_request_count") != 24:
        raise RuntimeError("expected_model_request_count mismatch")
    ordered = manifest.get("ordered_case_ids")
    if not isinstance(ordered, list) or len(ordered) != 24 or len(set(ordered)) != 24:
        raise RuntimeError("ordered_case_ids invalid")


def validate_bound_blobs(manifest: dict) -> None:
    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise RuntimeError("bindings missing")
    for name, binding in bindings.items():
        path_value = binding.get("path")
        expected_blob = binding.get("git_blob_sha")
        if not isinstance(path_value, str) or not isinstance(expected_blob, str):
            raise RuntimeError(f"invalid binding record: {name}")
        path = ROOT / path_value
        if not path.is_file():
            raise RuntimeError(f"missing bound artifact: {name}")
        actual_blob = git_blob_sha1(path)
        if actual_blob != expected_blob:
            raise RuntimeError(f"blob mismatch: {name}")


def build_prep_report(manifest: dict) -> dict:
    return {
        "runner_version": RUNNER_VERSION,
        "mode": MODE,
        "status": "PREP_VALIDATED_NO_EXECUTION",
        "case_count": manifest["expected_case_count"],
        "model_request_count": 0,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "preflight_authorized": False,
        "qualification_claim_allowed": False,
        "hard_stop": manifest["hard_stop"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI-assisted development prep artifacts only; no model execution is implemented.")
    parser.add_argument("--validate-prep", action="store_true", help="Validate manifest and bound blobs without model contact.")
    args = parser.parse_args()
    if not args.validate_prep:
        raise SystemExit("fail-closed: only --validate-prep is supported; no execution path exists")

    manifest = load_manifest()
    validate_manifest_fail_closed(manifest)
    validate_bound_blobs(manifest)
    print(json.dumps(build_prep_report(manifest), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
