from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/missav/scripts"


class MissavWorkflowTests(unittest.TestCase):
    def test_relative_browser_wrapper_preserves_challenge_stop_with_cdpath(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installed = root / ".agents/skills/missav/scripts"
            shutil.copytree(SCRIPTS, installed)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            browser = fake_bin / "agent-browser"
            browser.write_text("#!/usr/bin/env bash\nif [[ \"$*\" == *\"get title\"* ]]; then printf '%s\\n' 'Just a moment...'; fi\n")
            browser.chmod(0o755)
            result = subprocess.run(
                ["bash", ".agents/skills/missav/scripts/browse-page.sh", "https://missav.ws/cn/search/example"],
                cwd=root, env={**os.environ, "CDPATH": str(root), "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}", "MISSAV_CHROME": "/does/not/exist"},
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
            self.assertIn("Authorized API or site-owner access is required", result.stderr)

    def test_run_recommend_keeps_queries_with_spaces_as_one_url(self) -> None:
        """Given a multi-word preference, one query must reach the browser intact."""
        run_recommend = SCRIPTS / "run-recommend.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            command_log = root / "commands.log"
            prefs = root / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["first query"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then printf '%s\\n' 'Just a moment...'; fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export HOME="{root}/home"
export MISSAV_CHROME=/does/not/exist
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 42)
            opened = [
                line for line in command_log.read_text(encoding="utf-8").splitlines()
                if " open " in f" {line} "
            ]
            self.assertEqual(len(opened), 1)
            self.assertIn("/cn/search/first+query", opened[0])
            self.assertNotIn("first query", result.stderr)

    def test_run_recommend_does_not_initialize_default_home_for_custom_prefs(self) -> None:
        """A custom --prefs file must not create or mutate ~/.missav."""
        run_recommend = SCRIPTS / "run-recommend.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            prefs = root / "custom" / "preferences.json"
            prefs.parent.mkdir()
            prefs.write_text(
                '{"likes":{"genres":["first"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$*\" == *\"get title\"* ]]; then printf '%s\\n' 'Just a moment...'; fi\n",
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export HOME="{root}/home"
export MISSAV_CHROME=/does/not/exist
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 42)
            self.assertFalse((root / "home/.missav").exists())

    def test_short_genre_does_not_match_code_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            listings = Path(temporary_directory) / "listings.json"
            prefs = Path(temporary_directory) / "preferences.json"
            listings.write_text(
                '[{"href":"https://missav.ws/cn/hsm-089","slug":"hsm-089","title":"HSM-089","code":"HSM-089"}]',
                encoding="utf-8",
            )
            prefs.write_text(
                '{"likes":{"genres":["SM"]},"dislikes":{},"limit":10}',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "node",
                    str(SCRIPTS / "filter-recommendations.mjs"),
                    str(listings),
                    "--prefs",
                    str(prefs),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("genre:SM", result.stdout)

    def test_browse_page_preserves_blocked_access_exit_status(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        browse_page = SCRIPTS / "browse-page.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then
  printf '%s\\n' 'Just a moment...'
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browse_page}" "https://missav.ws/cn/search/example"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 42)
            self.assertIn("FAIL: could not load", result.stderr)
            commands = command_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                len([line for line in commands if "open https://missav.ws/cn/search/example" in line]),
                1,
            )

    def test_challenge_body_is_detected_when_title_is_generic(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"

        result = subprocess.run(
            [
                "bash",
                "-c",
                f'''source "{browser_env}"
missav_ab() {{
  if [[ "$1" == "get" && "$2" == "title" ]]; then
    printf '%s\\n' 'MissAV'
  elif [[ "$1" == "get" && "$2" == "text" && "$3" == "body" ]]; then
    printf '%s\\n' 'Enable JavaScript and cookies to continue'
  fi
}}
missav_stop_if_challenged
''',
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 42)
        self.assertIn("Authorized API or site-owner access is required", result.stderr)

    def test_run_recommend_stops_after_blocked_query(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["first"],"labels":["second"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then
  printf '%s\\n' 'Just a moment...'
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 42)
            commands = command_log.read_text(encoding="utf-8").splitlines()
            opened = [line for line in commands if " open " in f" {line} "]
            self.assertEqual(len(opened), 1)
            self.assertNotIn("second", "\n".join(opened))
            self.assertIn("Authorized API or site-owner access is required", result.stderr)

    def test_enrichment_challenge_is_not_reported_as_success(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["first"],"labels":[]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then
  if [[ "$*" == *"--session missav-run-"* && "$*" == *"enrich"* ]]; then
    printf '%s\\n' 'Just a moment...'
  else
    printf '%s\\n' 'Listing page'
  fi
fi
if [[ "$*" == *"eval"* && "$*" != *"enrich"* ]]; then
  printf '%s\\n' '[{{"href":"https://missav.ws/cn/test-001","slug":"test-001","title":"TEST-001","code":"TEST-001","duration":"1:00:00","durationMinutes":60}}]'
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('"items"', result.stdout)

    def test_category_prefixed_detail_url_is_accepted_as_valid(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        result = subprocess.run(
            [
                "bash",
                "-c",
                f'''source "{browser_env}"
missav_is_bad_url "https://missav.ws/dm1/cn/ssis-825" "detail"
''',
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        # missav_is_bad_url returns 1 when the URL is NOT bad (i.e. good)
        self.assertEqual(result.returncode, 1)

    def test_detail_extraction_supports_category_prefixed_urls(self) -> None:
        extract_detail_path = str(SCRIPTS / "extract-detail.js")
        js_code = f"""
        const fs = require('fs');
        const vm = require('vm');
        const code = fs.readFileSync('{extract_detail_path}', 'utf8');
        const context = {{
          location: {{
            href: 'https://missav.ws/dm247/cn/ssis-825',
            pathname: '/dm247/cn/ssis-825'
          }},
          document: {{
            title: 'SSIS-825 淫乱女教师 - 枫ふうあ',
            querySelectorAll: () => [],
            querySelector: (sel) => {{
              if (sel === 'h1') return {{ textContent: 'SSIS-825 淫乱女教师 - 枫ふうあ' }};
              if (sel && sel.includes('mb-1')) return {{ textContent: '剧情描述文本' }};
              return null;
            }}
          }},
          URL: URL,
          Set: Set,
          Map: Map,
          console: console
        }};
        vm.createContext(context);
        const output = vm.runInContext(code, context);
        console.log(output);
        """
        result = subprocess.run(
            ["node", "-e", js_code],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"code": "SSIS-825"', result.stdout)
        self.assertIn('"blocked": false', result.stdout)

    def test_slug_keyword_matches_user_keyword_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            listings = Path(temporary_directory) / "listings.json"
            prefs = Path(temporary_directory) / "preferences.json"
            listings.write_text(
                '[{"href":"https://missav.ws/cn/ssis-825-english-subtitle","slug":"ssis-825-english-subtitle","title":"SSIS-825 枫ふうあ","code":"SSIS-825"}]',
                encoding="utf-8",
            )
            prefs.write_text(
                '{"likes":{"keywords":["english-subtitle"]},"dislikes":{},"limit":10}',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "node",
                    str(SCRIPTS / "filter-recommendations.mjs"),
                    str(listings),
                    "--prefs",
                    str(prefs),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("keyword:english-subtitle", result.stdout)

    def test_signal_extraction_preserves_explicit_performers_and_code(self) -> None:
        js_code = f"""
        import('{SCRIPTS}/lib/preferences.mjs').then(m => {{
          const item = {{
            title: 'MIDV-123 三上悠亚',
            performers: ['三上悠亚']
          }};
          const signals = m.extractSignalsFromItem(item);
          console.log(JSON.stringify(signals));
        }});
        """
        result = subprocess.run(
            ["node", "--input-type=module", "-e", js_code],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"code":"MIDV-123"', result.stdout)
        self.assertIn('"labels":["MIDV"]', result.stdout)
        self.assertIn('"performers":["三上悠亚"]', result.stdout)

    def test_dislike_feedback_removes_matching_code_from_likes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            prefs_dir = Path(temporary_directory)
            item_file = prefs_dir / "item.json"
            item_file.write_text(
                '{"code":"SSIS-825","title":"SSIS-825 枫ふうあ","href":"https://missav.ws/cn/ssis-825"}',
                encoding="utf-8",
            )
            # init preferences
            subprocess.run(
                ["node", str(SCRIPTS / "preferences.mjs"), "init", "--dir", str(prefs_dir)],
                check=True,
                capture_output=True,
            )
            # like item first
            subprocess.run(
                [
                    "node",
                    str(SCRIPTS / "preferences.mjs"),
                    "feedback",
                    "like",
                    "--item",
                    str(item_file),
                    "--dir",
                    str(prefs_dir),
                ],
                check=True,
                capture_output=True,
            )
            # verify liked
            show_before = subprocess.run(
                ["node", str(SCRIPTS / "preferences.mjs"), "show", "--dir", str(prefs_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"SSIS-825"', show_before.stdout)

            # now dislike it
            subprocess.run(
                [
                    "node",
                    str(SCRIPTS / "preferences.mjs"),
                    "feedback",
                    "dislike",
                    "--item",
                    str(item_file),
                    "--dir",
                    str(prefs_dir),
                ],
                check=True,
                capture_output=True,
            )
            show_after = subprocess.run(
                ["node", str(SCRIPTS / "preferences.mjs"), "show", "--dir", str(prefs_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            import json
            data = json.loads(show_after.stdout)["preferences"]
            self.assertNotIn("SSIS-825", data["likes"]["codes"])
            self.assertIn("SSIS-825", data["dislikes"]["codes"])

    def test_description_analysis_executes_with_cli_genres_without_prefs_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            listings = Path(temporary_directory) / "listings.json"
            listings.write_text(
                '[{"href":"https://missav.ws/cn/test-sm","title":"Test Title","code":"TEST-01","description":"这篇剧情包含深喉和调教受虐"}]',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "node",
                    str(SCRIPTS / "filter-recommendations.mjs"),
                    str(listings),
                    "--genres",
                    "SM",
                    "--limit",
                    "5",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("desc:", result.stdout)

    def test_challenge_during_listing_extraction_stops_workflow(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["first","second"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            # Return normal title during browse open, but challenge during eval in extract-listings
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then
  if [[ "$*" == *"search/first"* ]] || [[ "$*" == *"first"* ]]; then
    printf '%s\\n' 'First listing title'
  fi
fi
if [[ "$*" == *"get url"* ]]; then
  printf '%s\\n' 'https://missav.ws/cn/search/first'
fi
if [[ "$*" == *"eval"* ]]; then
  # Simulate cloudflare challenge on extraction eval
  printf '%s\\n' 'Just a moment...'
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 42)
            commands = command_log.read_text(encoding="utf-8").splitlines()
            opened = [line for line in commands if " open " in f" {line} "]
            self.assertEqual(len(opened), 1)
            self.assertNotIn("second", "\n".join(opened))

    def test_workflow_passes_default_filter_from_preferences(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["testgenre"]},"search":{"defaultFilter":"chinese-subtitle"}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"get title"* ]]; then
  printf '%s\\n' 'Search page'
fi
if [[ "$*" == *"eval"* ]]; then
  printf '%s\\n' '[{{"href":"https://missav.ws/cn/test-01","slug":"test-01","title":"TEST-01","code":"TEST-01"}}]'
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            commands = command_log.read_text(encoding="utf-8").splitlines()
            opened = [line for line in commands if "open https://missav.ws" in line]
            self.assertTrue(any("filters=chinese-subtitle" in line for line in opened))

    def test_end_to_end_recommend_workflow_success(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"genres":["SM"],"labels":["SSIS"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
printf '%s\\n' "$*" >> "{command_log}"
if [[ "$*" == *"open "* ]]; then
  for arg in "$@"; do
    if [[ "$arg" == "http"* ]]; then
      printf '%s\\n' "$arg" > "{temporary_directory}/current_url.txt"
    fi
  done
fi
CURRENT_URL="$(cat "{temporary_directory}/current_url.txt" 2>/dev/null || true)"
if [[ "$*" == *"get title"* ]]; then
  printf '%s\\n' 'Regular Page Title'
fi
if [[ "$*" == *"get url"* ]]; then
  if [[ -n "$CURRENT_URL" ]]; then
    printf '%s\\n' "$CURRENT_URL"
  else
    printf '%s\\n' 'https://missav.ws/cn/search/sm'
  fi
fi
if [[ "$*" == *"eval"* ]]; then
  if [[ "$CURRENT_URL" == *"dm1"* || "$CURRENT_URL" == *"ssis-825"* ]]; then
    printf '%s\\n' '{{"href":"https://missav.ws/dm1/cn/ssis-825","slug":"ssis-825","title":"SSIS-825 淫乱女教师 - 枫ふうあ","code":"SSIS-825","description":"这是一部极品SM调教与受虐主题作品","tags":["SM","调教"],"performers":["枫ふうあ"],"genres":["SM"],"duration":"2:00:00","durationMinutes":120,"blocked":false}}'
  else
    printf '%s\\n' '[{{"href":"https://missav.ws/dm1/cn/ssis-825","slug":"ssis-825","title":"SSIS-825 淫乱女教师 - 枫ふうあ","code":"SSIS-825","duration":"2:00:00","durationMinutes":120}}]'
  fi
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn('"items"', result.stdout)
            self.assertIn("SSIS-825", result.stdout)
            self.assertIn("desc:", result.stdout)

    def test_detail_enrichment_fallback_on_missing_description(self) -> None:
        run_recommend = SCRIPTS / "run-recommend.sh"
        browser_env = SCRIPTS / "lib/browser-env.sh"

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            prefs = Path(temporary_directory) / "preferences.json"
            prefs.write_text(
                '{"likes":{"labels":["SSIS"]},"search":{}}',
                encoding="utf-8",
            )
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
set -e
if [[ "$*" == *"open "* ]]; then
  for arg in "$@"; do
    if [[ "$arg" == "http"* ]]; then
      printf '%s\\n' "$arg" > "{temporary_directory}/current_url.txt"
    fi
  done
fi
CURRENT_URL="$(cat "{temporary_directory}/current_url.txt" 2>/dev/null || true)"
if [[ "$*" == *"get title"* ]]; then
  printf '%s\\n' 'Regular Page Title'
fi
if [[ "$*" == *"get url"* ]]; then
  if [[ -n "$CURRENT_URL" ]]; then
    printf '%s\\n' "$CURRENT_URL"
  else
    printf '%s\\n' 'https://missav.ws/cn/search/ssis'
  fi
fi
if [[ "$*" == *"eval"* ]]; then
  if [[ "$CURRENT_URL" == *"dm1"* || "$CURRENT_URL" == *"ssis-825"* ]]; then
    # Return empty description
    printf '%s\\n' '{{"href":"https://missav.ws/dm1/cn/ssis-825","slug":"ssis-825","title":"SSIS-825","code":"SSIS-825","description":"","blocked":false}}'
  else
    printf '%s\\n' '[{{"href":"https://missav.ws/dm1/cn/ssis-825","slug":"ssis-825","title":"SSIS-825","code":"SSIS-825","duration":"2:00:00","durationMinutes":120}}]'
  fi
fi
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_CHROME=/does/not/exist
export MISSAV_START_SLEEP=0
source "{browser_env}"
source "{run_recommend}" --prefs "{prefs}"
''',
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn('"items"', result.stdout)
            self.assertIn("SSIS-825", result.stdout)
            self.assertIn("WARN: detail enrichment failed, showing list-only results", result.stderr)

    def test_parse_eval_json_recovers_from_noisy_stdout(self) -> None:
        js_code = f"""
        import('{SCRIPTS}/lib/parse-eval-json.mjs').then(m => {{
          const noisy = '[INFO] Connected to daemon\\n[\\n{{"href":"https://missav.ws/cn/test-1","code":"TEST-1"}}\\n]\\n[DEBUG] Done';
          const parsed = m.parseEvalJson(noisy);
          console.log(JSON.stringify(parsed));
        }});
        """
        result = subprocess.run(
            ["node", "--input-type=module", "-e", js_code],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"code":"TEST-1"', result.stdout)

    def test_build_search_url_rejects_empty_query(self) -> None:
        result = subprocess.run(
            ["node", str(SCRIPTS / "build-search-url.mjs"), "search", "   "],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Search query must not be empty", result.stderr)

    def test_preferences_cli_help_exits_zero(self) -> None:
        result = subprocess.run(
            ["node", str(SCRIPTS / "preferences.mjs"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stderr)

    def test_user_chrome_cdp_mode_uses_cdp_flag(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_USE_USER_CHROME=1
export MISSAV_CDP_PORT=9222
source "{browser_env}"
_missav_ab_base get title
''',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            commands = command_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(commands), 1)
            self.assertIn("--cdp 9222 get title", commands[0])
            self.assertNotIn("--session", commands[0])
            self.assertNotIn("--executable-path", commands[0])

    def test_user_chrome_cdp_mode_preserves_running_browser(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_USE_USER_CHROME=1
source "{browser_env}"
missav_browser_start
missav_browser_close
''',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            commands = command_log.read_text(encoding="utf-8") if command_log.exists() else ""
            self.assertNotIn("close", commands)

    def test_default_mode_is_user_chrome(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            # Do NOT set MISSAV_USE_USER_CHROME
            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
unset MISSAV_USE_USER_CHROME
source "{browser_env}"
_missav_ab_base get title
''',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            commands = command_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(commands), 1)
            self.assertIn("--cdp 9222", commands[0])

    def test_isolated_mode_disables_user_chrome(self) -> None:
        browser_env = SCRIPTS / "lib/browser-env.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory) / "bin"
            fake_bin.mkdir()
            command_log = Path(temporary_directory) / "commands.log"
            fake_browser = fake_bin / "agent-browser"
            fake_browser.write_text(
                f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{command_log}"
''',
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)

            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'''export PATH="{fake_bin}:$PATH"
export MISSAV_USE_USER_CHROME=0
source "{browser_env}"
_missav_ab_base get title
''',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            commands = command_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(commands), 1)
            self.assertNotIn("--cdp", commands[0])
            self.assertIn("--session", commands[0])




if __name__ == "__main__":
    unittest.main()

