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
        self.assertEqual(rival.root_parent, 320400039)
        self.assertEqual(rival.commitments, {"processed": 3})
        reorg = segments[1]
        self.assertEqual((reorg.start_slot, reorg.end_slot), (320400056, 320400057))
        self.assertEqual(reorg.length, 2)
        self.assertEqual(reorg.root_parent, 320400055)
        self.assertEqual(reorg.commitments, {"finalized": 2})

    def test_orphan_count(self):
        self.assertEqual(self.report.orphan_count, 5)

    def test_findings(self):
        self.assertEqual(self.report.findings, 3 + 5)


class IdentityTests(unittest.TestCase):
    def test_orphan_detected_at_a_duplicated_slot(self):
        # Two blocks claim slot 1. The finalized one wins; the processed one is
        # orphaned even though its slot number is canonical.
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized", "blockhash": "A"}',
                '{"slot": 1, "parent": 0, "commitment": "processed", "blockhash": "B"}',
                '{"slot": 2, "parent": 1, "commitment": "finalized", "blockhash": "C"}',
            ]
        )
        records, _ = parse_text(text)
        report = find_forks(records)
        self.assertEqual(report.duplicate_slots, {1: ["A", "B"]})
        self.assertEqual(report.orphan_count, 1)
        self.assertEqual(report.orphan_segments[0].start_slot, 1)

    def test_single_chain_has_no_orphans(self):
        text = "\n".join(
            [
                '{"slot": 1, "parent": 0, "commitment": "finalized", "blockhash": "A"}',
                '{"slot": 2, "parent": 1, "commitment": "finalized", "blockhash": "B"}',
            ]
        )
        records, _ = parse_text(text)
        report = find_forks(records)
        self.assertEqual(report.duplicate_slots, {})
        self.assertEqual(report.orphan_segments, [])
        self.assertEqual(report.orphan_count, 0)
