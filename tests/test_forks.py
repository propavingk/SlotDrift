"""Tests for fork detection and orphan segmentation."""
from __future__ import annotations

import unittest
from pathlib import Path

from slotdrift.forks import find_forks
from slotdrift.model import parse_file, parse_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class ClusterWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records, errors = parse_file(SAMPLES / "cluster-window.jsonl")
        assert not errors
        cls.report = find_forks(records)

    def test_duplicate_slots(self):
        self.assertEqual(
            sorted(self.report.duplicate_slots), [320400040, 320400041, 320400042]
        )
        for hashes in self.report.duplicate_slots.values():
            self.assertEqual(len(hashes), 2)

    def test_canonical_tip(self):
        self.assertEqual(self.report.canonical_tip, 320400060)

    def test_orphan_segments(self):
        segments = self.report.orphan_segments
        self.assertEqual(len(segments), 2)
        rival = segments[0]
        self.assertEqual((rival.start_slot, rival.end_slot), (320400040, 320400042))
        self.assertEqual(rival.length, 3)
