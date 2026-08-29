from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import llm.local_model.structured_output_v0_6_candidate as transport

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json"
PROMPT = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt"
TRANSPORT = ROOT / "llm/local_model/structured_output_v0_6_candidate.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class V17BoundedComponentsCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load(SCHEMA)

    def test_c01_schema_identity_is_explicitly_candidate(self) -> None:
        self.assertEqual(self.schema["$id"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate")
        self.assertEqual(
            self.schema["properties"]["contract_version"]["const"],
            "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate",
        )

    def test_c02_schema_has_exact_array_bounds(self) -> None:
        self.assertEqual(self.schema["properties"]["proposals"]["maxItems"], 8)
        props = self.schema["$defs"]["proposal"]["properties"]
        for key in ("assignment_candidates", "conflict_candidate_refs", "gap_notes", "uncertainty_notes"):
            self.assertEqual(props[key]["maxItems"], 8)

    def test_c03_schema_has_exact_text_bounds(self) -> None:
        props = self.schema["$defs"]["proposal"]["properties"]
        self.assertEqual(props["normalized_statement"]["maxLength"], 512)
        self.assertEqual(props["derivation_note"]["maxLength"], 384)
        self.assertEqual(props["gap_notes"]["items"]["maxLength"], 256)
        self.assertEqual(props["uncertainty_notes"]["items"]["maxLength"], 256)

    def test_c04_payload_builder_enforces_1024_ceiling(self) -> None:
        payload = transport.build_structured_payload(
            model="synthetic-model-id",
            messages=[{"role": "system", "content": "x"}],
        )
        self.assertEqual(payload["max_completion_tokens"], 1024)
        self.assertFalse(payload["stream"])
        with self.assertRaises(ValueError):
            transport.build_structured_payload(
                model="synthetic-model-id",
                messages=[{"role": "system", "content": "x"}],
                max_completion_tokens=1025,
            )

    def test_c05_payload_uses_strict_bounded_candidate_schema(self) -> None:
        response_format = transport.build_response_format()
        self.assertEqual(response_format["type"], "json_schema")
        self.assertTrue(response_format["json_schema"]["strict"])
        bounded = response_format["json_schema"]["schema"]
        self.assertEqual(bounded["properties"]["proposals"]["maxItems"], 8)

    def test_c06_prompt_binds_candidate_contract_and_concision(self) -> None:
        text = PROMPT.read_text(encoding="utf-8")
        self.assertIn("ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate", text)
        self.assertIn("so knapp wie möglich und ohne Wiederholungen", text)

    def test_c07_candidate_transport_has_no_contact_or_execution_imports(self) -> None:
        tree = ast.parse(TRANSPORT.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden_roots = {"urllib", "requests", "httpx", "socket", "subprocess"}
        self.assertFalse({name.split(".")[0] for name in imported} & forbidden_roots)
        source = TRANSPORT.read_text(encoding="utf-8")
        self.assertNotIn("chat/completions", source)
        self.assertNotIn("preflight_loaded_model", source)

    def test_c08_candidate_does_not_mutate_active_v02_contract(self) -> None:
        active = load(ROOT / "domains/zukunftscheck/schema/b_semantic_contract_v0_2.schema.json")
        self.assertEqual(active["$id"], "ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.2")
        self.assertNotIn("maxItems", active["properties"]["proposals"])


if __name__ == "__main__":
    unittest.main()
