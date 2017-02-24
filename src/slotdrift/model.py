"""Record model and parsing for slot exports.

The document format is line-oriented JSON (JSONL). Each line is one slot
record. Parsing is strict about the fields that carry meaning and liberal
about unknown keys so exports recorded by different harnesses stay readable.

Validation errors never abort a run. They are collected with their line
numbers and reported as findings, because a malformed export is itself a
continuity problem worth seeing.
"""
from __future__ import annotations

