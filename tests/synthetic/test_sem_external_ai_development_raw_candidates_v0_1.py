"""Model-free static provenance and isolation checks for eight external-AI raw candidates.
These candidates are not bound to the existing 24-case runner, gold, or holdout.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "tests/fixtures/zs_ki_b_sem_external_ai_development_raw_candidates_v0_1.json"
EXISTING = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_challenges_v0_1.json"
MANIFEST = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_manifest_candidate_v0_2.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ExternalAiDevelopmentRawCandidatesV01(unittest.TestCase):
    def test_eight_unique_non_holdout_development_candidates(self):
        d = load(RAW)
        cases = d["cases"]
        self.assertEqual(d["case_count"], 8)
        self.assertEqual(len(cases), 8)
        ids = [c["candidate_id"] for c in cases]
        self.assertEqual(len(set(ids)), 8)
        self.assertTrue(all(s.startswith("ZS-KI-B-SEM-DEVRAW-2026-") for s in ids))
        self.assertEqual(len(set(c["original_incoming_label"] for c in cases)), 8)
        self.assertTrue(all(c["source_text_as_supplied"].strip() for c in cases))
        self.assertTrue(all(c["provenance_marker"] == "AI_ASSISTED_DEVELOPMENT_ONLY" for c in cases))
        self.assertTrue(all(c["provenance_basis"] == "USER_REPORTED_EXTERNAL_GENERATIVE_AI" for c in cases))
        self.assertTrue(all(c["gold_status"] == "NOT_CREATED" for c in cases))

    def test_fail_closed_flags_and_no_gold(self):
        d = load(RAW)
        for flag in ("qualification_claim_allowed", "execution_authorized", "model_contact_authorized",
                     "preflight_authorized", "automatic_retry_authorized", "automatic_rerun_authorized",
                     "output_repair_authorized", "ready_for_user_approval", "runner_bound",
                     "independent_human_holdout"):
            self.assertIs(d[flag], False, flag)
        self.assertEqual(d["gold_status"], "NOT_CREATED")
        self.assertEqual(d["hard_stop"], "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION")
        for c in d["cases"]:
            self.assertIs(c["runner_compatible_claim"], False)
            self.assertIs(c["model_run_authorized"], False)
            self.assertIs(c["preflight_authorized"], False)
            for prohibited in ("expected_assignments", "optional_assignments", "forbidden_assignments",
                               "expected_conflict_candidate"):
                self.assertNotIn(prohibited, c)

    def test_multi_source_claim_explicitly_open(self):
        d = load(RAW)
        c = next(c for c in d["cases"] if c["original_incoming_label"] == "H-FREE-01")
        self.assertEqual(c["source_structure"], "COMPOSITE_TWO_DESCRIBED_DOCUMENTS")
        self.assertEqual(c["source_location_mapping_status"], "OPEN_MULTI_SOURCE")
        self.assertNotIn("source_location_id", c)
        self.assertTrue(all(c["source_structure"] == "ONE_SYNTHETIC_DOCUMENT" for c in d["cases"] if c is not c))

    def test_not_part_of_pinned_24_development_cases(self):
        raw = load(RAW)
        old = load(EXISTING)
        manifest = load(MANIFEST)
        self.assertEqual(old["case_count"], 24)
        self.assertEqual(len(old["cases"]), 24)
        self.assertEqual(manifest["expected_case_count"], 24)
        self.assertEqual(len(manifest["ordered_case_ids"]), 24)
        self.assertFalse(set(c["candidate_id"] for c in raw["cases"]) & set(c["case_id"] for c in old["cases"]))
        self.assertTrue(all("source_location_id" not in c for c in raw["cases"]))


if __name__ == "__main__":
    unittest.main()
