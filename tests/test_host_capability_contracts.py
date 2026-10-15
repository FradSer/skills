"""Every skill may rely on a host capability only after discovery, with a stated fallback.

Regression origin: `review-pr` instructed the agent to poll with `monitor_start`. No host
exposed that tool, so the watch dead-ended after one poll, while the suite stayed green on a
string match in the document. The defect class is wider than one tool name:

- a named host tool the runtime does not have;
- a worker-spawn step with no sequential fallback;
- a host capability (continuation, monitor, subagent, hook, scheduler) with no rule for the
  host that lacks it.

The authoritative policy lives in `.agents/skills/skill-creator/SKILL.md` step 6. This module
enforces it across the collection.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

from tools.skill_eval.fixtures import UNVERIFIED_HOST_TOOLS


ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (ROOT / "skills", ROOT / ".agents" / "skills")

# pi built-in tools, verified from the live tool inventory on 2026-10-15 (67 tools, minus the
# MCP servers). A skill may also use a tool that another host provides, but then it must state
# what it does when that host lacks the tool.
PI_BUILTIN_TOOLS = frozenset(
    {
        "read", "bash", "edit", "write", "agent_start", "agent_input", "agent_stop",
        "agent_list", "create_task", "get_task", "list_tasks", "update_task", "web_search",
        "source_check", "fetch_content", "get_search_content", "get_goal", "create_goal",
        "impeccable_load", "matt_pocock_workflow", "enter_worktree",
    }
)

# Harness-specific tool names that were tried in this collection and verified absent. The eval
# grader reads the same mapping, so the source contract and the runtime contract stay aligned.

TOOL_SHAPED = re.compile(r"`([a-z][a-z0-9_]*_(?:start|stop|send|input|list|watch|monitor|spawn|tool))`")
WORKER_SPAWN = re.compile(
    r"\b(spawn|fan out|dispatch|launch|start|run)\w*\b[^.\n]{0,60}\b(subagent|independent agent|"
    r"review-triage agent|executor subagent)",
    re.IGNORECASE,
)
FALLBACK = re.compile(
    r"if the runtime|if the host|when the host|when available|runtime supports|cannot spawn|"
    r"exposes no|could not be established|if none exists|without hooks|otherwise|fall back|"
    r"no supported mechanism|shared the main context",
    re.IGNORECASE,
)
SCANNED_SUFFIXES = frozenset({".md", ".sh", ".py", ".yaml", ".js", ".ts"})

# (document, required discovery markers, required fallback markers): every marker must appear
# once whitespace is normalized.
HOST_CAPABILITY_DEPENDENCIES = (
    ("skills/review-pr/SKILL.md", ("Discover the host's continuation facility",),
     ("ongoing monitoring could not be established", "the host exposes no facility")),
    ("skills/review-pr/references/runbook.md", ("Discover how this host",),
     ("ongoing monitoring could not be established",)),
    ("skills/review-pr/references/review-loop.md", ("Discover how this host",),
     ("ongoing monitoring could not be established", "shared the main context")),
    ("skills/create-pr/SKILL.md", (), ("host continuation facility",)),
    ("skills/create-pr/references/review-pr-handoff.md", (), ("host continuation facility",)),
    ("skills/create-pr/references/runbook.md", (), ("ongoing monitoring could not be established",)),
    ("skills/review-pr/references/closeout.md", (), ("shared the main context", "without hooks")),
    ("skills/loop/SKILL.md", ("Discover the host's scheduling capabilities",),
     ("report that the host cannot run this loop",)),
    ("skills/design-engineering/references/emil/improve-animations/overview.md", (),
     ("cannot spawn",)),
    ("skills/storm/references/research.md", (),
     ("if the runtime supports spawning workers", "otherwise execute sequentially")),
)


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def local_script_functions() -> set[str]:
    """Names the collection itself defines, so they are not host tools."""
    names: set[str] = set()
    for root in SCAN_ROOTS:
        for path in root.glob("*/scripts/**/*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            names.update(re.findall(r"(?:function\s+)?\b([a-z][a-z0-9_]*)\(\)\s*\{", text))
    return names


def scanned_documents(suffixes: frozenset[str]) -> list[Path]:
    documents: list[Path] = []
    for root in SCAN_ROOTS:
        documents.extend(
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.suffix.lower() in suffixes
        )
    return documents


def paragraphs(text: str) -> list[str]:
    return re.split(r"\n\s*\n", text)


def scan_text(text: str, local_functions: set[str]) -> list[str]:
    """Return the defect-class findings for one document."""
    findings: list[str] = []
    for name in sorted(set(TOOL_SHAPED.findall(text))):
        if name in PI_BUILTIN_TOOLS or name in local_functions:
            continue
        holders = [block for block in paragraphs(text) if f"`{name}`" in block]
        if any(FALLBACK.search(block) for block in holders):
            continue
        findings.append(f"unverified host tool `{name}`")
    for block in paragraphs(text):
        if WORKER_SPAWN.search(block) and not FALLBACK.search(block):
            findings.append(f"worker spawn without fallback: {' '.join(block.split())[:80]}")
    return findings


class HostCapabilityContractTests(unittest.TestCase):
    def test_the_scanner_detects_the_original_defect(self) -> None:
        # A guard that cannot fail proves nothing. This pins the detector to the real defect.
        self.assertEqual(
            ["unverified host tool `monitor_start`"],
            scan_text("In Pi, start every one-shot poll with `monitor_start`.", set()),
        )
        self.assertEqual(
            [],
            scan_text(
                "In Pi, start every one-shot poll with `monitor_start`. "
                "If the host exposes no such facility, report it and stop.",
                set(),
            ),
        )
        self.assertTrue(scan_text("Fan out subagents, one per category.", set()))
        self.assertEqual(
            [],
            scan_text(
                "Fan out subagents, one per category. If the runtime cannot spawn workers, "
                "audit the categories sequentially in-context.",
                set(),
            ),
        )

    def test_no_skill_names_a_tool_that_no_host_exposes(self) -> None:
        documents = scanned_documents(SCANNED_SUFFIXES)
        self.assertGreater(len(documents), 50, "the collection scan lost its input")
        for path in documents:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name, evidence in UNVERIFIED_HOST_TOOLS.items():
                self.assertNotIn(
                    f"`{name}`", text, f"{path.relative_to(ROOT)}: {name} is {evidence}"
                )

    def test_no_document_requires_a_worker_spawn_without_a_fallback(self) -> None:
        local = local_script_functions()
        for path in scanned_documents(frozenset({".md"})):
            findings = [item for item in scan_text(path.read_text(encoding="utf-8"), local)
                        if item.startswith("worker spawn")]
            self.assertEqual([], findings, path.relative_to(ROOT))

    def test_no_document_names_an_unverified_host_tool(self) -> None:
        local = local_script_functions()
        for path in scanned_documents(SCANNED_SUFFIXES):
            findings = [item for item in scan_text(path.read_text(encoding="utf-8", errors="ignore"), local)
                        if item.startswith("unverified host tool")]
            self.assertEqual([], findings, path.relative_to(ROOT))

    def test_documented_host_capability_dependencies_state_a_fallback(self) -> None:
        for relative, discovery, fallback in HOST_CAPABILITY_DEPENDENCIES:
            document = normalized(ROOT / relative)
            for marker in discovery:
                self.assertIn(marker, document, f"{relative}: missing discovery {marker!r}")
            for marker in fallback:
                self.assertIn(marker, document, f"{relative}: missing fallback {marker!r}")


if __name__ == "__main__":
    unittest.main()