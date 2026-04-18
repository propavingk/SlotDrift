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
        report = analyze_continuity(records)
        self.assertEqual(report.missing, [2])

    def test_duplicate_slot_counted(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized", "blockhash": "A"}',
                '{"slot": 1, "parent": 0, "commitment": "processed", "blockhash": "B"}',
            ]
        )
        records, _ = parse_text(text)
        report = analyze_continuity(records)
        self.assertEqual(report.duplicates, {1: 2})

    def test_parent_marked_skipped_is_an_anomaly(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized"}',
                '{"slot": 2, "commitment": "skipped"}',
                '{"slot": 3, "parent": 2, "commitment": "finalized"}',
            ]
        )
        records, _ = parse_text(text)
        report = analyze_continuity(records)
        self.assertEqual(
            report.parent_anomalies, [(3, 2, "parent slot is marked skipped")]
        )

    def test_step_over_produced_slots_is_an_anomaly(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized"}',
                '{"slot": 2, "parent": 1, "commitment": "finalized"}',
                '{"slot": 3, "parent": 1, "commitment": "finalized"}',
            ]
        )
        records, _ = parse_text(text)
        report = analyze_continuity(records)
        self.assertEqual(
            report.parent_anomalies, [(3, 1, "step over slots not marked skipped")]
        )

    def test_step_over_skipped_slots_is_not_an_anomaly(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized"}',
                '{"slot": 2, "commitment": "skipped"}',
                '{"slot": 3, "commitment": "skipped"}',
                '{"slot": 4, "parent": 1, "commitment": "finalized"}',
            ]
        )
        records, _ = parse_text(text)
        report = analyze_continuity(records)
        self.assertEqual(report.parent_anomalies, [])

    def test_leader_stats_and_skip_rate(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized", "leader": "A"}',
                '{"slot": 2, "commitment": "skipped", "leader": "A"}',
                '{"slot": 3, "parent": 1, "commitment": "finalized", "leader": "B"}',
            ]
        )
        records, _ = parse_text(text)
        report = analyze_continuity(records)
        self.assertEqual(report.leaders["A"].scheduled, 2)
        self.assertEqual(report.leaders["A"].skipped, 1)
        self.assertEqual(report.leaders["A"].produced, 1)
        self.assertAlmostEqual(report.leaders["A"].skip_rate, 0.5)
        self.assertAlmostEqual(report.leaders["B"].skip_rate, 0.0)

    def test_empty_export(self):
        report = analyze_continuity([])
        self.assertEqual(report.record_count, 0)
        self.assertIsNone(report.min_slot)
        self.assertEqual(report.findings, 0)


if __name__ == "__main__":
    unittest.main()
