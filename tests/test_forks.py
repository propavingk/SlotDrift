"""Tests for fork detection and orphan segmentation."""
from __future__ import annotations

import unittest
from pathlib import Path

from slotdrift.forks import find_forks
from slotdrift.model import parse_file, parse_text

