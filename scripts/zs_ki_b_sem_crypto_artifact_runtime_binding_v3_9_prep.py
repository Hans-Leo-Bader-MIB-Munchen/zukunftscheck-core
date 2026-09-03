#!/usr/bin/env python3
"""V39 model-free distribution-artifact and runtime binding preparation.

V39 binds the exact reviewed cryptography wheel for the local Windows/CPython
runtime and can verify local runtime compatibility plus wheel SHA-256. It does
not install or import cryptography, perform signature verification, establish
external authority/trust, authorize execution, or contact a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import struct
import sys
from pathlib import Path
from typing import Any

import scripts.zs_ki_b_sem_crypto_backend_dependency_binding_v3_8_prep as v38

PREP_VERSION = "v3.9-crypto-artifact-runtime-binding-prep"
PREP_TYPE = "ZS-KI-B-SEM-CRYPTO-ARTIFACT-RUNTIME-BINDING-PREP-2026-001"
BASE_MAIN_COMMIT = "03acd43461cb75aadf9d4594bec34ccd30982ee1"
BINDING_VERSION = "ZS-KI-B-SEM-CRYPTO-ARTIFACT-RUNTIME-BINDING-2026-001_v0.1"
SOURCE_V38_SCRIPT_BLOB_SHA = "5c6ccdeeb94e086dfea48361279461c0d5cad2f8"

BACKEND_PACKAGE = "cryptography"
BACKEND_VERSION = "50.0.1"
BACKEND_REQUIREMENT = "cryptography==50.0.1"
ARTIFACT_FILENAME = "cryptography-50.0.1-cp311-abi3-win_amd64.whl"
ARTIFACT_SHA256 = "aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648"
ARTIFACT_INTERPRETER_TAG = "cp311"
ARTIFACT_ABI_TAG = "abi3"
ARTIFACT_PLATFORM_TAG = "win_amd64"
ARTIFACT_SOURCE = "PYPI"
ARTIFACT_PUBLISHER = "pyca/cryptography"
ARTIFACT_SOURCE_COMMIT = "dc1125347f52b36b7070332910c680e68db0f478"
ARTIFACT_TRUSTED_PUBLISHING_REPORTED = True
ARTIFACT_ATTESTATION_VERIFIED = False

TARGET_PYTHON_IMPLEMENTATION = "CPython"
TARGET_PYTHON_MIN = (3, 11)
TARGET_SYS_PLATFORM = "win32"
TARGET_MACHINE_ACCEPTED = frozenset({"AMD64", "x86_64"})
TARGET_POINTER_BITS = 64


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PermissionError(f"V39 {label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise PermissionError(
            f"V39 {label} keyset mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )


def _git_text_blob_sha1(path: str | Path) -> str:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V39 cannot read loaded V38 source for blob verification") from exc
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise PermissionError("V39 loaded V38 source contains non-canonical bare CR bytes")
    header = f"blob {len(canonical)}\0".encode("ascii")
    return hashlib.sha1(header + canonical).hexdigest()


def _validate_loaded_v38_blob() -> str:
    loaded_path = getattr(v38, "__file__", None)
    if not isinstance(loaded_path, str) or not loaded_path:
        raise PermissionError("V39 loaded V38 module has no source path")
    observed = _git_text_blob_sha1(loaded_path)
    if observed != SOURCE_V38_SCRIPT_BLOB_SHA:
        raise PermissionError("V39 loaded V38 implementation blob mismatch")
    return observed


def build_artifact_runtime_binding_preview() -> dict[str, Any]:
    source_blob = _validate_loaded_v38_blob()
    source_binding = v38.build_backend_binding_preview()
    binding = {
        "binding_version": BINDING_VERSION,
        "prep_version": PREP_VERSION,
        "prep_type": PREP_TYPE,
        "prep_base_main_commit": BASE_MAIN_COMMIT,
        "source_v38_prep_version": v38.PREP_VERSION,
        "source_v38_binding_version": v38.BINDING_VERSION,
        "source_v38_script_blob_sha": source_blob,
        "source_v38_backend_binding_sha256": source_binding["backend_binding_sha256"],
        "backend_package": BACKEND_PACKAGE,
        "backend_version": BACKEND_VERSION,
        "backend_requirement": BACKEND_REQUIREMENT,
        "artifact_source": ARTIFACT_SOURCE,
        "artifact_filename": ARTIFACT_FILENAME,
        "artifact_sha256_required": ARTIFACT_SHA256,
        "artifact_interpreter_tag": ARTIFACT_INTERPRETER_TAG,
        "artifact_abi_tag": ARTIFACT_ABI_TAG,
        "artifact_platform_tag": ARTIFACT_PLATFORM_TAG,
        "artifact_publisher": ARTIFACT_PUBLISHER,
        "artifact_source_commit": ARTIFACT_SOURCE_COMMIT,
        "artifact_trusted_publishing_reported": ARTIFACT_TRUSTED_PUBLISHING_REPORTED,
        "artifact_attestation_verified": ARTIFACT_ATTESTATION_VERIFIED,
        "target_python_implementation": TARGET_PYTHON_IMPLEMENTATION,
        "target_python_min_major": TARGET_PYTHON_MIN[0],
        "target_python_min_minor": TARGET_PYTHON_MIN[1],
        "target_sys_platform": TARGET_SYS_PLATFORM,
        "target_machine_accepted": sorted(TARGET_MACHINE_ACCEPTED),
        "target_pointer_bits": TARGET_POINTER_BITS,
        "runtime_target_verified": False,
        "dependency_artifact_hash_verified": False,
        "dependency_installed": False,
        "dependency_imported": False,
        "cryptographic_backend_present": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_verifier_identity_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "ready_for_model_contact": False,
        "model_qualified": False,
        "status": "ARTIFACT_RUNTIME_BOUND_NOT_LOCALLY_VERIFIED_NOT_INSTALLED_NOT_CRYPTO_VERIFIED",
    }
    binding["artifact_runtime_binding_sha256"] = _sha256_payload(binding)
    return binding


_BINDING_KEYS = {
    "binding_version", "prep_version", "prep_type", "prep_base_main_commit",
    "source_v38_prep_version", "source_v38_binding_version", "source_v38_script_blob_sha",
    "source_v38_backend_binding_sha256", "backend_package", "backend_version", "backend_requirement",
    "artifact_source", "artifact_filename", "artifact_sha256_required", "artifact_interpreter_tag",
    "artifact_abi_tag", "artifact_platform_tag", "artifact_publisher", "artifact_source_commit",
    "artifact_trusted_publishing_reported", "artifact_attestation_verified",
    "target_python_implementation", "target_python_min_major", "target_python_min_minor",
    "target_sys_platform", "target_machine_accepted", "target_pointer_bits",
    "runtime_target_verified", "dependency_artifact_hash_verified", "dependency_installed",
    "dependency_imported", "cryptographic_backend_present", "cryptographic_verification_performed",
    "external_signature_verified", "external_verifier_identity_verified", "external_authority_attested",
    "external_trust_anchor_verified", "execution_authorized", "model_run_authorized",
    "model_contact_authorized", "ready_for_model_contact", "model_qualified", "status",
    "artifact_runtime_binding_sha256",
}


def validate_artifact_runtime_binding_preview(binding: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(binding, _BINDING_KEYS, "artifact/runtime binding")
    expected = build_artifact_runtime_binding_preview()
    if binding != expected:
        raise PermissionError("V39 artifact/runtime binding mismatch")
    return binding


def validate_runtime_facts(*, implementation: str, version: tuple[int, int], sys_platform: str,
                           machine: str, pointer_bits: int) -> dict[str, Any]:
    if implementation != TARGET_PYTHON_IMPLEMENTATION:
        raise PermissionError("V39 requires CPython")
    if not isinstance(version, tuple) or len(version) != 2 or not all(type(v) is int for v in version):
        raise PermissionError("V39 invalid Python version facts")
    if version < TARGET_PYTHON_MIN:
        raise PermissionError("V39 requires Python 3.11+")
    if sys_platform != TARGET_SYS_PLATFORM:
        raise PermissionError("V39 requires Windows win32 runtime")
    if machine not in TARGET_MACHINE_ACCEPTED:
        raise PermissionError("V39 requires Windows x86-64 machine")
    if pointer_bits != TARGET_POINTER_BITS:
        raise PermissionError("V39 requires 64-bit Python runtime")
    return {
        "python_implementation": implementation,
        "python_major": version[0],
        "python_minor": version[1],
        "sys_platform": sys_platform,
        "machine": machine,
        "pointer_bits": pointer_bits,
        "runtime_target_verified": True,
        "compatible_artifact_filename": ARTIFACT_FILENAME,
        "status": "RUNTIME_TARGET_VERIFIED_FOR_BOUND_WHEEL",
    }


def validate_current_runtime() -> dict[str, Any]:
    return validate_runtime_facts(
        implementation=platform.python_implementation(),
        version=(sys.version_info.major, sys.version_info.minor),
        sys_platform=sys.platform,
        machine=platform.machine(),
        pointer_bits=struct.calcsize("P") * 8,
    )


def _sha256_file(path: str | Path) -> str:
    try:
        p = Path(path)
        if not p.is_file():
            raise PermissionError("V39 artifact path is not a file")
        digest = hashlib.sha256()
        with p.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except PermissionError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise PermissionError("V39 cannot read artifact") from exc


def verify_distribution_artifact(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.name != ARTIFACT_FILENAME:
        raise PermissionError("V39 artifact filename mismatch")
    observed = _sha256_file(p)
    if observed != ARTIFACT_SHA256:
        raise PermissionError("V39 artifact SHA-256 mismatch")
    return {
        "artifact_filename": ARTIFACT_FILENAME,
        "artifact_sha256_required": ARTIFACT_SHA256,
        "artifact_sha256_observed": observed,
        "dependency_artifact_hash_verified": True,
        "dependency_installed": False,
        "dependency_imported": False,
        "cryptographic_backend_present": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_qualified": False,
        "status": "BOUND_DISTRIBUTION_ARTIFACT_SHA256_VERIFIED_NOT_INSTALLED",
    }


def reject_any_install_crypto_or_live_use() -> None:
    raise PermissionError("V39 verifies artifact/runtime only; install, crypto verification and live/model use remain forbidden")


def build_prep_report() -> dict[str, Any]:
    return {
        "mode": "MODEL_FREE_CRYPTO_ARTIFACT_RUNTIME_BINDING_PREP",
        "status": "PASS",
        "base_main_commit": BASE_MAIN_COMMIT,
        "artifact_filename": ARTIFACT_FILENAME,
        "artifact_sha256_required": ARTIFACT_SHA256,
        "runtime_target_verified": False,
        "dependency_artifact_hash_verified": False,
        "dependency_installed": False,
        "dependency_imported": False,
        "cryptographic_backend_present": False,
        "cryptographic_verification_performed": False,
        "external_signature_verified": False,
        "external_authority_attested": False,
        "external_trust_anchor_verified": False,
        "execution_authorized": False,
        "model_run_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "model_qualified": False,
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", action="store_true")
    group.add_argument("--check-runtime", action="store_true")
    group.add_argument("--verify-artifact", metavar="PATH")
    args = parser.parse_args(argv)
    if args.report:
        result = build_prep_report()
    elif args.check_runtime:
        result = validate_current_runtime()
    else:
        result = verify_distribution_artifact(args.verify_artifact)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
