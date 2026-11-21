"""Regulatory 3.4 model-free static regression, no model contact."""
import json
import unittest
from pathlib import Path
from core.validation.validator import ROOT

def load(relative):
    return json.loads((ROOT/relative).read_text(encoding="utf-8"))

class Regulatory34Tests(unittest.TestCase):
    def test_r1_r2_r3_r4(self):
        old=load("domains/zukunftscheck/rules/reference_questions_v0_1.json")
        new=load("domains/zukunftscheck/rules/reference_questions_v0_2.json")
        self.assertEqual(len(old["questions"]),67)
        self.assertEqual(len(new["questions"]),67)
        self.assertEqual([(x["question_id"],x["pf_id"]) for x in old["questions"]],[(x["question_id"],x["pf_id"]) for x in new["questions"]])
        diff=[(o,n) for o,n in zip(old["questions"],new["questions"]) if o!=n]
        self.assertEqual(len(diff),1)
        self.assertEqual(diff[0][0]["question_id"],"3.4")
        self.assertEqual(diff[0][1]["pf_id"],"PF3")
        self.assertEqual(diff[0][1]["question"],"Welche Fristen, Termine, laufenden Verfahren oder aktuell wirksam werdenden beziehungsweise absehbaren regulatorischen Änderungen sind für die Orientierungsfrage, die anstehende Entscheidung oder die vorgesehene Verwendung erheblich?")
        self.assertEqual(new["source_drive_file_id"],"18ws6TryEYZWLboO_fVY0IzZWgAN3nrQRzo-jly2x3GE")
    def test_r4_r13_r14(self):
        old=load("domains/zukunftscheck/rules/reference_question_meanings_v0_7.json")
        new=load("domains/zukunftscheck/rules/reference_question_meanings_v0_8.json")
        self.assertEqual(len(new["meanings"]),67)
        self.assertEqual([x for x in old["meanings"] if x["question_id"]!="3.4"],[x for x in new["meanings"] if x["question_id"]!="3.4"])
        r=next(x for x in new["meanings"] if x["question_id"]=="3.4")
        self.assertIn("erhebliche Fristen",r["positive_scope"])
        self.assertIn("September-Termin",r["disambiguation_notes"])
        self.assertIn("ohne erkennbaren Bezug",r["negative_scope"])
        self.assertIn("keine Vollständigkeitszusage",new["calibration_scope"])
    def test_r15_bound_versions_without_execution(self):
        from scripts import zs_ki_b_sem_ai_assisted_development_live_runner_candidate_v0_2 as runner
        self.assertIsInstance(runner.validate_static_package(),dict)
        b=load("tests/fixtures/zs_ki_b_sem_ai_assisted_development_runtime_binding_candidate_v0_2.json")
        self.assertFalse(b["model_contact_authorized"])
        self.assertFalse(b["execution_authorized"])
        self.assertEqual(b["h5_status"],"SEPARATE_NOT_AUTHORIZED")
        with self.assertRaises(PermissionError):
            runner.execute_once()

if __name__=="__main__":
    unittest.main()
