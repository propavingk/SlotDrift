"""Tests for record parsing and validation."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from slotdrift.model import FormatError, parse_record, parse_text
