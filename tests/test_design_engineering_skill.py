from pathlib import Path
import re
import shutil
import tempfile
import unittest

from tests.test_skill_references import reachable_files


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "design-engineering"
SKILL_MD = SKILL_DIR / "SKILL.md"
EMIL_DIR = SKILL_DIR / "references" / "emil"


class DesignEngineeringSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_text = SKILL_MD.read_text(encoding="utf-8")

    def test_emil_overviews_strip_standalone_initial_response_greetings(self) -> None:
        offenders = [
            str(path.relative_to(SKILL_DIR))
            for path in sorted(EMIL_DIR.glob("*/overview.md"))
            if "## Initial Response" in path.read_text(encoding="utf-8")
            or "Do not provide any other information until the user asks a question."
            in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_emil_references_rewrite_skill_md_and_cross_pack_names(self) -> None:
        stale_skill_md = [
            str(path.relative_to(SKILL_DIR))
            for path in sorted(EMIL_DIR.rglob("*.md"))
            if re.search(r"\bSKILL\.md\b", path.read_text(encoding="utf-8"))
        ]
        self.assertEqual([], stale_skill_md)

        animate_text = (EMIL_DIR / "animate" / "overview.md").read_text(encoding="utf-8")
        self.assertIn("references/emil/improve-animations/overview.md", animate_text)
        self.assertIn("references/emil/review-animations/overview.md", animate_text)
        self.assertIn("references/emil/find-animation-opportunities/overview.md", animate_text)
        self.assertIn("references/emil/animate-expo/overview.md", animate_text)
        self.assertIn("references/emil/pick-ui-library/overview.md", animate_text)

    def test_router_synthesizes_overlapping_workflows_and_craft_parameters(self) -> None:
        for required in (
            "references/emil/emil-design-eng/overview.md",
            "references/emil/animate/overview.md",
            "references/emil/animate-expo/overview.md",
            "references/emil/review-animations/overview.md",
            "references/emil/improve-animations/overview.md",
            "references/emil/find-animation-opportunities/overview.md",
            "references/emil/animation-vocabulary/overview.md",
            "references/emil/performance-cheatsheet.md",
            "references/emil/prototype/overview.md",
            "references/emil/break-ui/overview.md",
            "references/emil/mobile-native/overview.md",
            "references/emil/apple-design/overview.md",
            "references/emil/pick-ui-library/overview.md",
            "references/emil/ask-sonner/overview.md",
            "references/emil/write-swift/overview.md",
            "cubic-bezier(0.23, 1, 0.32, 1)",
            "__variant",
            "prefers-reduced-motion",
        ):
            self.assertIn(required, self.skill_text)

        reached = reachable_files(SKILL_DIR)
        unreachable = [
            str(path.relative_to(SKILL_DIR))
            for path in sorted((SKILL_DIR / "references").rglob("*.md"))
            if path.resolve() not in reached
        ]
        self.assertEqual([], unreachable)

    def test_interfaces_sync_builder_normalizes_emil_packs_idempotently(self) -> None:
        import importlib.util
        import sys

        sync_dir = ROOT / "tools" / "skill-sync"
        sys.path.insert(0, str(sync_dir))
        self.addCleanup(lambda: sys.path.remove(str(sync_dir)))
        spec = importlib.util.spec_from_file_location("interfaces_sync", sync_dir / "interfaces.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            emil_src = base / "emil" / "skills"
            (emil_src / "animate").mkdir(parents=True)
            (emil_src / "review-animations").mkdir(parents=True)
            (base / "emil" / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (base / "emil" / "performance-cheatsheet.md").write_text("# Perf\n", encoding="utf-8")
            (emil_src / "animate" / "SKILL.md").write_text(
                "---\nname: animate\ndescription: Build animations\n---\n\n"
                "# Building Animations\n\n"
                "## Initial Response\n\n"
                "When this skill is first invoked without a specific question, respond only with:\n\n"
                "> Greeting\n\n"
                "Do not provide any other information until the user asks a question.\n\n"
                "See `review-animations` and tokens in SKILL.md.\n",
                encoding="utf-8",
            )
            (emil_src / "review-animations" / "SKILL.md").write_text(
                "---\nname: review-animations\ndescription: Review animations\n---\n\n"
                "# Reviewing Animations\n\nBody.\n",
                encoding="utf-8",
            )
            target = base / "out"
            (target / "design-engineering" / "references").mkdir(parents=True)
            module.merge_emil(emil_src, target)

            overview = (target / "design-engineering/references/emil/animate/overview.md").read_text(encoding="utf-8")
            self.assertNotIn("## Initial Response", overview)
            self.assertNotIn("SKILL.md", overview)
            self.assertIn("references/emil/review-animations/overview.md", overview)
            self.assertIn("overview.md", overview)


if __name__ == "__main__":
    unittest.main()
