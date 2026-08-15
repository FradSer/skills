from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/swiftui/SKILL.md"
README = ROOT / "README.md"
README_ZH_CN = ROOT / "README.zh-CN.md"
SHARED_SKILLS = Path.home() / ".agents/skills"
PI_SKILLS = Path.home() / ".pi/agent/skills"
CLAUDE_SKILLS = Path.home() / ".claude/skills"


class SwiftUISkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_prioritizes_macos_and_ios_26_and_native_glass(self) -> None:
        self.assertIn("macOS 26", self.text)
        self.assertIn("iOS 26", self.text)
        self.assertIn("glassEffect", self.text)
        self.assertIn("GlassEffectContainer", self.text)

    def test_reserves_glass_for_the_functional_layer(self) -> None:
        self.assertIn("functional layer", self.text)
        self.assertIn("content layer", self.text)
        self.assertIn("references/liquid-glass.md", self.text)

    def test_routes_general_review_to_authoritative_reference(self) -> None:
        self.assertIn("references/twostraws.md", self.text)
        self.assertNotIn("references/review.md", self.text)
        for reference in ("accessibility", "performance", "data", "navigation", "Swift 6.2"):
            self.assertIn(reference, self.text)

    def test_bilingual_readmes_link_to_the_skill(self) -> None:
        for readme in (README, README_ZH_CN):
            text = readme.read_text(encoding="utf-8")
            self.assertIn("[swiftui](skills/swiftui/)", text)
            self.assertNotIn("skills/swiftui-liquid-glass/", text)

    def test_availability_example_keeps_the_control_semantic(self) -> None:
        reference = (ROOT / "skills/swiftui/references/liquid-glass.md").read_text(encoding="utf-8")
        example = reference.split("private var filterControl", 1)[1].split("private var filterLabel", 1)[0]
        self.assertIn('Button("Show filters", systemImage: "line.3.horizontal.decrease.circle")', example)
        self.assertIn("showFilters = true", example)

    def test_background_extension_is_documented_and_no_fake_modifier(self) -> None:
        reference = (ROOT / "skills/swiftui/references/liquid-glass.md").read_text(encoding="utf-8")
        self.assertIn("backgroundExtensionEffect()", reference)
        self.assertIn("Landmarks: Building an app with Liquid Glass", reference)
        self.assertNotIn(".scrollExtensionMode(", reference)

    def test_installed_runtimes_link_to_the_repository_skill(self) -> None:
        expected = (ROOT / "skills/swiftui").resolve()
        for runtime_skills in (SHARED_SKILLS, PI_SKILLS, CLAUDE_SKILLS):
            link = runtime_skills / "swiftui"
            self.assertTrue(link.is_symlink(), f"{link} must be a symbolic link")
            self.assertEqual(link.resolve(), expected)

    def test_topic_references_are_vendored_and_routed(self) -> None:
        references = ROOT / "skills/swiftui/references"
        expected = [
            "state-management.md",
            "view-structure.md",
            "performance-patterns.md",
            "list-patterns.md",
            "layout-best-practices.md",
            "sheet-navigation-patterns.md",
            "scroll-patterns.md",
            "focus-patterns.md",
            "animation-basics.md",
            "animation-transitions.md",
            "animation-advanced.md",
            "accessibility-patterns.md",
            "charts.md",
            "charts-accessibility.md",
            "image-optimization.md",
            "text-patterns.md",
            "localization.md",
            "macos-scenes.md",
            "macos-window-styling.md",
            "macos-views.md",
            "latest-apis.md",
            "soft-deprecation.md",
            "previews.md",
            "trace-recording.md",
            "trace-analysis.md",
            "twostraws.md",
        ]
        for reference in expected:
            path = references / reference
            self.assertTrue(path.is_file(), f"{path} must exist")
            self.assertIn(f"references/{reference}", self.text)

    def test_trace_scripts_are_vendored(self) -> None:
        scripts = ROOT / "skills/swiftui/scripts"
        for script in ("analyze_trace.py", "record_trace.py", "instruments_parser"):
            self.assertTrue((scripts / script).exists(), f"{scripts / script} must exist")
        self.assertIn("SKILL_DIR", self.text)
        self.assertIn("https://github.com/AvdLee/SwiftUI-Agent-Skill", self.text)

    def test_correctness_checklist_and_api_freshness_rules(self) -> None:
        self.assertIn("## Correctness checklist", self.text)
        for rule in (
            "@State` properties are `private`",
            "ForEach` uses stable identity",
            ".animation(_:value:)` always includes the `value` parameter",
            "references/latest-apis.md",
        ):
            self.assertIn(rule, self.text)
        self.assertIn("at the start of every task", self.text)


if __name__ == "__main__":
    unittest.main()
