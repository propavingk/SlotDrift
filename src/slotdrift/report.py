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
        return self.continuity.findings + self.forks.findings + len(self.parse_errors)


def render_text(analysis: Analysis, limit: int | None = None) -> str:
    limit = analysis.list_limit if limit is None else limit
    c = analysis.continuity
    f = analysis.forks
    lines: list[str] = []
    lines.append("SLOTDRIFT REPORT")
    lines.append(f"input: {analysis.source}")
    window = "empty"
    if c.min_slot is not None:
