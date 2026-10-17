"""The marketing router mirrors 50 upstream workflows behind one discoverable skill.

Regression origin: a mirrored tree that keeps upstream discovery metadata exposes
every upstream skill again, and a routed document that no link reaches is dead
weight. These tests hold the single-entry contract and the mirror transforms.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import sys
import tempfile
import unittest

import yaml

from tests.test_skill_references import reachable_files


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "marketing"
SKILL_MD = SKILL_DIR / "SKILL.md"
ROUTES = SKILL_DIR / "routes.yml"
LOCAL_ENTRIES = {"SKILL.md", "README.md", "SYNC.md", "agents", "scripts"}

BUILDER_DIR = ROOT / "tools" / "skill-sync"


def load_builder():
    sys.path.insert(0, str(BUILDER_DIR))
    spec = importlib.util.spec_from_file_location("marketing_sync", BUILDER_DIR / "marketing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_upstream(upstream: Path, cro: str | None = None) -> None:
    write(upstream / "LICENSE", "MIT License\n\nCopyright (c) 2025 Corey Haines\n")
    write(
        upstream / "skills" / "copywriting" / "SKILL.md",
        '---\nname: copywriting\ndescription: "Write marketing copy."\n---\n\n# Copywriting\n\nBody.\n',
    )
    write(
        upstream / "skills" / "cro" / "SKILL.md",
        cro
        if cro is not None
        else (
            "---\n"
            "name: cro\n"
            'description: "When the user wants to increase conversions. Also use when the '
            "user says 'CRO'.\"\n"
            "metadata:\n  version: 2.0.3\n"
            "---\n\n"
            "# CRO\n\n"
            "See `references/form.md` and [copywriting](../copywriting/SKILL.md).\n\n"
            "Read [Terms](link).\n"
        ),
    )
    write(upstream / "skills" / "cro" / "references" / "form.md", "# Form\n")
    write(upstream / "skills" / "cro" / "evals" / "evals.json", "{}\n")
    write(upstream / "skills" / "cro" / "agents" / "openai.yaml", "policy: {}\n")


def tree_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class MarketingBuilderTests(unittest.TestCase):
    """The builder is deterministic, validates upstream, and rewrites routing hops."""

    def setUp(self) -> None:
        self.builder = load_builder()
        self.addCleanup(lambda: sys.path.remove(str(BUILDER_DIR)))
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def build(self) -> Path:
        upstream = self.base / "upstream"
        build_upstream(upstream)
        self.builder.build(upstream, self.base / "out", commit="a" * 40)
        return self.base / "out" / "marketing"

    def test_each_workflow_becomes_one_document_without_discovery_metadata(self) -> None:
        router = self.build()
        entry = router / "cro" / "cro.md"
        self.assertTrue(entry.is_file())
        self.assertEqual([], list(router.rglob("SKILL.md")))
        self.assertFalse(entry.read_text(encoding="utf-8").startswith("---"))

    def test_upstream_eval_and_agents_metadata_is_not_copied(self) -> None:
        router = self.build()
        self.assertFalse((router / "cro" / "evals").exists())
        self.assertFalse((router / "cro" / "agents").exists())

    def test_cross_skill_and_in_pack_links_are_rewritten(self) -> None:
        entry = (self.build() / "cro" / "cro.md").read_text(encoding="utf-8")
        self.assertIn("[copywriting](../copywriting/copywriting.md)", entry)
        self.assertIn("[`references/form.md`](references/form.md)", entry)

    def test_unresolvable_example_links_move_to_the_placeholder_origin(self) -> None:
        entry = (self.build() / "cro" / "cro.md").read_text(encoding="utf-8")
        self.assertIn("[Terms](https://example.com/link)", entry)

    def test_routes_manifest_carries_one_condensed_row_per_workflow(self) -> None:
        records = yaml.safe_load((self.build() / "routes.yml").read_text(encoding="utf-8"))["routes"]
        self.assertEqual(["copywriting", "cro"], sorted(row["name"] for row in records))
        cro = next(row for row in records if row["name"] == "cro")
        self.assertEqual("cro/cro.md", cro["entry"])
        self.assertEqual("Increase conversions.", cro["description"])

    def test_upstream_license_is_retained_beside_the_router(self) -> None:
        self.assertIn("Corey Haines", (self.build() / "coreyhaines31-LICENSE.txt").read_text(encoding="utf-8"))

    def test_rebuilding_an_existing_target_is_idempotent(self) -> None:
        router = self.build()
        first = tree_digest(router)
        self.builder.build(self.base / "upstream", self.base / "out", commit="a" * 40)
        self.assertEqual(first, tree_digest(router))

    def test_invalid_upstream_identity_is_rejected(self) -> None:
        upstream = self.base / "upstream"
        build_upstream(upstream, cro='---\nname: conversion\ndescription: "x"\n---\n\n# CRO\n')
        with self.assertRaises(ValueError):
            self.builder.build(upstream, self.base / "out")

    def test_missing_upstream_description_is_rejected(self) -> None:
        upstream = self.base / "upstream"
        build_upstream(upstream, cro='---\nname: cro\n---\n\n# CRO\n')
        with self.assertRaises(ValueError):
            self.builder.build(upstream, self.base / "out")

    def test_condense_keeps_the_routing_sentence_within_the_budget(self) -> None:
        condensed = self.builder.condense_description(
            "When the user wants to " + "word " * 80 + ". Also use when the user says 'x'."
        )
        self.assertLessEqual(len(condensed), 220)
        self.assertTrue(condensed.endswith("…"))
        self.assertNotIn("Also use", condensed)


class MarketingTreeTests(unittest.TestCase):
    """Only `marketing` is discoverable, and every routed document stays reachable."""

    def setUp(self) -> None:
        self.skill_text = SKILL_MD.read_text(encoding="utf-8")
        self.routes = yaml.safe_load(ROUTES.read_text(encoding="utf-8"))["routes"]

    def test_only_the_router_is_discoverable(self) -> None:
        self.assertEqual([SKILL_MD], list(SKILL_DIR.rglob("SKILL.md")))

    def test_routes_and_packs_agree(self) -> None:
        packs = {
            path.name
            for path in SKILL_DIR.iterdir()
            if path.is_dir() and path.name not in LOCAL_ENTRIES
        }
        self.assertEqual(packs, {row["name"] for row in self.routes})
        for row in self.routes:
            with self.subTest(route=row["name"]):
                self.assertEqual(f"{row['name']}/{row['name']}.md", row["entry"])
                self.assertTrue((SKILL_DIR / row["entry"]).is_file())
                self.assertTrue(row["description"].strip())

    def test_router_index_lists_every_route(self) -> None:
        for row in self.routes:
            with self.subTest(route=row["name"]):
                self.assertIn(f"]({row['entry']})", self.skill_text)

    def test_product_context_is_the_first_routing_step(self) -> None:
        self.assertIn("Load the product context first", self.skill_text)
        self.assertLess(
            self.skill_text.index("Load the product context first"),
            self.skill_text.index("Match the request to one row"),
        )

    def test_router_maps_bare_workflow_names_to_pack_documents(self) -> None:
        self.assertIn("cro/cro.md", self.skill_text)
        self.assertIn("SKILL.md", self.skill_text)

    def test_every_routed_document_is_reachable_from_the_router(self) -> None:
        reached = reachable_files(SKILL_DIR)
        unreachable = [
            str(path.relative_to(SKILL_DIR))
            for path in sorted(SKILL_DIR.rglob("*.md"))
            if path.resolve() not in reached
        ]
        self.assertEqual([], unreachable)

    def test_routed_documents_carry_no_discovery_frontmatter(self) -> None:
        offenders = [
            str(path.relative_to(SKILL_DIR))
            for path in sorted(SKILL_DIR.glob("*/*.md"))
            if path.read_text(encoding="utf-8").startswith("---\n")
        ]
        self.assertEqual([], offenders)

    def test_local_files_survive_and_describe_the_sync(self) -> None:
        for relative in (
            "README.md",
            "SYNC.md",
            "agents/openai.yaml",
            "scripts/sync-marketing.sh",
            "coreyhaines31-LICENSE.txt",
        ):
            with self.subTest(path=relative):
                self.assertTrue((SKILL_DIR / relative).is_file())

    def test_sync_records_the_upstream_revision(self) -> None:
        sync = (SKILL_DIR / "SYNC.md").read_text(encoding="utf-8")
        self.assertIn("coreyhaines31/marketingskills", sync)
        self.assertIn("**Synced commit**:", sync)


if __name__ == "__main__":
    unittest.main()