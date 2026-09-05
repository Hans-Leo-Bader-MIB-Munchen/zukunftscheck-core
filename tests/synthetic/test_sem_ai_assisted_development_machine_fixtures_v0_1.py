import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHALLENGES = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_challenges_v0_1.json"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_gold_v0_2.json"
MANIFEST = ROOT / "tests/fixtures/zs_ki_b_sem_ai_assisted_development_manifest_candidate_v0_1.json"
REFERENCE_QUESTIONS = ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json"
CATALOG = ROOT / "docs/ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-CHALLENGE-CATALOG-2026-001_v0.1.md"


class TestSemAiAssistedDevelopmentMachineFixturesV01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.challenges = json.loads(CHALLENGES.read_text(encoding="utf-8"))
        cls.gold = json.loads(GOLD.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.reference = json.loads(REFERENCE_QUESTIONS.read_text(encoding="utf-8"))
        cls.catalog = CATALOG.read_text(encoding="utf-8")

    def test_exact_24_case_order_matches_manifest_and_gold(self):
        challenge_ids = [c["case_id"] for c in self.challenges["cases"]]
        gold_ids = [c["case_id"] for c in self.gold["cases"]]
        self.assertEqual(self.challenges["case_count"], 24)
        self.assertEqual(self.gold["case_count"], 24)
        self.assertEqual(challenge_ids, self.manifest["ordered_case_ids"])
        self.assertEqual(gold_ids, challenge_ids)
        self.assertEqual(len(set(challenge_ids)), 24)

    def test_every_machine_case_text_is_present_in_catalog(self):
        for case in self.challenges["cases"]:
            self.assertIn(case["case_id"], self.catalog)
            self.assertIn(case["source_location_id"], self.catalog)
            self.assertIn(case["text"], self.catalog)

    def test_gold_question_ids_exist_and_sets_are_disjoint_per_case(self):
        valid_ids = set()
        for pf in self.reference.get("prueffelder", self.reference.get("reference_questions", [])):
            if isinstance(pf, dict):
                for q in pf.get("fragen", pf.get("questions", [])):
                    if isinstance(q, dict) and isinstance(q.get("question_id"), str):
                        valid_ids.add(q["question_id"])
        if not valid_ids:
            def walk(value):
                if isinstance(value, dict):
                    qid = value.get("question_id")
                    if isinstance(qid, str):
                        valid_ids.add(qid)
                    for v in value.values():
                        walk(v)
                elif isinstance(value, list):
                    for v in value:
                        walk(v)
            walk(self.reference)
        self.assertEqual(len(valid_ids), 67)
        for case in self.gold["cases"]:
            required = set(case["required"])
            optional = set(case["optional"])
            forbidden = set(case["forbidden"])
            self.assertTrue((required | optional | forbidden).issubset(valid_ids), case["case_id"])
            self.assertTrue(required.isdisjoint(optional), case["case_id"])
            self.assertTrue(required.isdisjoint(forbidden), case["case_id"])
            self.assertTrue(optional.isdisjoint(forbidden), case["case_id"])

    def test_time_002_specificity_adjudication_is_explicit(self):
        record = next(c for c in self.gold["cases"] if c["case_id"].endswith("TIME-002"))
        self.assertEqual(record["required"], ["4.2", "4.5"])
        self.assertEqual(record["optional"], [])
        self.assertEqual(record["forbidden"], ["11.1"])
        self.assertTrue(record["conflict_expected"])
        self.assertTrue(record["human_review_expected"])
        self.assertIn("decision relevance", self.gold["time_002_adjudication"])

    def test_governance_stays_development_only(self):
        self.assertEqual(self.challenges["status"], "AI_ASSISTED_DEVELOPMENT_ONLY")
        self.assertEqual(self.challenges["data_class"], "SYNTHETIC_ONLY")
        self.assertFalse(self.challenges["qualification_claim_allowed"])
        self.assertEqual(self.gold["status"], "AI_ASSISTED_DEVELOPMENT_ONLY")
        self.assertFalse(self.gold["qualification_gold"])


if __name__ == "__main__":
    unittest.main()
