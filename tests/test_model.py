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
