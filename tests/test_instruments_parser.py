import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/swiftui/scripts/analyze_trace.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("analyze_trace", SCRIPT)
assert SPEC and SPEC.loader
analyze_trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyze_trace)


class WindowParsingTests(unittest.TestCase):
    def test_rejects_non_finite_window_values(self) -> None:
        with self.assertRaises(SystemExit):
            analyze_trace._parse_window("nan:10")
