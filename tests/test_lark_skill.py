import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
LARK_DIR = ROOT / "skills/lark"
SKILL_MD = LARK_DIR / "SKILL.md"
README_MD = LARK_DIR / "README.md"
SYNC_MD = LARK_DIR / "SYNC.md"
SYNC_SCRIPT = LARK_DIR / "scripts/sync-lark.sh"

OBSOLETE_SUBSKILLS = [
    "lark-approval",
    "lark-apps",
    "lark-attendance",
    "lark-base",
    "lark-calendar",
    "lark-contact",
    "lark-doc",
    "lark-drive",
    "lark-event",
    "lark-im",
    "lark-mail",
    "lark-markdown",
    "lark-minutes",
    "lark-note",
    "lark-okr",
    "lark-openapi-explorer",
    "lark-shared",
    "lark-sheets",
    "lark-skill-maker",
    "lark-slides",
    "lark-task",
    "lark-vc",
    "lark-vc-agent",
    "lark-whiteboard",
    "lark-wiki",
    "lark-workflow-meeting-summary",
    "lark-workflow-standup-report",
]


class LarkSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL_MD.read_text(encoding="utf-8")
        parts = self.text.split("---\n", 2)
        self.frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

    def test_frontmatter_configuration(self) -> None:
        self.assertEqual(self.frontmatter.get("name"), "lark")
        self.assertIn("lark-cli skills read", self.frontmatter.get("description", ""))
        self.assertIn("lark-cli", self.frontmatter.get("metadata", {}).get("requires", {}).get("bins", []))

    def test_shared_auth_prerequisite_guidance(self) -> None:
        self.assertIn("lark-cli skills read lark-shared", self.text)
        self.assertIn("lark-cli auth login", self.text)

    def test_subskill_index_table_uses_skills_read(self) -> None:
        self.assertIn("## Sub-skill Index", self.text)
        for subskill in ("lark-shared", "lark-doc", "lark-base", "lark-im", "lark-sheets", "lark-calendar", "lark-mail"):
            self.assertIn(f"`lark-cli skills read {subskill}`", self.text)

    def test_hoists_lark_shared_at_top_of_table(self) -> None:
        table_start = self.text.find("## Sub-skill Index")
        self.assertNotEqual(table_start, -1)
        table_text = self.text[table_start:]
        shared_pos = table_text.find("`lark-cli skills read lark-shared`")
        doc_pos = table_text.find("`lark-cli skills read lark-doc`")
        self.assertNotEqual(shared_pos, -1)
        self.assertNotEqual(doc_pos, -1)
        self.assertLess(shared_pos, doc_pos)

    def test_reference_file_routing_instructions(self) -> None:
        self.assertIn("lark-cli skills read <sub-skill>/<path>", self.text)
        self.assertIn("lark-cli schema", self.text)

    def test_no_obsolete_subdirectories_in_skill_tree(self) -> None:
        for sub in OBSOLETE_SUBSKILLS:
            sub_dir = LARK_DIR / sub
            self.assertFalse(sub_dir.exists(), f"Obsolete sub-skill directory {sub_dir} should not exist")
        self.assertFalse((LARK_DIR / ".backup").exists(), "Backup directory should not be tracked")

    def test_readme_and_sync_md_reflect_skills_read_architecture(self) -> None:
        readme_text = README_MD.read_text(encoding="utf-8")
        self.assertIn("lark-cli skills read", readme_text)
        sync_text = SYNC_MD.read_text(encoding="utf-8")
        self.assertIn("lark-cli skills read", sync_text)
        self.assertIn("lark-cli skills list", sync_text)

    def test_sync_script_dry_run_or_refresh(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), f"{SYNC_SCRIPT} must exist")
        result = subprocess.run([str(SYNC_SCRIPT), "--check"], capture_output=True, text=True)
        self.assertIn(result.returncode, (0, 1))

    def test_sync_never_prunes_local_skill_directories_implicitly(self) -> None:
        script = SYNC_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("-exec rm", script)

    def test_refresh_updates_last_checked_date_and_preserves_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "skills/lark"
            shutil.copytree(LARK_DIR, target)
            tool = root / "tools/skill-sync"
            tool.mkdir(parents=True)
            shutil.copy(ROOT / "tools/skill-sync/gen-index.py", tool)
            (target / "SYNC.md").write_text("**Last checked**: 2000-01-01\n**lark-cli version**: 0.0.0\n")
            local = target / "local-draft/note.md"
            local.parent.mkdir()
            local.write_text("Preserve local fixture")
            commands = root / "bin"
            commands.mkdir()
            for name, body in (("lark-cli", '#!/bin/sh\nif [ "$1" = --version ]; then echo "lark-cli 1.2.3"; else echo \'{"skills":[{"name":"lark-shared","description":"Shared fixture","version":"1"}]}\'; fi\n'), ("date", "#!/bin/sh\necho 2099-01-01\n")):
                path = commands / name
                path.write_text(body)
                path.chmod(0o755)
            result = subprocess.run(["bash", str(target / "scripts/sync-lark.sh")], env={**os.environ, "PATH": f"{commands}{os.pathsep}{os.environ['PATH']}"}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("**Last checked**: 2099-01-01", (target / "SYNC.md").read_text())
            self.assertIn("**lark-cli version**: 1.2.3", (target / "SYNC.md").read_text())
            self.assertEqual(local.read_text(), "Preserve local fixture")


if __name__ == "__main__":
    unittest.main()
