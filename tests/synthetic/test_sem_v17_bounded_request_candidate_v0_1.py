from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "tests/fixtures/zs_ki_b_sem_v17_bounded_request_candidate_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
SUITE = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_suite_frozen_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class V17BoundedRequestCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = load(CANDIDATE)
        self.gold = load(GOLD)
        self.suite = load(SUITE)

    def test_b01_candidate_is_model_free_and_not_authorized(self) -> None:
        self.assertEqual(self.candidate["status"], "MODEL_FREE_DESIGN_CANDIDATE_NOT_AUTHORIZED")
        gov = self.candidate["governance"]
        self.assertFalse(gov["model_contact_authorized"])
        self.assertFalse(gov["preflight_authorized"])
        self.assertFalse(gov["qualification_execution_authorized"])
        self.assertFalse(gov["model_qualified"])
        self.assertTrue(gov["new_explicit_model_contact_authorization_required_before_any_execution"])

    def test_b02_output_generation_is_finitely_bounded_in_candidate(self) -> None:
        transport = self.candidate["candidate_transport"]
        self.assertGreater(transport["max_completion_tokens"], 0)
        self.assertLessEqual(transport["max_completion_tokens"], 1024)
        self.assertEqual(transport["retry_count"], 0)
        self.assertFalse(transport["output_repair"])

    def test_b03_schema_arrays_are_all_given_finite_candidate_caps(self) -> None:
        caps = self.candidate["candidate_schema_cardinalities"]
        for key, value in caps.items():
            if key.endswith("_max_items") or "max_items_per_proposal" in key:
                self.assertIsInstance(value, int)
                self.assertGreater(value, 0)
        self.assertIn("Engineering safety bounds", caps["non_assignment_caps_evidence"])

    def test_b04_candidate_caps_cover_frozen_gold_assignment_counts_conservatively(self) -> None:
        max_required_plus_optional = 0
        for case in self.gold["cases"]:
            required = len(case.get("expected_assignments", []))
            optional = len(case.get("optional_assignments", []))
            max_required_plus_optional = max(max_required_plus_optional, required + optional)
        cap = self.candidate["candidate_schema_cardinalities"]["assignment_candidates_max_items_per_proposal"]
        # Deliberately conservative: compares a per-case Gold maximum to the
        # tighter per-proposal candidate cap; it does not assert one proposal
        # per SourceLocation or collapse semantically distinct statements.
        self.assertLessEqual(max_required_plus_optional, cap)
        self.assertEqual(max_required_plus_optional, 3)

    def test_b05_first_candidate_does_not_reduce_semantic_context(self) -> None:
        strategy = self.candidate["context_strategy"]
        self.assertTrue(strategy["first_candidate_preserves_all_67_reference_questions"])
        self.assertTrue(strategy["first_candidate_preserves_all_67_meaning_entries"])
        self.assertFalse(strategy["pf_prefiltering_allowed"])

    def test_b06_candidate_proposal_cap_exceeds_frozen_source_location_count(self) -> None:
        max_locations = max(len(case["source_locations"]) for case in self.suite["cases"])
        proposal_cap = self.candidate["candidate_schema_cardinalities"]["proposals_max_items"]
        self.assertEqual(max_locations, 2)
        self.assertGreaterEqual(proposal_cap, max_locations)

    def test_b07_free_text_fields_have_finite_candidate_bounds(self) -> None:
        bounds = self.candidate["candidate_text_lengths"]
        for key in (
            "normalized_statement_max_length",
            "derivation_note_max_length",
            "gap_note_max_length",
            "uncertainty_note_max_length",
        ):
            self.assertIsInstance(bounds[key], int)
            self.assertGreater(bounds[key], 0)
        self.assertEqual(bounds["evidence_class"], "ENGINEERING_BOUNDS_NOT_GOLD_DERIVED")

    def test_b08_prompt_candidate_requires_concise_non_redundant_free_text(self) -> None:
        prompt_meta = self.candidate["candidate_prompt"]
        self.assertEqual(prompt_meta["status"], "MODEL_FREE_PROMPT_CANDIDATE_NOT_EXECUTION_BOUND")
        self.assertTrue(prompt_meta["required_concision_instruction"])
        prompt_path = ROOT / prompt_meta["path"]
        text = prompt_path.read_text(encoding="utf-8")
        self.assertIn("so knapp wie möglich", text)
        self.assertIn("ohne Wiederholungen", text)


if __name__ == "__main__":
    unittest.main()
