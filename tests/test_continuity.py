"""Tests for continuity analysis."""
from __future__ import annotations

import unittest
from pathlib import Path

from slotdrift.continuity import analyze_continuity
from slotdrift.model import parse_file, parse_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


