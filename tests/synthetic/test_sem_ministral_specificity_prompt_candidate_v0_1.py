from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt"
CANDIDATE = ROOT / "llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt"
GOLD = ROOT / "tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json"
POLICY = ROOT / "tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json"

BASELINE_SHA256 = "a8e51fecbadbd674a8c36f762b234c2e6d157e84d53e0666204d0a998291eecc"
CANDIDATE_SHA256 = "2d56a8ada5d66f196d0f4a18f828de4d82e41654fb9a49d432ab16e87fdb54e8"
GOLD_GIT_BLOB = "704adbd930c042b132a34bb9ddc95b4531f336b2"
POLICY_GIT_BLOB = "9bc06b2648b05f9bb1d464e019e23f8afd82570b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class MinistralSpecificityPromptCandidateV01Tests(unittest.TestCase):
    def test_baseline_prompt_is_unchanged(self) -> None:
        self.assertEqual(sha256(BASELINE), BASELINE_SHA256)

    def test_candidate_prompt_is_exactly_bound(self) -> None:
        self.assertEqual(sha256(CANDIDATE), CANDIDATE_SHA256)

    def test_candidate_contains_all_specificity_guards(self) -> None:
        text = CANDIDATE.read_text(encoding="utf-8")
        for marker in ("R-SP1", "R-SP2", "R-SP3", "Verwende keine First-Match-Logik"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertIn("Mehrere assignment_candidates bleiben erforderlich", text)
        self.assertIn("eigenständig im Text enthalten", text)

    def test_candidate_preserves_existing_time_and_review_guards(self) -> None:
        text = CANDIDATE.read_text(encoding="utf-8")
        self.assertIn("Unterschiedliche Werte oder Zustände sind nicht allein deshalb ein Konfliktkandidat", text)
        self.assertIn('Wenn assignment_confidence="UNCERTAIN" gesetzt wird', text)
        self.assertIn("human_review_required=true", text)

    def test_candidate_preserves_offline_and_authority_limits(self) -> None:
        text = CANDIDATE.read_text(encoding="utf-8")
        self.assertIn("Verwende keine Tools, kein Web, kein MCP", text)
        self.assertIn("Keine HumanDecision", text)
        self.assertIn("Gib nur den vertragskonformen strukturierten Output zurück", text)

    def test_frozen_gold_and_policy_remain_exact(self) -> None:
        self.assertEqual(git_blob_sha1(GOLD), GOLD_GIT_BLOB)
        self.assertEqual(git_blob_sha1(POLICY), POLICY_GIT_BLOB)


if __name__ == "__main__":
    unittest.main()
