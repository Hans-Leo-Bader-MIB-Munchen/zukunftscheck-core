#!/usr/bin/env python3
"""Risk-based unittest orchestration for ZS-KI-B development.

This module changes only *which existing tests are run at which development
stage*. It does not remove tests, weaken test assertions, authorize model use,
or make a fast-profile pass equivalent to the full suite.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import time
import unittest
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ORCHESTRATION_VERSION = "ZS-KI-B-TEST-ORCHESTRATION-RISK-BASED-REGRESSION-2026-001_v0.5"
BASE_MAIN_COMMIT = "39d57ded8108b0c8f724db15d36dbce1c22bf212"

# Deep baseline originated as an 18-module allowlist measured at 295 tests / 875.894 s.
# V38, V39 and V40 are added under the maintenance rule for new security-relevant blocks.
SECURITY_CRITICAL_DEEP_MODULES: tuple[str, ...] = (
    "tests.synthetic.test_sem_v25_max_tokens_binding_prep_v0_1",
    "tests.synthetic.test_sem_v26_one_shot_authorization_prep_v0_1",
    "tests.synthetic.test_sem_v27_approval_ceremony_architecture_prep_v0_1",
    "tests.synthetic.test_sem_v28_execution_gate_integration_prep_v0_1",
    "tests.synthetic.test_sem_v29_run_authorization_transform_prep_v0_1",
    "tests.synthetic.test_sem_v30_proof_enforcing_live_gate_prep_v0_1",
    "tests.synthetic.test_sem_v31_authority_state_atomic_consume_prep_v0_1",
    "tests.synthetic.test_sem_v32_external_state_atomic_consume_integration_prep_v0_1",
    "tests.synthetic.test_sem_v33_canonical_store_toctou_hardening_prep_v0_1",
    "tests.synthetic.test_sem_v34_authoritative_external_store_trust_anchor_binding_prep_v0_1",
    "tests.synthetic.test_sem_v35_external_attestation_global_single_use_prep_v0_1",
    "tests.synthetic.test_sem_v36_external_attestation_persistent_global_single_use_prep_v0_1",
    "tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1",
    "tests.synthetic.test_sem_v38_crypto_backend_dependency_binding_prep_v0_1",
    "tests.synthetic.test_sem_v39_crypto_artifact_runtime_binding_prep_v0_1",
    "tests.synthetic.test_sem_v40_cryptographic_signature_verification_prep_v0_1",
    "tests.synthetic.test_sem_runtime_guard_frozen_suite_sweep_v0_1",
    "tests.synthetic.test_semantic_runtime_guard_v0_1",
    "tests.synthetic.test_sem_canonical_binding_integrity_v0_1",
    "tests.synthetic.test_sem_system_qualification_execute_v0_2_gate",
    "tests.synthetic.test_sem_system_qualification_freeze_final_v0_2",
)

# Fast iteration gate. The original eight modules were measured at 51.465 s.
# V38/V39/V40 are short, security-relevant crypto/binding tests and are included from v0.5.
SECURITY_CRITICAL_FAST_MODULES: tuple[str, ...] = (
    "tests.synthetic.test_sem_v35_external_attestation_global_single_use_prep_v0_1",
    "tests.synthetic.test_sem_v36_external_attestation_persistent_global_single_use_prep_v0_1",
    "tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1",
    "tests.synthetic.test_sem_v38_crypto_backend_dependency_binding_prep_v0_1",
    "tests.synthetic.test_sem_v39_crypto_artifact_runtime_binding_prep_v0_1",
    "tests.synthetic.test_sem_v40_cryptographic_signature_verification_prep_v0_1",
    "tests.synthetic.test_sem_runtime_guard_frozen_suite_sweep_v0_1",
    "tests.synthetic.test_semantic_runtime_guard_v0_1",
    "tests.synthetic.test_sem_canonical_binding_integrity_v0_1",
    "tests.synthetic.test_sem_system_qualification_execute_v0_2_gate",
    "tests.synthetic.test_sem_system_qualification_freeze_final_v0_2",
)

# Backward-compatible name: must remain the deep suite, never silently weaken.
SECURITY_CRITICAL_MODULES = SECURITY_CRITICAL_DEEP_MODULES

_FOCUSED_MODULE_RE = re.compile(r"^tests\.synthetic\.test_[A-Za-z0-9_]+$")


def _validate_focused_module(module_name: str) -> str:
    if not isinstance(module_name, str) or not _FOCUSED_MODULE_RE.fullmatch(module_name):
        raise ValueError("focused module must match tests.synthetic.test_<name>")
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise ValueError(f"focused test module does not exist: {module_name}")
    origin = Path(spec.origin).resolve()
    tests_root = (ROOT / "tests" / "synthetic").resolve()
    try:
        origin.relative_to(tests_root)
    except ValueError as exc:
        raise ValueError("focused module resolves outside tests/synthetic") from exc
    if origin.suffix != ".py" or not origin.name.startswith("test_"):
        raise ValueError("focused module is not a Python test module")
    return module_name


def _load_named_modules(module_names: Iterable[str]) -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in module_names:
        suite.addTests(loader.loadTestsFromName(module_name))
    return suite


def _validate_allowlist(name: str, modules: tuple[str, ...]) -> None:
    if len(modules) != len(set(modules)):
        raise RuntimeError(f"{name} module allowlist contains duplicates")


def build_suite(profile: str, focused_modules: Iterable[str] = ()) -> unittest.TestSuite:
    if profile in {"critical", "critical-deep"}:
        _validate_allowlist("critical-deep", SECURITY_CRITICAL_DEEP_MODULES)
        return _load_named_modules(SECURITY_CRITICAL_DEEP_MODULES)
    if profile == "critical-fast":
        _validate_allowlist("critical-fast", SECURITY_CRITICAL_FAST_MODULES)
        if not set(SECURITY_CRITICAL_FAST_MODULES).issubset(set(SECURITY_CRITICAL_DEEP_MODULES)):
            raise RuntimeError("critical-fast must be a subset of critical-deep")
        return _load_named_modules(SECURITY_CRITICAL_FAST_MODULES)
    if profile == "full":
        return unittest.defaultTestLoader.discover(
            start_dir=str(ROOT / "tests"), pattern="test*.py", top_level_dir=str(ROOT)
        )
    if profile == "focused":
        validated = tuple(_validate_focused_module(name) for name in focused_modules)
        if not validated:
            raise ValueError("focused profile requires at least one --module")
        if len(validated) != len(set(validated)):
            raise ValueError("focused modules must be unique")
        return _load_named_modules(validated)
    raise ValueError(f"unsupported test profile: {profile}")


def run_profile(profile: str, focused_modules: Iterable[str] = (), verbosity: int = 1) -> int:
    suite = build_suite(profile, focused_modules)
    print(f"ZS-KI-B test profile: {profile}")
    print(f"orchestration_version: {ORCHESTRATION_VERSION}")
    print(f"base_main_commit: {BASE_MAIN_COMMIT}")
    print(f"selected_test_count: {suite.countTestCases()}")
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


def run_critical_module_timings(verbosity: int = 0) -> int:
    """Run the current deep allowlist module-by-module and report timings."""
    _validate_allowlist("critical-deep", SECURITY_CRITICAL_DEEP_MODULES)
    rows: list[tuple[float, int, str, bool]] = []
    all_ok = True
    total_start = time.perf_counter()
    print("ZS-KI-B critical-deep timing diagnostic")
    print(f"orchestration_version: {ORCHESTRATION_VERSION}")
    print(f"base_main_commit: {BASE_MAIN_COMMIT}")
    for module_name in SECURITY_CRITICAL_DEEP_MODULES:
        suite = _load_named_modules((module_name,))
        test_count = suite.countTestCases()
        start = time.perf_counter()
        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
        elapsed = time.perf_counter() - start
        ok = result.wasSuccessful()
        rows.append((elapsed, test_count, module_name, ok))
        all_ok = all_ok and ok
        print(f"TIMING {elapsed:10.3f}s  tests={test_count:3d}  ok={str(ok):5s}  {module_name}")
        if not ok:
            print("FAIL_CLOSED: timing diagnostic stopped after failing module", file=sys.stderr)
            break
    total_elapsed = time.perf_counter() - total_start
    print("\nSLOWEST_CRITICAL_MODULES")
    for elapsed, test_count, module_name, ok in sorted(rows, reverse=True)[:10]:
        print(f"{elapsed:10.3f}s  tests={test_count:3d}  ok={str(ok):5s}  {module_name}")
    print(f"TOTAL_CRITICAL_TIMING {total_elapsed:.3f}s  modules={len(rows)}  tests={sum(r[1] for r in rows)}")
    return 0 if all_ok else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ZS-KI-B unittest profiles")
    parser.add_argument(
        "--profile",
        choices=("focused", "critical-fast", "critical", "critical-deep", "full"),
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="focused unittest module, e.g. tests.synthetic.test_sem_v40_cryptographic_signature_verification_prep_v0_1",
    )
    parser.add_argument(
        "--critical-timings",
        action="store_true",
        help="diagnostic: run critical-deep module-by-module and print timings",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    if args.critical_timings and args.profile is not None:
        parser.error("--critical-timings cannot be combined with --profile")
    if not args.critical_timings and args.profile is None:
        parser.error("one of --profile or --critical-timings is required")
    if args.profile != "focused" and args.module:
        parser.error("--module is valid only with --profile focused")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.critical_timings:
            return run_critical_module_timings(verbosity=2 if args.verbose else 0)
        return run_profile(args.profile, args.module, verbosity=2 if args.verbose else 1)
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
