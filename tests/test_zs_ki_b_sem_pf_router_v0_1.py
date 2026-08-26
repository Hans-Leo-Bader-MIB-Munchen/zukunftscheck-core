import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zs_ki_b_sem_pf_router_v0_1.py"

spec = importlib.util.spec_from_file_location("pf_router_v0_1", SCRIPT)
router = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(router)


class PfRouterV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = router.load(router.QUESTIONS_PATH)["questions"]
        cls.holdouts = router.load(router.HOLDOUT_PATH)["cases"]
        cls.semantics = router.load_pf_semantics()

    def test_uninformative_text_fails_closed_to_all_questions(self):
        result = router.route_text("xyzqv", self.questions, self.semantics)
        self.assertEqual(result["mode"], "FULL_FAIL_CLOSED")
        self.assertEqual(result["selected_question_count"], 67)
        self.assertEqual(result["selected_pf_count"], 12)

    def test_reduced_route_keeps_complete_pf_question_groups(self):
        grouped = router.questions_by_pf(self.questions)
        for case in self.holdouts:
            result = router.route_text(case["text"], self.questions, self.semantics)
            if result["mode"] != "REDUCED_PF_STAGE_A":
                continue
            expected_ids = [qid for pf in result["selected_pf_ids"] for qid in grouped[pf]]
            self.assertEqual(result["selected_question_ids"], expected_ids)

    def test_reduced_route_never_exceeds_pf_limit(self):
        for case in self.holdouts:
            result = router.route_text(case["text"], self.questions, self.semantics)
            if result["mode"] == "REDUCED_PF_STAGE_A":
                self.assertLessEqual(result["selected_pf_count"], router.MAX_SELECTED_PFS)

    def test_holdout_expected_pfs_are_never_silently_excluded(self):
        for case in self.holdouts:
            result = router.route_text(case["text"], self.questions, self.semantics)
            if result["mode"] == "FULL_FAIL_CLOSED":
                continue
            self.assertTrue(set(case["expected_pf_ids"]).issubset(set(result["selected_pf_ids"])), case["case_id"])

    def test_holdouts_are_not_known_regression_case_ids(self):
        for case in self.holdouts:
            self.assertNotIn("R16", case["case_id"])
            self.assertNotIn("R18", case["case_id"])
            self.assertNotIn("R21", case["case_id"])
            self.assertNotIn("R22", case["case_id"])

    def test_pf_semantics_cover_exactly_all_reference_pfs(self):
        reference_pfs = {row["pf_id"] for row in self.questions}
        self.assertEqual(set(self.semantics), reference_pfs)

    def test_pf_semantics_contains_no_case_specific_ids(self):
        source = router.PF_SEMANTICS_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ("r16", "r18", "r21", "r22", "ho-001", "ho-002", "ho-003", "ho-004", "ho-005", "ho-006"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
