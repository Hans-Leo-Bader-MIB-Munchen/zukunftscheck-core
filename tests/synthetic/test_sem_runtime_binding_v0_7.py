from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_V07 = ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_7.py"
RUNNER_V06 = ROOT / "scripts/zs_ki_b_sem_qualifikation_runner_v0_6.py"
PROMPT_V05 = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_5.txt"
PROMPT_V04 = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_4.txt"
MEANINGS_V07 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_7.json"
MEANINGS_V02 = ROOT / "domains/zukunftscheck/rules/reference_question_meanings_v0_2.json"


class SemRuntimeBindingV07Tests(unittest.TestCase):
    def test_b01_additive_historical_v02_path_remains_untouched_and_explicit(self) -> None:
        self.assertTrue(RUNNER_V06.exists())
        self.assertTrue(PROMPT_V04.exists())
        self.assertTrue(MEANINGS_V02.exists())
        self.assertIn("reference_question_meanings_v0_2.json", RUNNER_V06.read_text(encoding="utf-8"))
        self.assertIn("reference_question_meanings_v0_2.json", PROMPT_V04.read_text(encoding="utf-8"))

    def test_b02_new_prompt_explicitly_binds_v07_without_qualification_claim(self) -> None:
        text = PROMPT_V05.read_text(encoding="utf-8")
        self.assertIn("reference_question_meanings_v0_7.json", text)
        self.assertIn("67 von 67", text)
        self.assertIn("ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2", text)
        self.assertIn("keine Modellqualifikation", text)
        self.assertIn("keine Benchmarkfreigabe", text)
        self.assertIn("keine Generalisierungsfreigabe", text)
        self.assertIn("keine Produktivfreigabe", text)

    def test_b03_runtime_binding_validator_accepts_exact_67_of_67_bundle(self) -> None:
        import scripts.zs_ki_b_sem_qualifikation_runner_v0_7 as runner

        binding = runner.validate_runtime_binding()
        self.assertEqual(binding["binding_version"], "ZS-DEV-KI-B-SEM-RUNTIME-BINDING-V0-7-2026-001_v0.1")
        self.assertEqual(binding["reference_question_count"], 67)
        self.assertEqual(binding["meaning_question_count"], 67)
        self.assertEqual(binding["coverage"], "67/67")

    def test_b04_message_payload_contains_the_complete_v07_meaning_layer(self) -> None:
        import scripts.zs_ki_b_sem_qualifikation_runner_v0_7 as runner

        case = runner.load(runner.CASE_PATHS[0])
        prompt_text = PROMPT_V05.read_text(encoding="utf-8")
        messages = runner.build_messages(case, prompt_text)
        payload = json.loads(messages[1]["content"])
        meanings = payload["reference_question_meanings"]
        self.assertEqual(meanings["schema_version"], "v0.7")
        self.assertEqual(len(meanings["meanings"]), 67)
        self.assertEqual(
            {row["question_id"] for row in meanings["meanings"]},
            {row["question_id"] for row in json.loads((ROOT / "domains/zukunftscheck/rules/reference_questions_v0_1.json").read_text(encoding="utf-8"))["questions"]},
        )

    def test_b05_standalone_dry_run_is_model_free_and_reports_binding_manifest(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER_V07), "--model", "NOT_EXECUTED_MODEL_NAME"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        manifest = payload["manifest"]
        self.assertEqual(payload["mode"], "DRY_RUN_SEM_RUNTIME_BINDING_V0_7")
        self.assertEqual(manifest["runner_version"], "v0.7")
        self.assertEqual(manifest["prompt_version"], "zs_ki_b_sem_qualifikation_system_v0_5")
        self.assertEqual(manifest["contract_version"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")
        self.assertEqual(manifest["binding_version"], "ZS-DEV-KI-B-SEM-RUNTIME-BINDING-V0-7-2026-001_v0.1")
        self.assertEqual(manifest["meaning_layer_schema_version"], "v0.7")
        self.assertEqual(manifest["meaning_layer_reference_question_count"], 67)
        self.assertEqual(manifest["meaning_layer_entry_count"], 67)
        self.assertEqual(manifest["meaning_layer_coverage"], "67/67")
        self.assertTrue(manifest["meaning_layer_full_reference_coverage"])
        self.assertFalse(manifest["meaning_layer_model_qualified"])
        self.assertFalse(manifest["model_execution_enabled"])
        self.assertFalse(manifest["benchmark_approved"])
        self.assertFalse(manifest["generalisation_approved"])
        self.assertFalse(manifest["real_data_approved"])
        self.assertFalse(manifest["pilot_approved"])
        self.assertFalse(manifest["production_approved"])
        self.assertFalse(manifest["phase_f_approved"])
        self.assertEqual(manifest["expected_run_count"], 0)
        self.assertEqual(manifest["observed_run_count"], 0)
        self.assertEqual(manifest["expected_model_request_count"], 0)
        self.assertEqual(manifest["observed_model_request_count"], 0)
        self.assertFalse(manifest["execution_attempted"])
        self.assertEqual(manifest["contract_schema"], "b_semantic_contract_v0_2.schema.json")
        self.assertTrue(manifest["contract_schema_sha256"])
        self.assertTrue(manifest["meaning_layer_sha256"])
        self.assertTrue(manifest["prompt_sha256"])
        self.assertTrue(manifest["runner_sha256"])

    def test_b06_execute_flag_is_blocked_before_any_model_contact(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER_V07), "--execute", "--model", "MUST_NOT_RUN"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("model execution is disabled", completed.stderr)

    def test_b07_unknown_question_id_remains_fail_closed(self) -> None:
        from core.validation.semantic_boundary_v0_2 import validate_semantic_response_v0_2

        response = {
            "contract_version": "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2",
            "source_location_id": "SL-SYN-001",
            "proposals": [{
                "proposal_id": "SP-SYN-UNKNOWN-QID",
                "source_location_id": "SL-SYN-001",
                "normalized_statement": "Synthetische Testaussage.",
                "finding_type_candidate": "DT",
                "evidence_relation_type_candidate": "DIRECT",
                "derivation_note": None,
                "assignment_candidates": [{
                    "question_id": "99.9",
                    "pf_id": "PF1",
                    "assignment_confidence": "CLEAR",
                    "human_review_required": False,
                }],
                "conflict_candidate_refs": [],
                "gap_notes": [],
                "uncertainty_notes": [],
                "human_review_required": False,
            }],
        }
        issues = validate_semantic_response_v0_2(
            response,
            allowed_source_location_ids={"SL-SYN-001"},
            target_source_location_id="SL-SYN-001",
        )
        self.assertIn("UNKNOWN_QUESTION_ID", {issue.code for issue in issues})

    def test_b08_v07_source_artifact_itself_still_declares_model_free_no-production_scope(self) -> None:
        doc = json.loads(MEANINGS_V07.read_text(encoding="utf-8"))
        scope = doc["calibration_scope"].lower()
        self.assertEqual(doc["schema_version"], "v0.7")
        self.assertEqual(len(doc["meanings"]), 67)
        self.assertIn("keine modellqualifikation", scope)
        self.assertIn("keine produktivfreigabe", scope)


if __name__ == "__main__":
    unittest.main()
