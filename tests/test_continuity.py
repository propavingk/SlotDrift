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

    def test_no_findings(self):
        self.assertEqual(self.report.missing, [])
        self.assertEqual(self.report.duplicates, {})
        self.assertEqual(self.report.parent_anomalies, [])
        self.assertEqual(self.report.findings, 0)

    def test_skipped_slots_recorded(self):
        self.assertEqual(self.report.skipped, [100000010, 100000011])

    def test_boundary_parent_below_window_is_not_an_anomaly(self):
        self.assertEqual(self.report.parent_anomalies, [])


class InMemoryTests(unittest.TestCase):
    def test_missing_slot_detected(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized"}',
                '{"slot": 3, "parent": 1, "commitment": "finalized"}',
            ]
        )
        records, errors = parse_text(text)
        self.assertEqual(errors, [])
