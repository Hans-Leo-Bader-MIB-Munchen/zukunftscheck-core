from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


PROMPT_PATH = Path("llm/prompts/zs_ki_b_sem_qualifikation_system_v0_2.txt")
PROMPT_SHA256 = "9280e064c2504677f1e7e9e408990532046aaed087caf41a241a718a89d85b40"


class SemQualificationPromptV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PROMPT_PATH.read_text(encoding="utf-8")

    def test_01_prompt_hash_is_frozen(self) -> None:
        digest = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        self.assertEqual(digest, PROMPT_SHA256)

    def test_02_requires_semantic_and_evidential_splitting(self) -> None:
        self.assertIn("semantisch oder evidenziell unterschiedliche Aussagen", self.text)
        self.assertIn("getrennte Proposals", self.text)
        self.assertIn("nicht zu einer gemeinsamen DIRECT-Aussage verschmolzen", self.text)

    def test_03_requires_unsupported_for_unproven_conclusions(self) -> None:
        self.assertIn("übernimmt nicht automatisch den Evidenzstatus ihrer Prämisse", self.text)
        self.assertIn("getrennt als UNSUPPORTED", self.text)

    def test_04_requires_content_based_question_assignment(self) -> None:
        self.assertIn("deren Fragetext durch den konkreten Aussageinhalt tatsächlich berührt wird", self.text)
        self.assertIn("Keine assoziative Zuordnung", self.text)

    def test_05_requires_review_flags_for_uncertainty(self) -> None:
        self.assertIn('assignment_confidence="UNCERTAIN"', self.text)
        self.assertIn("AssignmentCandidate human_review_required=true", self.text)
        self.assertIn("Proposal-Ebene human_review_required=true", self.text)


if __name__ == "__main__":
    unittest.main()
