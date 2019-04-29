"""Tests for record parsing and validation."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from slotdrift.model import FormatError, parse_record, parse_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def decode(line: str) -> object:
    return json.loads(line)


class ParseRecordTests(unittest.TestCase):
    def test_minimal_valid_record(self):
        record = parse_record(
            {"slot": 10, "parent": 9, "commitment": "finalized", "leader": "A"}, 1
        )
        self.assertEqual(record.slot, 10)
        self.assertEqual(record.parent, 9)
        self.assertFalse(record.skipped)
        self.assertEqual(record.rank, 2)

