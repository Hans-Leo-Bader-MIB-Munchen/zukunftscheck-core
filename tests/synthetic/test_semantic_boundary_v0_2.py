from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_V01 = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_1.schema.json"
SCHEMA_V02 = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_2.schema.json"
BOUNDARY_V02 = ROOT / "core/validation/semantic_boundary_v0_2.py"


def load_boundary_v02():
    if not BOUNDARY_V02.exists():
        raise AssertionError(f"missing implementation artifact: {BOUNDARY_V02.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("semantic_boundary_v0_2", BOUNDARY_V02)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def proposal(source_location_id: str | None = "SL-A") -> dict:
    value = {
        "proposal_id": "P-1",
        "normalized_statement": "Synthetischer Testbefund.",
        "finding_type_candidate": "DT",
        "evidence_relation_type_candidate": "DIRECT",
        "assignment_candidates": [],
        "conflict_candidate_refs": [],
        "gap_notes": [],
        "uncertainty_notes": [],
        "human_review_required": False,
    }
    if source_location_id is not None:
        value["source_location_id"] = source_location_id
    return value


def response(*proposals: dict, target: str = "SL-A") -> dict:
    return {
        "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        "source_location_id": target,
        "proposals": list(proposals),
    }


class SemanticBoundaryV02Tests(unittest.TestCase):
    def test_t1_v02_schema_requires_proposal_source_location(self) -> None:
        self.assertTrue(SCHEMA_V02.exists(), "v0.2 schema must exist")
        schema = json.loads(SCHEMA_V02.read_text(encoding="utf-8"))
        proposal_def = schema["$defs"]["proposal"]
        self.assertIn("source_location_id", proposal_def["required"])
        self.assertIn("source_location_id", proposal_def["properties"])
        self.assertEqual(
            schema["properties"]["contract_version"]["const"],
            "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
        )

    def test_t2_missing_proposal_source_location_fails_closed(self) -> None:
        boundary = load_boundary_v02()
        issues = boundary.validate_semantic_response_v0_2(
            response(proposal(None)),
            allowed_source_location_ids={"SL-A"},
            target_source_location_id="SL-A",
        )
        self.assertTrue(any(i.code == "MISSING_PROPOSAL_SOURCE_LOCATION_REF" for i in issues))

    def test_t3_unknown_proposal_source_location_fails_closed(self) -> None:
        boundary = load_boundary_v02()
        issues = boundary.validate_semantic_response_v0_2(
            response(proposal("SL-UNKNOWN")),
            allowed_source_location_ids={"SL-A"},
            target_source_location_id="SL-A",
        )
        self.assertTrue(any(i.code == "UNKNOWN_PROPOSAL_SOURCE_LOCATION_REF" for i in issues))

    def test_t4_multi_source_response_is_formally_valid(self) -> None:
        boundary = load_boundary_v02()
        result = response(proposal("SL-A"), {**proposal("SL-B"), "proposal_id": "P-2"}, target="SL-B")
        issues = boundary.validate_semantic_response_v0_2(
            result,
            allowed_source_location_ids={"SL-A", "SL-B"},
            target_source_location_id="SL-B",
        )
        self.assertEqual([], issues)

    def test_t5_top_level_target_anchor_must_match_case_target(self) -> None:
        boundary = load_boundary_v02()
        issues = boundary.validate_semantic_response_v0_2(
            response(proposal("SL-A"), target="SL-A"),
            allowed_source_location_ids={"SL-A", "SL-B"},
            target_source_location_id="SL-B",
        )
        self.assertTrue(any(i.code == "TARGET_SOURCE_LOCATION_MISMATCH" for i in issues))

    def test_t11_single_source_identity_is_fail_closed(self) -> None:
        boundary = load_boundary_v02()
        issues = boundary.validate_semantic_response_v0_2(
            response(proposal("SL-B"), target="SL-A"),
            allowed_source_location_ids={"SL-A"},
            target_source_location_id="SL-A",
        )
        self.assertTrue(issues)

    def test_t13_v01_contract_remains_unchanged_and_v02_is_separate(self) -> None:
        self.assertTrue(SCHEMA_V01.exists())
        self.assertTrue(SCHEMA_V02.exists())
        old = json.loads(SCHEMA_V01.read_text(encoding="utf-8"))
        new = json.loads(SCHEMA_V02.read_text(encoding="utf-8"))
        self.assertEqual(old["properties"]["contract_version"]["const"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.1")
        self.assertEqual(new["properties"]["contract_version"]["const"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")
        self.assertNotIn("source_location_id", old["$defs"]["proposal"]["properties"])
        self.assertIn("source_location_id", new["$defs"]["proposal"]["properties"])

    def test_t14_at_least_one_proposal_must_cover_target_anchor(self) -> None:
        boundary = load_boundary_v02()
        result = response(proposal("SL-A"), {**proposal("SL-A"), "proposal_id": "P-2"}, target="SL-B")
        issues = boundary.validate_semantic_response_v0_2(
            result,
            allowed_source_location_ids={"SL-A", "SL-B"},
            target_source_location_id="SL-B",
        )
        self.assertTrue(any(i.code == "TARGET_SOURCE_LOCATION_NOT_COVERED" for i in issues))


if __name__ == "__main__":
    unittest.main()
