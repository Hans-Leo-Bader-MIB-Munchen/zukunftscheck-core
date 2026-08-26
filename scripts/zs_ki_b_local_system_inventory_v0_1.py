#!/usr/bin/env python3
"""Local-only inventory for model/hardware decision.

Reads LM Studio /v1/models on loopback and NVIDIA GPU information via nvidia-smi.
No model inference is performed. No remote/cloud endpoint is allowed.
"""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE_URL = "http://127.0.0.1:1234/v1"


def require_loopback(url: str) -> None:
    parsed = urlparse(url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("non-loopback endpoint rejected")


def get_models() -> dict:
    require_loopback(BASE_URL)
    req = urllib.request.Request(f"{BASE_URL}/models", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def get_gpu() -> dict:
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,memory.free,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    if completed.returncode != 0:
        return {"error": completed.stderr.strip() or f"nvidia-smi exit {completed.returncode}"}
    rows = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            rows.append({"raw": line})
            continue
        rows.append({
            "name": parts[0],
            "memory_total_mib": int(parts[1]),
            "memory_used_mib": int(parts[2]),
            "memory_free_mib": int(parts[3]),
            "driver_version": parts[4],
        })
    return {"gpus": rows}


def main() -> int:
    result = {
        "mode": "LOCAL_SYSTEM_INVENTORY_V0_1",
        "model_inference": False,
        "remote_cloud": False,
        "base_url": BASE_URL,
        "models": get_models(),
        "gpu": get_gpu(),
        "decision_guardrail": (
            "This inventory only establishes locally available models and GPU capacity. "
            "It does not qualify any model semantically."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
