from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/loop/SKILL.md"


class LoopSkillTests(unittest.TestCase):
    def test_requires_host_capability_and_bounded_fallback(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("capability", text)
        self.assertIn("stop", text.lower())
        self.assertIn("must not start", text.lower())
        self.assertNotIn("while true; do", text)
