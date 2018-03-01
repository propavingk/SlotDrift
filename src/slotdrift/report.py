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
        window = f"{c.min_slot}..{c.max_slot}"
    lines.append(
        f"records: {analysis.record_count} | window: {window} | parse errors: {len(analysis.parse_errors)}"
    )
    lines.append("")
    lines.append("CONTINUITY")
    lines.append(f"  missing slots: {len(c.missing)}")
    lines.append(f"  duplicate slots: {len(c.duplicates)}")
    lines.append(f"  parent anomalies: {len(c.parent_anomalies)}")
    lines.append(f"  skipped slots: {len(c.skipped)}")
    lines.append("")
    lines.append(f"GAPS (first {limit})")
    for slot in c.missing[:limit]:
        lines.append(f"  slot {slot}")
    if len(c.missing) > limit:
        lines.append(f"  ... {len(c.missing) - limit} more")
    if not c.missing:
        lines.append("  none")
    lines.append("")
    lines.append(f"PARENT ANOMALIES (first {limit})")
    for slot, parent, reason in c.parent_anomalies[:limit]:
        lines.append(f"  slot {slot} parent {parent}: {reason}")
    if len(c.parent_anomalies) > limit:
        lines.append(f"  ... {len(c.parent_anomalies) - limit} more")
    if not c.parent_anomalies:
        lines.append("  none")
    lines.append("")
    lines.append(f"FORKS (first {limit})")
    for slot, hashes in sorted(f.duplicate_slots.items())[:limit]:
        lines.append(f"  duplicate slot {slot}: {len(hashes)} blockhashes")
    if len(f.duplicate_slots) > limit:
        lines.append(f"  ... {len(f.duplicate_slots) - limit} more duplicate slots")
    for segment in f.orphan_segments[:limit]:
        mix = ", ".join(f"{k} {v}" for k, v in sorted(segment.commitments.items()))
        lines.append(
            "  orphan segment "
