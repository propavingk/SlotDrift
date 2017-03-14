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

    @property
    def skipped(self) -> bool:
        return self.commitment == "skipped"

    @property
    def rank(self) -> int:
        return RANK[self.commitment]


def _require_int(obj: dict, key: str, line: int, minimum: int | None = None) -> int:
    if key not in obj:
        raise FormatError(f"line {line}: missing required field '{key}'")
    value = obj[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise FormatError(f"line {line}: field '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise FormatError(f"line {line}: field '{key}' must be >= {minimum}")
    return value


def _optional_str(obj: dict, key: str, line: int) -> str | None:
    if key not in obj or obj[key] is None:
        return None
    value = obj[key]
    if not isinstance(value, str) or not value:
        raise FormatError(f"line {line}: field '{key}' must be a non-empty string")
    return value


def parse_record(obj: object, line: int) -> SlotRecord:
    """Validate one decoded JSON value into a SlotRecord."""
    if not isinstance(obj, dict):
        raise FormatError(f"line {line}: record must be a JSON object")
    slot = _require_int(obj, "slot", line, minimum=0)
    parent = None
    if "parent" in obj and obj["parent"] is not None:
        parent = _require_int(obj, "parent", line, minimum=0)
    if "commitment" not in obj:
        raise FormatError(f"line {line}: missing required field 'commitment'")
    commitment = obj["commitment"]
    if commitment not in COMMITMENTS:
        raise FormatError(
            f"line {line}: commitment must be one of {', '.join(COMMITMENTS)}"
        )
    tx_count = None
    if "tx_count" in obj and obj["tx_count"] is not None:
        tx_count = _require_int(obj, "tx_count", line, minimum=0)
    record = SlotRecord(
        slot=slot,
