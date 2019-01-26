"""End to end tests through the CLI entry point."""
from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

from slotdrift.cli import main

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def run(args: list[str]) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
