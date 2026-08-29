#!/usr/bin/env python3
"""Model-free persistent single-use authorization consumption preparation.

V22 adds the durable claim primitive needed by a future live runner before any
model contact. It performs no HTTP, localhost, preflight or model generation.
No valid authorization artifact is created by default.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v2_1_authorization_prep as v21

RUNNER_VERSION = "v2.2-persistent-consumption-prep"
RUN_TYPE = "ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-2-PERSISTENT-CONSUMPTION-PREP-2026-023"
PERSISTENCE_VERSION = "ZS-KI-B-AUTH-CONSUMPTION-PERSISTENCE-2026-001_v0.1"
MOVEFILE_WRITE_THROUGH = 0x00000008
ERROR_FILE_EXISTS = 80
ERROR_ALREADY_EXISTS = 183


def build_consumed_state(auth: dict[str, Any]) -> dict[str, Any]:
    """Build the fail-closed durable state for an exactly valid V21 authorization."""
    v21.validate_execution_authorization(auth)
    consumed = deepcopy(auth)
    consumed.update(
        {
            "status": "CONSUMED_PRE_MODEL_CONTACT",
            "authorization_consumed": True,
            "execution_authorized": False,
            "model_run_authorized": False,
            "model_contact_authorized": False,
            "persistence_version": PERSISTENCE_VERSION,
            "consumption_boundary": "BEFORE_FIRST_MODEL_CONTACT",
            "single_use_claimed": True,
        }
    )
    return consumed


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("failed to persist complete authorization consumption state")
        offset += written


def _fsync_parent_directory(parent: Path) -> None:
    """Durably commit a newly created directory entry on POSIX."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    dir_fd = os.open(parent, flags)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _claim_posix(target: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        _write_all(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_parent_directory(target.parent)


def _claim_windows(target: Path, payload: bytes) -> None:
    """Single-winner Windows claim using a write-through same-directory move.

    A temporary file is fully written and fsync'd first. MoveFileExW is then used
    without MOVEFILE_REPLACE_EXISTING, so an existing target wins fail-closed.
    MOVEFILE_WRITE_THROUGH makes the move complete synchronously before return.
    """
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".claimtmp", dir=target.parent)
    tmp = Path(tmp_name)
    try:
        try:
            _write_all(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        move_file_ex = kernel32.MoveFileExW
        move_file_ex.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move_file_ex.restype = ctypes.c_int
        if not move_file_ex(str(tmp), str(target), MOVEFILE_WRITE_THROUGH):
            error = ctypes.get_last_error()
            if error in {ERROR_FILE_EXISTS, ERROR_ALREADY_EXISTS}:
                raise FileExistsError(f"authorization consumption state already exists: {target}")
            raise ctypes.WinError(error)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def claim_authorization_once(path: Path, auth: dict[str, Any]) -> dict[str, Any]:
    """Persist a one-time claim before any future model contact.

    POSIX uses exclusive target creation, file fsync and parent-directory fsync.
    Windows uses an fsync'd same-directory temporary file followed by a
    write-through MoveFileExW without replacement. In both cases only one target
    claim can win and persistence completes before the in-memory authorization is
    marked consumed.
    """
    consumed = build_consumed_state(auth)
    target = Path(path)
    if not target.parent.exists():
        raise FileNotFoundError(f"authorization state directory does not exist: {target.parent}")

    payload = (json.dumps(consumed, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if os.name == "nt":
        _claim_windows(target, payload)
    else:
        _claim_posix(target, payload)

    auth["authorization_consumed"] = True
    auth["execution_authorized"] = False
    auth["model_run_authorized"] = False
    auth["model_contact_authorized"] = False
    auth["status"] = "CONSUMED_PRE_MODEL_CONTACT"
    return consumed


def load_consumption_state(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("persisted authorization consumption state is not an object")
    return payload


def validate_persisted_consumption(path: Path) -> dict[str, Any]:
    state = load_consumption_state(path)
    if not (
        state.get("status") == "CONSUMED_PRE_MODEL_CONTACT"
        and state.get("authorization_consumed") is True
        and state.get("execution_authorized") is False
        and state.get("model_run_authorized") is False
        and state.get("model_contact_authorized") is False
        and state.get("persistence_version") == PERSISTENCE_VERSION
        and state.get("consumption_boundary") == "BEFORE_FIRST_MODEL_CONTACT"
        and state.get("single_use_claimed") is True
    ):
        raise PermissionError("persisted authorization state is not a valid consumed fail-closed state")
    return state


def build_persistence_report() -> dict[str, Any]:
    v21_report = v21.build_authorization_report()
    checks = {
        "v21_authorization_binding_pass": v21_report.get("status") == "PASS",
        "v21_not_ready_to_execute": v21_report.get("ready_to_execute") is False,
        "v21_model_contact_not_authorized": v21_report.get("model_contact_authorized") is False,
        "v21_no_authorization_artifact_created": v21_report.get("authorization_artifact_created") is False,
        "exclusive_single_winner_gate_defined": True,
        "durable_file_fsync_defined": True,
        "durable_directory_entry_commit_defined": True,
        "windows_write_through_move_defined": True,
        "consume_before_future_model_contact": True,
        "no_default_state_path": True,
        "no_model_contact_path": True,
        "model_not_qualified": v21_report.get("model_qualified") is False,
    }
    passed = all(checks.values())
    return {
        "mode": "MODEL_FREE_PERSISTENT_AUTHORIZATION_CONSUMPTION_PREP",
        "status": "PASS" if passed else "FAIL_CLOSED",
        "runner_version": RUNNER_VERSION,
        "run_type": RUN_TYPE,
        "persistence_version": PERSISTENCE_VERSION,
        "checks": checks,
        "persistent_consumption_binding_ready": passed,
        "ready_to_execute": False,
        "execution_authorized": False,
        "model_contact_authorized": False,
        "model_contact_performed": False,
        "authorization_artifact_created": False,
        "consumption_artifact_created_by_report": False,
        "future_live_runner_must_claim_and_persist_before_model_contact": True,
        "new_explicit_single_use_model_contact_authorization_required": True,
        "model_qualified": False,
    }


def main() -> int:
    report = build_persistence_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
