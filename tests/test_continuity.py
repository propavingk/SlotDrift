"""Tests for continuity analysis."""
from __future__ import annotations

import unittest
from pathlib import Path

from slotdrift.continuity import analyze_continuity
from slotdrift.model import parse_file, parse_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class CleanWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records, errors = parse_file(SAMPLES / "clean-window.jsonl")
        assert not errors
        cls.report = analyze_continuity(records)

    def test_window_bounds(self):
        self.assertEqual(self.report.min_slot, 100000000)
        self.assertEqual(self.report.max_slot, 100000029)
        self.assertEqual(self.report.window, 30)

