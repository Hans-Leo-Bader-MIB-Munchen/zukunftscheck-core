import copy
import unittest

from core.validation.validator import validate_bundle, validate_original_text_change


def base_bundle():
    return {
        "run_manifest": {"run_id":"RUN-SYN-001","schema_version":"v0.1","development_data_class":"SYNTHETIC_ONLY","llm_used":False},
        "documents": [{"document_id":"DOC-1","document_title":"Synthetik","document_type":"TEST","source_status":"DRAFT","project_or_case_id":"CASE-SYN","confidentiality_or_data_class":"SYNTHETIC","storage_reference":"local:test","captured_at":"2026-08-25T00:00:00+02:00","captured_by":"TEST"}],
        "source_locations": [{"source_location_id":"LOC-1","document_id":"DOC-1","original_text":"synthetischer Originaltext","extraction_method":"MANUAL","locator_quality":"EXACT","human_review_required":False,"source_version_reference":"v0"}],
        "findings": [{"finding_id":"F-1","normalized_statement":"synthetische Aussage","finding_type":"DT","human_content_confirmation":"UNREVIEWED","human_review_required":False}],
        "evidence_relations": [{"evidence_relation_id":"E-1","finding_id":"F-1","source_location_id":"LOC-1","evidence_relation_type":"DIRECT"}],
        "assignments": [{"assignment_id":"A-1","finding_id":"F-1","pf_id":"PF11","question_id":"11.2","assignment_confidence":"CLEAR","human_review_required":False}],
        "conflicts": [], "human_decisions": [], "audit_events": []
    }


class ValidatorSyntheticTests(unittest.TestCase):
    def codes(self, bundle):
        return {issue.code for issue in validate_bundle(bundle)}

    def test_T01_missing_id(self):
        b=base_bundle(); del b["documents"][0]["document_id"]; self.assertIn("MISSING_ID",self.codes(b))
    def test_T02_unknown_document(self):
        b=base_bundle(); b["source_locations"][0]["document_id"]="DOC-X"; self.assertIn("UNKNOWN_DOCUMENT_REF",self.codes(b))
    def test_T03_unknown_question(self):
        b=base_bundle(); b["assignments"][0]["question_id"]="13.1"; self.assertIn("UNKNOWN_QUESTION_ID",self.codes(b))
    def test_T04_pf_question_mismatch(self):
        b=base_bundle(); b["assignments"][0].update(question_id="4.2",pf_id="PF5"); self.assertIn("PF_QUESTION_MISMATCH",self.codes(b))
    def test_T05_invalid_source_status(self):
        b=base_bundle(); b["documents"][0]["source_status"]="E-DRAFT"; self.assertIn("INVALID_SOURCE_STATUS",self.codes(b))
    def test_T06_invalid_evidence_relation(self):
        b=base_bundle(); b["evidence_relations"][0]["evidence_relation_type"]="DRAFT"; self.assertIn("INVALID_EVIDENCE_RELATION",self.codes(b))
    def test_T07_derived_needs_note(self):
        b=base_bundle(); b["evidence_relations"][0]["evidence_relation_type"]="DERIVED"; self.assertIn("MISSING_DERIVATION_PATH",self.codes(b))
    def test_T08_unclear_locator_review(self):
        b=base_bundle(); b["source_locations"][0].update(locator_quality="UNCLEAR",human_review_required=False); self.assertIn("MISSING_REVIEW_FLAG",self.codes(b))
    def test_T09_uncertain_assignment_review(self):
        b=base_bundle(); b["assignments"][0].update(assignment_confidence="UNCERTAIN",human_review_required=False); self.assertIn("MISSING_REVIEW_FLAG",self.codes(b))
    def test_T10_human_decision_actor(self):
        b=base_bundle(); b["human_decisions"]=[{"human_decision_id":"HD-1","actor_type":"AI","decision_scope":"content","decision_value":"x","reason":"synthetic"}]; self.assertIn("NONHUMAN_APPROVAL",self.codes(b))
    def test_T11_schema_version(self):
        b=base_bundle(); b["run_manifest"]["schema_version"]="v0.2"; self.assertIn("SCHEMA_VERSION_MISMATCH",self.codes(b))
    def test_T12_real_data_blocked(self):
        b=base_bundle(); b["run_manifest"]["development_data_class"]="REAL"; self.assertIn("REAL_DATA_BLOCKED",self.codes(b))
    def test_T13_llm_blocked(self):
        b=base_bundle(); b["run_manifest"]["llm_used"]=True; self.assertIn("LLM_NOT_ALLOWED",self.codes(b))
    def test_T14_valid_assignment(self):
        self.assertEqual([], validate_bundle(base_bundle()))
    def test_T15_valid_derived(self):
        b=base_bundle(); b["evidence_relations"][0].update(evidence_relation_type="DERIVED",derivation_note="synthetische Ableitung"); self.assertEqual([], validate_bundle(b))
    def test_BV015_original_text_immutable(self):
        before=base_bundle(); after=copy.deepcopy(before); after["source_locations"][0]["original_text"]="verändert"
        self.assertEqual("PROVENANCE_OVERWRITE", validate_original_text_change(before,after)[0].code)


if __name__ == "__main__":
    unittest.main()
