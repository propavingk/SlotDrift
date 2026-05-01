"""End to end tests through the CLI entry point."""
from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

from slotdrift.cli import main

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def run(args: list[str]) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(args)
    return code, buffer.getvalue()


class ExitCodeTests(unittest.TestCase):
    def test_clean_window_exits_zero(self):
        code, output = run(["analyze", str(SAMPLES / "clean-window.jsonl")])
        self.assertEqual(code, 0)
        self.assertIn("FINDINGS: 0", output)

    def test_cluster_window_exits_one(self):
        code, output = run(["analyze", str(SAMPLES / "cluster-window.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("FINDINGS: 12", output)

    def test_broken_lines_exit_one_with_parse_errors(self):
        code, output = run(["analyze", str(SAMPLES / "broken-lines.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("parse errors: 7", output)
        self.assertIn("records: 2", output)

    def test_missing_input_exits_two(self):
        with self.assertRaises(SystemExit) as caught:
            run(["analyze", str(SAMPLES / "does-not-exist.jsonl")])
        self.assertEqual(caught.exception.code, 2)

    def test_version_exits_zero(self):
        with self.assertRaises(SystemExit) as caught:
            run(["--version"])
        self.assertEqual(caught.exception.code, 0)


class FormatTests(unittest.TestCase):
    def test_json_output_has_expected_shape(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(
                ["analyze", str(SAMPLES / "cluster-window.jsonl"), "--format", "json"]
            )
        self.assertEqual(code, 1)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["records"], 64)
        self.assertEqual(payload["findings"], 12)
        self.assertEqual(payload["forks"]["canonical_tip"], 320400060)
        self.assertEqual(len(payload["forks"]["orphan_segments"]), 2)
        self.assertEqual(payload["parse_errors"], [])

    def test_limit_truncates_lists(self):
        code, output = run(
            ["analyze", str(SAMPLES / "cluster-window.jsonl"), "--limit", "1"]
        )
        self.assertEqual(code, 1)
        self.assertIn("... 2 more duplicate slots", output)

    def test_leaders_command_lines(self):
        code, output = run(["leaders", str(SAMPLES / "clean-window.jsonl")])
        self.assertEqual(code, 0)
        lines = [line for line in output.splitlines() if line.strip()]
        self.assertTrue(any("skipped 1/4 (25.0%)" in line for line in lines))

    def test_forks_command_reports_segments(self):
        code, output = run(["forks", str(SAMPLES / "cluster-window.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("duplicate slot 320400040: 2 blockhashes", output)
        self.assertIn("orphan segment 320400056..320400057", output)


if __name__ == "__main__":
    unittest.main()
