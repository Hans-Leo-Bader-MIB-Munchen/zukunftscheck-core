import copy
import json
import unittest
from pathlib import Path

from core.validation.validator import validate_bundle, validate_original_text_change

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "zs_ki_b_e2e_valid_bundle_v0_1.json"


def load_bundle():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class ZsKiBE2EWorkflowTests(unittest.TestCase):
    def codes(self, bundle):
        return {issue.code for issue in validate_bundle(bundle)}

    def test_E01_complete_happy_path(self):
        self.assertEqual([], validate_bundle(load_bundle()))

    def test_E02_evidence_modes_are_all_covered(self):
        modes = {r["evidence_relation_type"] for r in load_bundle()["evidence_relations"]}
        self.assertEqual({"DIRECT", "DERIVED", "UNSUPPORTED"}, modes)

    def test_E03_same_finding_can_map_to_multiple_questions(self):
        b = load_bundle()
        mappings = [r for r in b["assignments"] if r["finding_id"] == "F-SYN-3"]
        self.assertEqual(2, len(mappings))
        self.assertEqual({"PF4", "PF11"}, {r["pf_id"] for r in mappings})

    def test_E04_unclear_location_is_fail_closed_to_review(self):
        b = load_bundle()
        loc = next(r for r in b["source_locations"] if r["source_location_id"] == "LOC-SYN-3")
        self.assertEqual("UNCLEAR", loc["locator_quality"])
        self.assertTrue(loc["human_review_required"])
        loc["human_review_required"] = False
        self.assertIn("MISSING_REVIEW_FLAG", self.codes(b))

    def test_E05_uncertain_assignment_is_fail_closed_to_review(self):
        b = load_bundle()
        assignment = next(r for r in b["assignments"] if r["assignment_id"] == "A-SYN-4")
        self.assertEqual("UNCERTAIN", assignment["assignment_confidence"])
        self.assertTrue(assignment["human_review_required"])
        assignment["human_review_required"] = False
        self.assertIn("MISSING_REVIEW_FLAG", self.codes(b))

    def test_E06_pf_question_mismatch_is_rejected(self):
        b = load_bundle()
        b["assignments"][0]["pf_id"] = "PF5"
        self.assertIn("PF_QUESTION_MISMATCH", self.codes(b))

    def test_E07_conflict_candidate_and_confirmed_remain_distinct(self):
        states = {r["conflict_status"] for r in load_bundle()["conflicts"]}
        self.assertEqual({"CANDIDATE", "CONFIRMED"}, states)

    def test_E08_original_text_overwrite_is_rejected(self):
        before = load_bundle()
        after = copy.deepcopy(before)
        after["source_locations"][0]["original_text"] = "überschriebener synthetischer Text"
        issues = validate_original_text_change(before, after)
        self.assertEqual(["PROVENANCE_OVERWRITE"], [i.code for i in issues])

    def test_E09_real_data_class_is_blocked(self):
        b = load_bundle()
        b["run_manifest"]["development_data_class"] = "REAL"
        self.assertIn("REAL_DATA_BLOCKED", self.codes(b))

    def test_E10_llm_use_is_blocked(self):
        b = load_bundle()
        b["run_manifest"]["llm_used"] = True
        self.assertIn("LLM_NOT_ALLOWED", self.codes(b))

    def test_E11_nonhuman_human_decision_is_rejected(self):
        b = load_bundle()
        b["human_decisions"][0]["actor_type"] = "AI"
        self.assertIn("NONHUMAN_APPROVAL", self.codes(b))

    def test_E12_unsupported_evidence_needs_no_source_location(self):
        b = load_bundle()
        unsupported = next(r for r in b["evidence_relations"] if r["evidence_relation_type"] == "UNSUPPORTED")
        self.assertNotIn("source_location_id", unsupported)
        self.assertEqual([], validate_bundle(b))


if __name__ == "__main__":
    unittest.main()
