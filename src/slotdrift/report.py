"""Deterministic text and JSON rendering.

The text report is line oriented so two runs diff cleanly in git. Lists are
truncated with an explicit `... N more` line, never silently cut. Rendering
never depends on wall-clock time or randomness.
"""
from __future__ import annotations

from dataclasses import dataclass

from .continuity import ContinuityReport
from .forks import ForkReport

LIST_LIMIT = 10


@dataclass
class Analysis:
    source: str
    record_count: int
    parse_errors: list[tuple[int, str]]
    continuity: ContinuityReport
    forks: ForkReport
    list_limit: int = LIST_LIMIT

    @property
    def findings(self) -> int:
