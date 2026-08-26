#!/usr/bin/env python3
"""One-run model-free post-fix validation for PF router v0.1.

This script reads the frozen validation fixture and evaluates the unchanged
Stage-A PF router. It does not call a model or network service and does not
modify router semantics, thresholds, or the frozen fixture.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "scripts" / "zs_ki_b_sem_pf_router_v0_1.py"
VALIDATION_PATH = ROOT / "tests" / "fixtures" / "zs_ki_b_sem_pf_router_postfix_validation_FROZEN_v0_1.json"

spec = importlib.util.spec_from_file_location("pf_router_v0_1", ROUTER_PATH)
router = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(router)


def main() -> int:
    questions = router.load(router.QUESTIONS_PATH)["questions"]
    semantics = router.load_pf_semantics()
    validation = router.load(VALIDATION_PATH)

    rows = []
    pass_count = 0
    reduced_count = 0
    fail_closed_count = 0

    for case in validation["cases"]:
        result = router.route_text(case["text"], questions, semantics)
        expected = set(case["expected_pf_ids"])
        selected = set(result["selected_pf_ids"])
        expected_retained = expected.issubset(selected)
        if result["mode"] == "REDUCED_PF_STAGE_A":
            reduced_count += 1
        else:
            fail_closed_count += 1
        if expected_retained:
            pass_count += 1
        rows.append({
            "case_id": case["case_id"],
            "expected_pf_ids": case["expected_pf_ids"],
            "mode": result["mode"],
            "selected_pf_ids": result["selected_pf_ids"],
            "selected_question_count": result["selected_question_count"],
            "fallback_reasons": result["fallback_reasons"],
            "expected_pf_ids_retained": expected_retained,
        })

    total = len(rows)
    overall = "PASS" if pass_count == total else "FAIL"
    report = {
        "mode": "MODEL_FREE_PF_ROUTER_POSTFIX_VALIDATION_V0_1",
        "fixture_status": validation.get("status"),
        "model_contact": False,
        "network_contact": False,
        "qualification_claim": False,
        "production_routing_claim": False,
        "case_count": total,
        "pass_count": pass_count,
        "fail_count": total - pass_count,
        "reduced_route_count": reduced_count,
        "fail_closed_route_count": fail_closed_count,
        "overall": overall,
        "cases": rows,
        "interpretation_guardrail": "PASS means only that the frozen post-fix validation cases retain all pre-specified expected PFs under the unchanged model-free Stage-A router. It is not production validation and does not validate Stage B or model semantics."
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
