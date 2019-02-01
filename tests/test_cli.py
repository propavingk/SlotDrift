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
