#!/usr/bin/env python3
"""One-shot ZS-KI-B local structured-output smoke-test runner v0.2.

Default mode is dry-run and performs no network call. --execute is required for
exactly one local inference request. The endpoint remains restricted to loopback.
No retry or output repair is performed. Every executed attempt is persisted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.local_model.openai_compatible import LocalModelError, validate_local_base_url
from llm.local_model.structured_output_v0_2 import (
    OUTPUT_MODE_VERSION,
    build_response_format,
    chat_completion_structured,
)
from llm.smoketest import build_messages, canonical_json, evaluate_smoke, parse_model_json, sha256_text

CASE_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_smoketest_case_v0_1.json"
EXPECT_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_smoketest_expectations_v0_1.json"
PROMPT_PATH = ROOT / "llm" / "prompts" / "zs_ki_b_smoketest_system_v0_1.txt"
DEFAULT_OUTPUT = "zs_ki_b_smoketest_result_v0_2.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_synthetic_only(case: dict) -> None:
    if case.get("data_class") != "SYNTHETIC_ONLY":
        raise ValueError("smoketest runner requires data_class=SYNTHETIC_ONLY")


def current_git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot resolve clean git state for auditable run manifest") from exc
    if status.stdout.strip():
        raise RuntimeError("working tree must be clean for auditable run manifest")
    commit = completed.stdout.strip()
    if len(commit) != 40 or any(ch not in "0123456789abcdefABCDEF" for ch in commit):
        raise RuntimeError("invalid git commit returned for auditable run manifest")
    return commit.lower()


def persist_result(result: dict, output_path: str) -> None:
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    Path(output_path).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def provider_metadata(envelope: dict) -> dict:
    return {
        "id": envelope.get("id"),
        "model": envelope.get("model"),
        "created": envelope.get("created"),
        "usage": envelope.get("usage"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="genau einen lokalen strukturierten Modellaufruf ausführen")
    parser.add_argument("--model", default="", help="lokale Modell-ID; für --execute erforderlich")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Audit-JSON des ausgeführten Einmallaufs (Standard: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    base_url = validate_local_base_url(args.base_url)
    case = load(CASE_PATH)
    require_synthetic_only(case)
    expectations = load(EXPECT_PATH)
    messages = build_messages(case)
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    response_format = build_response_format()

    manifest = {
        "run_type": "ZS-KI-B-LOCAL-MODEL-SMOKETEST-2026-001",
        "runner_version": "v0.2",
        "output_mode_version": OUTPUT_MODE_VERSION,
        "git_commit": current_git_commit(),
        "case_id": case["case_id"],
        "data_class": case["data_class"],
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1",
        "prompt_version": "zs_ki_b_smoketest_system_v0_1",
        "prompt_sha256": sha256_text(prompt_text),
        "case_sha256": sha256_text(canonical_json(case)),
        "expectations_sha256": sha256_text(canonical_json(expectations)),
        "response_format_sha256": sha256_text(canonical_json(response_format)),
        "base_url": base_url,
        "model": args.model or None,
        "execution_attempted": False,
        "executed": False,
        "retry_count": 0,
        "output_repair": False,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    if not args.execute:
        result = {
            "mode": "DRY_RUN_STRUCTURED_V0_2",
            "manifest": manifest,
            "message_count": len(messages),
            "response_format": response_format,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not args.model.strip():
        parser.error("--model ist zusammen mit --execute erforderlich")

    manifest["execution_attempted"] = True
    try:
        content, envelope = chat_completion_structured(
            base_url=base_url,
            model=args.model,
            messages=messages,
            temperature=0.0,
        )
    except LocalModelError as exc:
        result = {
            "mode": "EXECUTED_ONCE_FAILED_STRUCTURED_V0_2",
            "manifest": manifest,
            "model_response_raw": None,
            "model_response": None,
            "evaluation": {
                "passed": False,
                "criteria": {"endpoint_response_pass": False},
                "endpoint_error": f"{type(exc).__name__}: {exc}",
            },
            "provider_envelope_metadata": None,
        }
        persist_result(result, args.output)
        return 2

    manifest["executed"] = True
    manifest["model"] = args.model
    manifest["model_response_sha256"] = sha256_text(content)

    try:
        response = parse_model_json(content)
    except (json.JSONDecodeError, ValueError) as exc:
        result = {
            "mode": "EXECUTED_ONCE_FAILED_STRUCTURED_V0_2",
            "manifest": manifest,
            "model_response_raw": content,
            "model_response": None,
            "evaluation": {
                "passed": False,
                "criteria": {"parse_pass": False},
                "parse_error": f"{type(exc).__name__}: {exc}",
            },
            "provider_envelope_metadata": provider_metadata(envelope),
        }
        persist_result(result, args.output)
        return 2

    evaluation = evaluate_smoke(response, case=case, expectations=expectations)
    result = {
        "mode": "EXECUTED_ONCE_STRUCTURED_V0_2",
        "manifest": manifest,
        "model_response_raw": content,
        "model_response": response,
        "evaluation": evaluation,
        "provider_envelope_metadata": provider_metadata(envelope),
    }
    persist_result(result, args.output)
    return 0 if evaluation["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
