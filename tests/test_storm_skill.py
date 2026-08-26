from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/storm"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"
README_MD = ROOT / "README.md"
README_ZH_CN = ROOT / "README.zh-CN.md"

PHASE_REFERENCES = ("research", "outline", "write", "polish")
PROPRIETARY_TOOLS = ("ToolSearch", "AskUserQuestion", "WebSearch", "WebFetch")


def skill_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in SKILL_DIR.rglob("*.md")
    )


class StormSkillStructureTests(unittest.TestCase):
    def test_skill_is_a_single_self_contained_directory(self) -> None:
        self.assertTrue(SKILL_MD.is_file())
        for name in ("engine", *PHASE_REFERENCES):
            self.assertTrue((REFERENCES / f"{name}.md").is_file(), name)
        self.assertFalse((SKILL_DIR / "agents").exists())
        self.assertFalse((SKILL_DIR / ".claude-plugin").exists())

    def test_every_phase_reference_links_back_to_the_engine(self) -> None:
        for name in PHASE_REFERENCES:
            text = (REFERENCES / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn("engine.md", text)

    def test_skill_entry_point_links_every_phase_and_the_engine(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        for name in ("engine", *PHASE_REFERENCES):
            self.assertIn(f"references/{name}.md", text)


class StormRuntimeNeutralityTests(unittest.TestCase):
    def test_names_no_proprietary_runtime_tool(self) -> None:
        for tool in PROPRIETARY_TOOLS:
            self.assertNotIn(tool, skill_text())

    def test_parallelism_has_a_sequential_fallback(self) -> None:
        text = skill_text()
        for marker in ("subagents if the runtime supports spawning workers",
                       "sequentially"):
            self.assertIn(marker, text)

    def test_retrieval_probes_available_tooling_before_falling_back(self) -> None:
        text = REFERENCES.joinpath("engine.md").read_text(encoding="utf-8")
        self.assertIn("Probe the runtime's tool set", text)
        self.assertIn("fall back to built-in web search", text)

    def test_local_documents_can_ground_the_run(self) -> None:
        self.assertIn("--docs", skill_text())
        self.assertIn("--docs-only", skill_text())


class StormPipelineContractTests(unittest.TestCase):
    def test_completed_phases_are_skipped_without_force(self) -> None:
        text = skill_text()
        self.assertIn("--force", text)
        self.assertIn("skip", text)
        self.assertIn("run-config.json", text)

    def test_write_never_runs_without_research_artifacts(self) -> None:
        write_text = REFERENCES.joinpath("write.md").read_text(encoding="utf-8")
        self.assertIn("research/sources.json", write_text)
        self.assertIn("stop and direct the user", write_text)
        for name, prerequisite in (("outline", "sources.json"),
                                   ("write", "outline.md"),
                                   ("polish", "article.md")):
            text = (REFERENCES / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn(prerequisite, text)
            self.assertIn("stop and direct the user", text)

    def test_citations_resolve_to_research_sources_only(self) -> None:
        engine = REFERENCES.joinpath("engine.md").read_text(encoding="utf-8")
        lowered = engine.lower()
        self.assertIn("never invent citations", lowered)
        self.assertIn("references = exactly the set of", lowered)
        polish = REFERENCES.joinpath("polish.md").read_text(encoding="utf-8")
        self.assertIn("References mirrors the body exactly", polish)

    def test_snippets_are_citation_stripped_before_reuse(self) -> None:
        engine = REFERENCES.joinpath("engine.md").read_text(encoding="utf-8")
        self.assertRegex(engine, r"strip_citations\(text\)")
        self.assertIn("removing every `[n]` and `[n][m]` pattern", engine)

    def test_temporary_output_dir_keeps_the_slug_component(self) -> None:
        engine = REFERENCES.joinpath("engine.md").read_text(encoding="utf-8")
        self.assertIn("storm-<slug>", engine)

    def test_conversation_units_return_json_arrays_only(self) -> None:
        research = REFERENCES.joinpath("research.md").read_text(encoding="utf-8")
        self.assertIn("Return ONLY a JSON array", research)
        self.assertIn("no prose", research)

    def test_phase_references_declare_their_arguments(self) -> None:
        expected = {"research": ["--max-perspective", "--max-turns",
                                 "--retriever", "--force"],
                    "outline": ["--force"],
                    "write": ["--retrieve-top-k", "--force"],
                    "polish": ["--remove-duplicate", "--force"]}
        for name, arguments in expected.items():
            text = (REFERENCES / f"{name}.md").read_text(encoding="utf-8")
            for argument in arguments:
                self.assertIn(argument, text, f"{name}: {argument}")

    def test_model_routing_splits_cost_from_quality(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Model routing", text)
        self.assertIn("strongest available model", text)


class StormDocumentationTests(unittest.TestCase):
    def test_bilingual_readmes_link_to_the_skill(self) -> None:
        for readme in (README_MD, README_ZH_CN):
            text = readme.read_text(encoding="utf-8")
            self.assertIn("[storm](skills/storm/)", text)


if __name__ == "__main__":
    unittest.main()
