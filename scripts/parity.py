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


def python_numbers(fixture: Path) -> dict:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "slotdrift", "analyze", str(fixture), "--format", "json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    payload = json.loads(result.stdout)
    continuity = payload["continuity"]
    forks = payload["forks"]
    duplicate_extra = sum(continuity["duplicates"].values()) - len(continuity["duplicates"])
    return {
        "records": payload["records"],
        "parse_errors": len(payload["parse_errors"]),
        "missing": len(continuity["missing"]),
        "duplicates": len(continuity["duplicates"]),
        "parent_anomalies": len(continuity["parent_anomalies"]),
        "skipped": len(continuity["skipped"]),
        "duplicate_slots": len(forks["duplicate_slots"]),
        "orphan_segments": len(forks["orphan_segments"]),
        "orphan_count": forks["orphan_segments"] and sum(
            s["length"] for s in forks["orphan_segments"]
        ),
        "findings": payload["findings"],
    }


def rust_numbers(fixture: Path) -> dict:
    result = subprocess.run(
        [
            "cargo",
            "run",
