from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/architecture/ZS-DEV-KI-B-SEM-SYSTEMQUALIFIKATION-ARCHITEKTUR-2026-001_v0.1.md"


class SemSystemqualifikationArchitekturTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_s01_model_and_system_qualification_are_separate_axes(self) -> None:
        self.assertIn("MODEL_QUALIFIED", self.text)
        self.assertIn("GUARDED_SYSTEM_QUALIFIED", self.text)
        self.assertIn("MODEL_QUALIFIED = false", self.text)

    def test_s02_guard_stop_cannot_be_reclassified_as_model_pass(self) -> None:
        self.assertIn("Guard-Stop", self.text)
        self.assertIn("kein Modell-PASS", self.text)
        self.assertIn("automatische Ergänzung", self.text)

    def test_s03_system_pass_requires_prefrozen_expected_behavior(self) -> None:
        self.assertIn("vorab eingefrorene Systemqualifikations-Suite", self.text)
        self.assertIn("PASS_THROUGH", self.text)
        self.assertIn("FAIL_CLOSED_STOP", self.text)

    def test_s04_architecture_does_not_authorize_model_or_real_data_use(self) -> None:
        self.assertIn("Kein weiterer Modelllauf", self.text)
        self.assertIn("Keine Realdaten-, Pilot-, Produktiv-, Benchmark-, Generalisierungs- oder Phase-F-Freigabe", self.text)

    def test_s05_next_block_is_model_free_policy_and_frozen_suite(self) -> None:
        self.assertIn("vollständig modellfreie", self.text)
        self.assertIn("Systemqualifikations-Policy und Frozen System-Suite v0.1", self.text)


if __name__ == "__main__":
    unittest.main()
