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

    def test_skipped_record_needs_no_parent(self):
        record = parse_record({"slot": 11, "commitment": "skipped"}, 1)
        self.assertTrue(record.skipped)
        self.assertIsNone(record.parent)

    def test_missing_slot_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record({"commitment": "finalized"}, 4)

    def test_negative_slot_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record({"slot": -1, "commitment": "skipped"}, 4)

    def test_unknown_commitment_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record({"slot": 5, "commitment": "maybe"}, 4)

    def test_skipped_with_blockhash_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record(
                {"slot": 5, "commitment": "skipped", "blockhash": "X"}, 4
            )

    def test_produced_without_parent_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record({"slot": 5, "commitment": "finalized"}, 4)

    def test_negative_tx_count_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_record(
                {"slot": 5, "parent": 4, "commitment": "finalized", "tx_count": -1}, 4
            )

    def test_unknown_keys_are_ignored(self):
        record = parse_record(
            {"slot": 5, "parent": 4, "commitment": "confirmed", "extra": {"a": 1}}, 1
        )
        self.assertEqual(record.commitment, "confirmed")


class ParseTextTests(unittest.TestCase):
    def test_blank_lines_are_ignored(self):
        text = "\n\n" + json.dumps(
            {"slot": 1, "commitment": "skipped"}
        ) + "\n\n"
        records, errors = parse_text(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(errors, [])

    def test_broken_lines_collect_errors_and_keep_going(self):
        text = (SAMPLES / "broken-lines.jsonl").read_text(encoding="utf-8")
        records, errors = parse_text(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(errors), 7)
        lines = [number for number, _ in errors]
        self.assertEqual(lines, [2, 3, 4, 5, 6, 7, 8])
        self.assertTrue(all(message.startswith("line ") for _, message in errors))


if __name__ == "__main__":
    unittest.main()
