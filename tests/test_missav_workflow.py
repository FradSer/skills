from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/missav/scripts"


class MissavWorkflowTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
