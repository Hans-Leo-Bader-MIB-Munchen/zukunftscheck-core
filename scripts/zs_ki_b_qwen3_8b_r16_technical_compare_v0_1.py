#!/usr/bin/env python3
"""One-shot local technical comparison: qwen3-8b on R16 full v0.6 request.

Technical/runtime diagnosis only. Synthetic data only. Loopback only. No retries.
No Human-Gold, qualification, production, or generalisation claim.

The user message is prefixed with /no_think as an explicit diagnostic mutation so
that the comparison targets non-reasoning throughput, matching the earlier local
runtime diagnosis where reasoning_tokens=0 was the intended condition.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.zs_ki_b_sem_qualifikation_runner_v0_6 as runner
from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_5 import chat_completion_structured
from llm.smoketest import parse_model_json

MODEL_DEFAULT = "qwen/qwen3-8b"
BASE_URL_DEFAULT = "http://127.0.0.1:1234/v1"


def r16_case() -> dict[str, Any]:
    for path in runner.CASE_PATHS:
        case = runner.load(path)
        if case.get("case_id") == "ZS-KI-B-SEM-R16-SYN-001":
            return case
    raise RuntimeError("R16 fixture not found")


def diagnostic_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    prompt_text = runner.PROMPT_PATH.read_text(encoding="utf-8")
    messages = runner.build_messages(case, prompt_text)
    if len(messages) != 2 or messages[1].get("role") != "user":
        raise RuntimeError("unexpected v0.6 message shape")
    messages = [dict(row) for row in messages]
    messages[1]["content"] = "/no_think\n" + messages[1]["content"]
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    args = parser.parse_args()

    base_url = validate_local_base_url(args.base_url)
    case = r16_case()
    messages = diagnostic_messages(case)

    result: dict[str, Any] = {
        "mode": "LOCAL_TECHNICAL_QWEN3_8B_R16_COMPARE_V0_1",
        "model": args.model,
        "base_url": base_url,
        "case_id": case["case_id"],
        "data_class": "SYNTHETIC_ONLY",
        "runner_reference": runner.RUNNER_VERSION,
        "prompt_reference": runner.PROMPT_VERSION,
        "diagnostic_mutation": "/no_think prefix on user message",
        "retry_count": 0,
        "model_contact": True,
        "remote_cloud": False,
        "qualification_claim": False,
        "human_gold_used": False,
        "production_claim": False,
        "elapsed_seconds": None,
        "provider_usage": None,
        "parse_pass": False,
        "boundary_pass": False,
        "endpoint_error": None,
        "parse_error": None,
        "boundary_evaluation": None,
        "model_response": None,
    }

    started = time.perf_counter()
    try:
        content, envelope = chat_completion_structured(
            base_url=base_url,
            model=args.model,
            messages=messages,
            temperature=0.0,
        )
    except LocalModelError as exc:
        result["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        result["endpoint_error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    result["elapsed_seconds"] = round(time.perf_counter() - started, 2)
    result["provider_usage"] = envelope.get("usage")

    try:
        response = parse_model_json(content)
        result["parse_pass"] = True
        result["model_response"] = response
    except (json.JSONDecodeError, ValueError) as exc:
        result["parse_error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    boundary = runner.evaluate_boundary(case, response)
    result["boundary_evaluation"] = boundary
    result["boundary_pass"] = bool(boundary.get("passed"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["boundary_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
