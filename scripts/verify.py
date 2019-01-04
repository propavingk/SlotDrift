"""Executable quality gate for slotdrift.

Runs eight mechanical checks over the repository and prints one line per
check. Exit code 0 when every check passes, 1 otherwise.

    python scripts/verify.py

The checks implement the standing lessons for this project tree. They are
deliberately mechanical: a claim of correctness is the exit code of this
script, not a sentence in a report.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
