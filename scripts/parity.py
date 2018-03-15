"""Cross-engine parity check.

Runs the Python implementation and the Rust engine on the same fixtures and
compares the numbers they report. This is a build-time check, not part of the
offline tool: the CLI itself never spawns processes.

Usage (from the repository root):

    python scripts/parity.py

Exit 0 when every fixture agrees, 1 otherwise.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ["clean-window.jsonl", "cluster-window.jsonl", "broken-lines.jsonl"]

KEYS = [
    "records",
    "parse_errors",
    "missing",
    "duplicates",
    "parent_anomalies",
    "skipped",
    "duplicate_slots",
    "orphan_segments",
    "orphan_count",
    "findings",
]
