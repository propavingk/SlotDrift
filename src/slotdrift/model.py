"""Record model and parsing for slot exports.

The document format is line-oriented JSON (JSONL). Each line is one slot
record. Parsing is strict about the fields that carry meaning and liberal
about unknown keys so exports recorded by different harnesses stay readable.

Validation errors never abort a run. They are collected with their line
numbers and reported as findings, because a malformed export is itself a
continuity problem worth seeing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

COMMITMENTS = ("processed", "confirmed", "finalized", "skipped")

# Higher rank means a stronger commitment. Skipped slots carry rank -1 because
# they produce no block and cannot anchor a chain.
RANK = {"skipped": -1, "processed": 0, "confirmed": 1, "finalized": 2}


class FormatError(ValueError):
    """Raised when a single record fails validation."""


@dataclass(frozen=True)
class SlotRecord:
    slot: int
    parent: int | None
    commitment: str
    leader: str | None
    blockhash: str | None
    tx_count: int | None
    line: int
