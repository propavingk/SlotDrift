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
