from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/tropes/scripts/load-preferences.sh"


class TropesPreferenceLoaderTests(unittest.TestCase):
    """Given isolated layers, the loader merges only valid object layers."""

    def run_loader(self, layers: dict[str, str], files: dict[str, object]):
        # Given explicit layer paths and no real HOME/project files
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = os.environ.copy()
            for variable, relative in layers.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                value = files.get(variable)
                if value is not None:
                    path.write_text(json.dumps(value), encoding="utf-8")
                env[variable] = str(path)
            # Empty overrides must disable their layers, including HOME lookup.
            env["HOME"] = str(root / "empty-home")
            completed = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=root,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(completed.stdout)

    def test_given_four_layers_when_loaded_then_higher_object_entries_win(self):
        layers = {
            "OFFICE_GLOBAL_SHARED": "global.json",
            "OFFICE_GLOBAL_LOCAL": "global-local.json",
            "OFFICE_PROJECT_SHARED": "project.json",
            "OFFICE_PROJECT_LOCAL": "project-local.json",
        }
        result = self.run_loader(
            layers,
            {
                "OFFICE_GLOBAL_SHARED": {
                    "tone": "formal",
                    "pattern_caps": [{"id": "arrow_flow", "max_nodes": 4}],
                },
                "OFFICE_GLOBAL_LOCAL": {
                    "pattern_caps": [{"id": "arrow_flow", "max_nodes": 3}],
                },
                "OFFICE_PROJECT_SHARED": {
                    "banned_words": ["buzzword"],
                },
                "OFFICE_PROJECT_LOCAL": {
                    "banned_words": ["private"],
                },
            },
        )

        self.assertEqual(result["tone"], "formal")
        self.assertEqual(result["pattern_caps"], [{"id": "arrow_flow", "max_nodes": 3}])
        self.assertEqual(result["banned_words"], ["buzzword", "private"])

    def test_given_empty_overrides_when_loaded_then_real_home_is_not_consulted(self):
        layers = {
            "OFFICE_GLOBAL_SHARED": "",
            "OFFICE_GLOBAL_LOCAL": "",
            "OFFICE_PROJECT_SHARED": "",
            "OFFICE_PROJECT_LOCAL": "",
        }
        self.assertEqual(self.run_loader(layers, {}), {})

    def test_given_scalar_layer_when_loaded_then_it_is_ignored_without_corrupting_merge(self):
        layers = {
            "OFFICE_GLOBAL_SHARED": "invalid.json",
            "OFFICE_GLOBAL_LOCAL": "valid.json",
            "OFFICE_PROJECT_SHARED": "",
            "OFFICE_PROJECT_LOCAL": "",
        }
        result = self.run_loader(
            layers,
            {
                "OFFICE_GLOBAL_SHARED": ["invalid-root"],
                "OFFICE_GLOBAL_LOCAL": {"tone": "neutral"},
            },
        )
        self.assertEqual(result, {"tone": "neutral"})


if __name__ == "__main__":
    unittest.main()
