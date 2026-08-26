import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zs_ki_b_sem_candidate_router_v0_1.py"

spec = importlib.util.spec_from_file_location("candidate_router_v0_1", SCRIPT)
router = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(router)


class CandidateRouterV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = router.load(router.QUESTIONS_PATH)["questions"]
        cls.meanings = router.load(router.MEANINGS_PATH)

    def synthetic_case(self, text: str):
        return {
            "case_id": "TEST-SYN",
            "source_locations": [
                {
                    "source_location_id": "SL-TEST",
                    "section_or_heading": "",
                    "page_reference": "1",
                    "original_text": text,
                }
            ],
        }

    def test_empty_or_lexically_uninformative_input_fails_closed(self):
        result = router.route(self.synthetic_case("xyzqv"), self.questions, self.meanings)
        self.assertEqual(result["mode"], "FULL_67_FAIL_CLOSED")
        self.assertEqual(result["selected_question_count"], 67)

    def test_reduced_route_never_exceeds_configured_limit(self):
        for path in router.CASE_PATHS:
            case = router.load(path)
            result = router.route(case, self.questions, self.meanings)
            if result["mode"] == "REDUCED_PF_EXPANDED":
                self.assertLessEqual(result["selected_question_count"], router.MAX_SELECTED_QUESTIONS)

    def test_selected_ids_always_resolve_to_reference_questions(self):
        all_ids = {row["question_id"] for row in self.questions}
        for path in router.CASE_PATHS:
            case = router.load(path)
            result = router.route(case, self.questions, self.meanings)
            self.assertTrue(set(result["selected_question_ids"]).issubset(all_ids))

    def test_no_human_gold_dependency_is_declared_or_imported(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("human_gold", source.replace('"human_gold_used": false', ""))
        self.assertNotIn("gold", source.replace("human-gold", ""))


if __name__ == "__main__":
    unittest.main()
