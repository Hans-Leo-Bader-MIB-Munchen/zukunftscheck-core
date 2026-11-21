"""Fail-closed MODEL-FREE version-chain regression for Regulatory 3.4.
No model, network, preflight, localhost, execution, or external authority.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = "tests/fixtures/zs_ki_b_sem_ai_assisted_development_"
MANIFEST = P + "manifest_candidate_v0_2.json"
FREEZE = P + "prep_freeze_binding_v0_2.json"
PREFLIGHT = P + "preflight_authorization_prep_candidate_v0_2.json"
AUTH = P + "authorization_prep_candidate_v0_5.json"
HARD_STOP = "NO_MODEL_CONTACT_WITHOUT_SEPARATE_EXPLICIT_USER_AUTHORIZATION"
FALSE_FLAGS = ("qualification_claim_allowed", "execution_authorized", "model_contact_authorized",
               "preflight_authorized", "automatic_retry_authorized", "automatic_rerun_authorized",
               "output_repair_authorized", "ready_for_user_approval")

def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))

def git_blob_sha1(p):
    data = (ROOT / p).read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError("bare CR in bound blob: " + p)
    return hashlib.sha1(f"blob {len(data)}\\0".encode("ascii").replace(b"\\0", b"\0") + data).hexdigest()

class Regulatory34AuthorizationChainV01(unittest.TestCase):
    def test_complete_pins_have_matching_blobs(self):
        docs = [load(MANIFEST), load(FREEZE), load(PREFLIGHT), load(AUTH)]
        for doc in docs:
            records = list(doc.get("bindings", {}).values())
            records += [v for k,v in doc.items() if k.startswith("bound_") and isinstance(v, dict) and {"path","git_blob_sha"} <= set(v)]
            self.assertTrue(records)
            for rec in records:
                self.assertEqual(git_blob_sha1(rec["path"]), rec["git_blob_sha"], rec["path"])
    def test_new_domain_and_binding_chain(self):
        manifest, freeze, preflight, auth = map(load, (MANIFEST, FREEZE, PREFLIGHT, AUTH))
        self.assertEqual(manifest["bindings"]["reference_questions"]["path"], "domains/zukunftscheck/rules/reference_questions_v0_2.json")
        self.assertEqual(manifest["bindings"]["meaning_layer"]["path"], "domains/zukunftscheck/rules/reference_question_meanings_v0_8.json")
        self.assertEqual(manifest["bindings"]["system_prompt"]["path"], "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_9_regulatory_3_4_candidate.txt")
        self.assertEqual(manifest["bindings"]["runner_candidate"]["path"], "scripts/zs_ki_b_sem_ai_assisted_development_live_runner_candidate_v0_2.py")
        self.assertEqual(manifest["bindings"]["runtime_binding_candidate"]["path"], P + "runtime_binding_candidate_v0_2.json")
        self.assertEqual(freeze["bindings"]["manifest_candidate"]["path"], MANIFEST)
        self.assertEqual(preflight["bound_runtime_binding_candidate"]["path"], P + "runtime_binding_candidate_v0_2.json")
        self.assertEqual(preflight["bound_prep_freeze_candidate"]["path"], FREEZE)
        self.assertEqual(auth["bound_preflight_authorization_prep"]["path"], PREFLIGHT)
        self.assertEqual(auth["bound_prep_freeze_candidate"]["path"], FREEZE)
        self.assertEqual(auth["bound_live_runner_candidate"]["path"], "scripts/zs_ki_b_sem_ai_assisted_development_live_runner_candidate_v0_2.py")
        self.assertEqual(manifest["ordered_case_ids_sha256"], freeze["ordered_case_ids_sha256"])
        self.assertEqual(manifest["expected_case_count"], 24)
    def test_fail_closed_and_no_synthetic_qualification_claim(self):
        for p in (MANIFEST, FREEZE, PREFLIGHT, AUTH, P+"runtime_binding_candidate_v0_2.json"):
            doc=load(p)
            self.assertEqual(doc["hard_stop"], HARD_STOP)
            for key in FALSE_FLAGS:
                self.assertIs(doc[key], False, (p,key))
            self.assertNotEqual(doc.get("status"), "PASS_FROZEN")
        self.assertFalse(load(AUTH)["preflight_requirement"]["preflight_result_bound"])
        self.assertEqual(load(MANIFEST)["h5_status"], "SEPARATE_NOT_AUTHORIZED")
    def test_historical_sources_still_present(self):
        for p in (P+"manifest_candidate_v0_1.json",
                  P+"prep_freeze_binding_v0_1.json",
                  P+"preflight_authorization_prep_candidate_v0_1.json",
                  P+"authorization_prep_candidate_v0_4.json"):
            self.assertTrue((ROOT/p).is_file(),p)

if __name__ == "__main__":
    unittest.main()
