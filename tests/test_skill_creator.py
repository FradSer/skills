from concurrent.futures import Future
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CREATOR = ROOT / ".agents/skills/skill-creator"
SCRIPTS = CREATOR / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillCreatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.skill = self.root / "sample"
        self.skill.mkdir()
        self.write_skill()

    def write_skill(self, metadata: str = "name: sample\ndescription: Handle sample inputs", body: str = "# Sample\n\nRead the supplied input and return its summary.") -> None:
        (self.skill / "SKILL.md").write_text(f"---\n{metadata}\n---\n{body}\n", encoding="utf-8")

    def test_validator_rejects_empty_fields_and_body(self) -> None:
        validator = load_module("creator_validate", SCRIPTS / "quick_validate.py")
        for metadata, body in (
            ('name: ""\ndescription: Useful input', "# Instructions"),
            ('name: sample\ndescription: " "', "# Instructions"),
            ('name: sample\ndescription: Useful input', ""),
            ('name: sample\ndescription: Useful input\ndisable-model-invocation: "false"', "# Instructions"),
        ):
            with self.subTest(metadata=metadata, body=body):
                self.write_skill(metadata, body)
                valid, message = validator.validate_skill(self.skill)
                self.assertFalse(valid, message)

    def test_validator_accepts_existing_runtime_metadata(self) -> None:
        validator = load_module("creator_validate", SCRIPTS / "quick_validate.py")
        self.write_skill("name: sample\ndescription: Useful input\ncompatibility: Python 3\ndisable-model-invocation: true\nmetadata:\n  version: '1'")
        self.assertTrue(validator.validate_skill(self.skill)[0])

    def test_package_direct_cli_from_another_working_directory(self) -> None:
        resources = self.skill / "references"
        resources.mkdir()
        (resources / "guide.md").write_text("Use this guide", encoding="utf-8")
        evaluations = self.skill / "evals"
        evaluations.mkdir()
        (evaluations / "evals.json").write_text("{}", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "package_skill.py"), str(self.skill), str(self.root / "out")],
            cwd=self.root, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.root / "out/sample.skill") as archive:
            self.assertEqual(set(archive.namelist()), {"sample/SKILL.md", "sample/references/guide.md"})

    def package_module(self, output: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "scripts.package_skill", str(self.skill), str(output)],
            cwd=CREATOR, capture_output=True, text=True, timeout=30,
        )

    def test_packaging_rejects_an_external_symlink(self) -> None:
        outside = self.root / "private.txt"
        outside.write_text("synthetic private fixture", encoding="utf-8")
        (self.skill / "outside.txt").symlink_to(outside)
        result = self.package_module(self.root / "out")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / "out/sample.skill").exists())

    def test_archive_does_not_contain_itself(self) -> None:
        result = self.package_module(self.skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.skill / "sample.skill") as archive:
            self.assertEqual(archive.namelist(), ["sample/SKILL.md"])

    def test_metadata_parser_uses_yaml_values(self) -> None:
        utilities = load_module("creator_utils", SCRIPTS / "utils.py")
        self.write_skill('name: sample # identifier\ndescription: "Say \\"hello\\" to input"')
        name, description, _ = utilities.parse_skill_md(self.skill)
        self.assertEqual(name, "sample")
        self.assertEqual(description, 'Say "hello" to input')

    def test_execution_error_cannot_pass_a_negative_trigger_case(self) -> None:
        with patch.dict(sys.modules):
            sys.path.insert(0, str(CREATOR))
            self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
            evaluation = load_module("creator_run_eval", SCRIPTS / "run_eval.py")

        class FailedExecutor:
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def submit(self, *args):
                future = Future()
                future.set_exception(RuntimeError("synthetic worker outage"))
                return future

        with patch.object(evaluation, "ProcessPoolExecutor", FailedExecutor):
            result = evaluation.run_eval(
                [{"query": "An unrelated task", "should_trigger": False}],
                "sample", "Useful input", 1, 1, self.root,
            )
        self.assertFalse(result["results"][0]["pass"])
        self.assertTrue(result["results"][0]["errors"])

    def test_trigger_events_are_drained_after_process_exit(self) -> None:
        sys.path.insert(0, str(CREATOR))
        self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
        evaluation = load_module("creator_drain_eval", SCRIPTS / "run_eval.py")
        event = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "unrelated.md"}},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "sample-skill-abcdabcd"}},
        ]}}
        stream = io.BytesIO((json.dumps(event) + "\n").encode())
        process = SimpleNamespace(stdout=stream, poll=lambda: 0, returncode=0)
        with patch.object(evaluation.uuid, "uuid4", return_value=SimpleNamespace(hex="abcdabcd")), patch.object(evaluation.subprocess, "Popen", return_value=process):
            triggered = evaluation.run_single_query("sample task", "sample", "Useful input", 1, str(self.root))
        self.assertTrue(triggered)
        self.assertTrue(stream.closed)

    def test_cli_failure_is_not_a_measured_non_trigger(self) -> None:
        sys.path.insert(0, str(CREATOR))
        self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
        evaluation = load_module("creator_failure_eval", SCRIPTS / "run_eval.py")
        process = SimpleNamespace(stdout=io.BytesIO(), poll=lambda: 1, returncode=1)
        with patch.object(evaluation.subprocess, "Popen", return_value=process):
            with self.assertRaises(RuntimeError):
                evaluation.run_single_query("unrelated task", "sample", "Useful input", 1, str(self.root))

    def test_small_holdout_preserves_training_and_global_random_state(self) -> None:
        sys.path.insert(0, str(CREATOR))
        self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
        loop = load_module("creator_run_loop", SCRIPTS / "run_loop.py")
        cases = [{"query": "yes", "should_trigger": True}, {"query": "no", "should_trigger": False}]
        before = random.getstate()
        train, test = loop.split_eval_set(cases, 0.4)
        self.assertEqual(len(train), 2)
        self.assertEqual(test, [])
        self.assertEqual(random.getstate(), before)

    def test_static_viewer_cannot_be_closed_by_prompt_text(self) -> None:
        viewer = load_module("creator_viewer", CREATOR / "eval-viewer/generate_review.py")
        payload = "</script><script>alert('synthetic fixture')</script>"
        page = viewer.generate_html([{"prompt": payload}], "sample")
        self.assertTrue(payload not in page, "Prompt text escaped the embedded JSON script")

    def test_viewer_excludes_symlinked_outputs_and_files(self) -> None:
        viewer = load_module("creator_viewer_links", CREATOR / "eval-viewer/generate_review.py")
        workspace = self.root / "workspace"
        workspace.mkdir()
        private = self.root / "private"
        private.mkdir()
        (private / "secret.txt").write_text("synthetic private fixture")
        linked_run = workspace / "linked"
        linked_run.mkdir()
        (linked_run / "outputs").symlink_to(private, target_is_directory=True)
        regular_run = workspace / "regular"
        (regular_run / "outputs").mkdir(parents=True)
        (regular_run / "outputs/secret.txt").symlink_to(private / "secret.txt")
        self.assertNotIn("synthetic private fixture", json.dumps(viewer.find_runs(workspace)))

    def test_viewer_sorts_missing_metadata_after_numbered_runs(self) -> None:
        viewer = load_module("creator_viewer_sort", CREATOR / "eval-viewer/generate_review.py")
        for name in ("a", "b"):
            (self.root / name / "outputs").mkdir(parents=True)
        (self.root / "a/eval_metadata.json").write_text(json.dumps({"eval_id": 2, "prompt": "A"}))
        self.assertEqual([run["eval_id"] for run in viewer.find_runs(self.root)], [2, None])

    def test_viewer_finds_metadata_above_nested_config_runs(self) -> None:
        viewer = load_module("creator_viewer_nested", CREATOR / "eval-viewer/generate_review.py")
        evaluation = self.root / "eval-0-case"
        (evaluation / "with_skill/run-1/outputs").mkdir(parents=True)
        (evaluation / "eval_metadata.json").write_text(json.dumps({"eval_id": 0, "prompt": "Nested input"}))
        run = viewer.find_runs(self.root)[0]
        self.assertEqual((run["eval_id"], run["prompt"]), (0, "Nested input"))

    def test_busy_viewer_port_uses_a_free_port_without_killing_processes(self) -> None:
        viewer = load_module("creator_viewer_port", CREATOR / "eval-viewer/generate_review.py")
        (self.root / "outputs").mkdir()
        server = SimpleNamespace(server_address=("127.0.0.1", 49152), serve_forever=lambda: (_ for _ in ()).throw(KeyboardInterrupt()), server_close=lambda: None)
        with patch.object(sys, "argv", ["generate_review.py", str(self.root)]), patch.object(viewer, "HTTPServer", side_effect=[OSError("busy"), server]) as http, patch.object(subprocess, "run", return_value=SimpleNamespace(stdout="424242\n")), patch.object(os, "kill") as kill, patch.object(viewer.webbrowser, "open") as browser, patch.object(sys, "stdout", io.StringIO()):
            viewer.main()
        kill.assert_not_called()
        self.assertEqual(http.call_args_list[1].args[0], ("127.0.0.1", 0))
        browser.assert_called_once_with("http://localhost:49152")

    def test_evaluation_rejects_invalid_inputs_before_starting_workers(self) -> None:
        sys.path.insert(0, str(CREATOR))
        self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
        evaluation = load_module("creator_eval_inputs", SCRIPTS / "run_eval.py")
        case = {"query": "sample", "should_trigger": True}
        for cases, options in (([], {}), ([case], {"runs_per_query": 0}), ([case], {"num_workers": 0}), ([case], {"timeout": 0}), ([case], {"trigger_threshold": float("nan")}), ([case, case], {}), ([{"query": "sample", "should_trigger": "false"}], {})):
            with self.subTest(cases=cases, options=options), patch.object(evaluation, "ProcessPoolExecutor") as executor:
                future = Future()
                future.set_result(True)
                executor.return_value.__enter__.return_value.submit.return_value = future
                arguments = {"num_workers": 1, "timeout": 1, **options}
                with self.assertRaises(ValueError):
                    evaluation.run_eval(cases, "sample", "Useful input", project_root=self.root, **arguments)
                executor.assert_not_called()

    def test_loop_rejects_empty_duplicate_and_zero_iteration_inputs(self) -> None:
        sys.path.insert(0, str(CREATOR))
        self.addCleanup(lambda: sys.path.remove(str(CREATOR)))
        loop = load_module("creator_loop_inputs", SCRIPTS / "run_loop.py")
        case = {"query": "sample", "should_trigger": True}
        measured = {"results": [{**case, "pass": True}], "summary": {"total": 1, "passed": 1, "failed": 0}}
        for cases, iterations in (([], 1), ([case, case], 1), ([case], 0)):
            with self.subTest(cases=cases, iterations=iterations), patch.object(loop, "run_eval", return_value=measured) as evaluate:
                with self.assertRaises(ValueError):
                    loop.run_loop(cases, self.skill, None, 1, 1, iterations, 1, 0.5, 0, "mock", False)
                evaluate.assert_not_called()

    def write_grading(self, path: Path, rate: float = 0.5) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"summary": {"pass_rate": rate, "passed": 1, "failed": 1, "total": 2}, "execution_metrics": {"output_chars": 9000}}))

    def test_benchmark_reports_actual_runs_and_no_unmeasured_baseline(self) -> None:
        benchmark = load_module("creator_benchmark", SCRIPTS / "aggregate_benchmark.py")
        self.write_grading(self.root / "eval-0/with_skill/run-1/grading.json")
        result = benchmark.generate_benchmark(self.root)
        self.assertEqual(result["metadata"]["runs_per_configuration"], 1)
        self.assertNotIn("delta", result["run_summary"])
        self.assertIsNone(result["runs"][0]["result"]["tokens"])
        self.assertNotIn("| 0% ± 0%", benchmark.generate_markdown(result))

    def test_benchmark_skips_malformed_run_directories(self) -> None:
        benchmark = load_module("creator_benchmark_names", SCRIPTS / "aggregate_benchmark.py")
        self.write_grading(self.root / "eval-0/with_skill/run-bad/grading.json")
        self.write_grading(self.root / "eval-0/with_skill/run-1/grading.json")
        self.assertEqual(len(benchmark.generate_benchmark(self.root)["runs"]), 1)

    def test_benchmark_requires_a_declared_comparison_pair(self) -> None:
        benchmark = load_module("creator_benchmark_pair", SCRIPTS / "aggregate_benchmark.py")
        results = {"foo": [{"pass_rate": 0.4, "time_seconds": None, "tokens": None}], "bar": [{"pass_rate": 0.8, "time_seconds": None, "tokens": None}]}
        self.assertNotIn("delta", benchmark.aggregate_results(results))
        explicit = benchmark.aggregate_results(results, primary_config="bar", baseline_config="foo")
        self.assertEqual(explicit["delta"]["pass_rate"], "+0.40")
        with self.assertRaises(ValueError):
            benchmark.aggregate_results(results, primary_config="bar")

    def test_single_configuration_viewer_has_no_baseline_or_delta_columns(self) -> None:
        source = (CREATOR / "eval-viewer/viewer.html").read_text()
        render = re.search(r"    function renderBenchmark\(\) \{[\s\S]*?\n    \}", source).group(0)
        script = "const target = {innerHTML: '', style: {}}; const document = {getElementById: () => target}; const escapeHtml = value => String(value); const EMBEDDED_DATA = " + json.dumps({"benchmark": {"metadata": {"skill_name": "sample", "runs_per_configuration": 1}, "run_summary": {"with_skill": {"pass_rate": {"mean": 0.5, "stddev": 0}, "tokens": {"mean": None, "stddev": None}}}}}) + ";\n" + render + "\nrenderBenchmark(); process.stdout.write(target.innerHTML);"
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        header = result.stdout.split("</thead>")[0]
        self.assertNotIn("Baseline", header)
        self.assertNotIn("Delta", header)


if __name__ == "__main__":
    unittest.main()
