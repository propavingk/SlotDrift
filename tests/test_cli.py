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
