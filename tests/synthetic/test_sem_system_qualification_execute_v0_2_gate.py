from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "zs_ki_b_sem_system_qualification_execute_v0_2.py"
EXPECTED_COMMIT = "e68dbf656dc47138dfda9f4f6297c28a44edda97"


class SemanticSystemQualificationExecuteV02GateTests(unittest.TestCase):
    def test_runner_is_bound_to_corrected_commit(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        values = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "EXPECTED_COMMIT"
        }
        self.assertEqual(values["EXPECTED_COMMIT"], EXPECTED_COMMIT)

    def test_runner_requires_explicit_authorize_execution_flag(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--authorize-execution", action="store_true"', text)
        self.assertIn('if not args.authorize_execution:', text)

    def test_runner_uses_distinct_v0_2_entrypoint(self) -> None:
        self.assertTrue(SCRIPT.name.endswith("execute_v0_2.py"))


if __name__ == "__main__":
    unittest.main()
