from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPT_V05 = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_5.txt"
PROMPT_V06 = ROOT / "llm" / "prompts" / "zs_ki_b_sem_qualifikation_system_v0_6.txt"


class SemQualificationPromptV06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v05 = PROMPT_V05.read_text(encoding="utf-8")
        cls.v06 = PROMPT_V06.read_text(encoding="utf-8")

    def test_p01_v06_preserves_v05_guardrails(self) -> None:
        required_fragments = [
            "Keine HumanDecision.",
            "Keine bestätigte Konfliktfeststellung.",
            "Keine neuen finding types, question_ids, PF-Zuordnungen, Statusdimensionen oder Regeln.",
            "Keine assoziative Zuordnung allein aufgrund einzelner Begriffe oder allgemeiner Nähe.",
            "Verwende keine Tools, kein Web, kein MCP, keine externen oder Remote-/Cloud-Quellen und keine Realdaten.",
            "Gib nur den vertragskonformen strukturierten Output zurück.",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.v05)
            self.assertIn(fragment, self.v06)

    def test_p02_v06_explicitly_requires_exhaustive_supported_multiassignment_check(self) -> None:
        self.assertIn(
            "Eine einzelne konkrete Aussage kann gleichzeitig mehrere eigenständig einschlägige Referenzfragen berühren",
            self.v06,
        )
        self.assertIn("Prüfe deshalb für jedes Proposal alle Referenzfragen dieses Aussageinhalts einzeln", self.v06)
        self.assertIn("Beschränke dich nicht auf nur eine vermeintlich wichtigste oder spezifischste Referenzfrage", self.v06)

    def test_p03_v06_keeps_anti_overgeneration_constraint_adjacent_to_multiassignment_rule(self) -> None:
        marker = "Eine einzelne konkrete Aussage kann gleichzeitig mehrere eigenständig einschlägige Referenzfragen berühren"
        start = self.v06.index(marker)
        window = self.v06[start : start + 1800]
        self.assertIn("keine assoziative Overgeneration", window)
        self.assertIn("Jede zusätzliche Zuordnung muss durch Fragetext und Meaning-Layer-Abgrenzung eigenständig getragen sein", window)

    def test_p04_v06_names_scope_and_dependency_markers_without_hardcoding_question_ids(self) -> None:
        marker = "Besonders bei sprachlichen Begrenzungs-, Einbeziehungs-, Ausschluss-, Abhängigkeits-, Zuständigkeits- oder Bearbeitungsumfangsmarkern"
        self.assertIn(marker, self.v06)
        for token in ["ausschließlich", "einschließlich", "ausgenommen", "erst nachdem", "zuständig", "bearbeitet", "nicht bearbeitet"]:
            self.assertIn(f"„{token}“", self.v06)
        self.assertIn("Diese Marker erzwingen keine bestimmte question_id", self.v06)

    def test_p05_v06_does_not_embed_frozen_gold_answers(self) -> None:
        forbidden_answer_fragments = [
            "2.1/PF2",
            "2.2/PF2",
            "8.1/PF8",
            "8.3/PF8",
            "9.1/PF9",
            "9.2/PF9",
            "9.3/PF9",
            "12.1/PF12",
            "12.2/PF12",
            "12.3/PF12",
        ]
        for fragment in forbidden_answer_fragments:
            self.assertNotIn(fragment, self.v06)

    def test_p06_v05_remains_unchanged_and_v06_is_separately_versioned(self) -> None:
        self.assertNotEqual(self.v05, self.v06)
        self.assertTrue(PROMPT_V05.exists())
        self.assertTrue(PROMPT_V06.exists())


if __name__ == "__main__":
    unittest.main()
