"""Continuity analysis: gaps, skips, parent links and per-leader skip rates.

The mental model is a window of slots, min_slot..max_slot. Every slot in the
window should appear exactly once, either as a produced block or as an explicit
skipped record. Anything else is reported:

- missing: the slot number falls inside the window but no record exists.
- duplicate: more than one record claims the same slot number.
- parent anomaly: a produced block points at a parent that is absent from the
  export, points at itself or a later slot, or skips over slots that are not
  marked skipped.
- unexplained step: parent is below slot-1 and the intermediate slots are not
  all present as skipped records.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .model import SlotRecord


@dataclass
class LeaderStats:
    leader: str
    scheduled: int = 0
    skipped: int = 0
    produced: int = 0

    @property
    def skip_rate(self) -> float:
        if self.scheduled == 0:
            return 0.0
        return self.skipped / self.scheduled


@dataclass
class ContinuityReport:
    record_count: int = 0
    min_slot: int | None = None
    max_slot: int | None = None
    window: int = 0
    missing: list[int] = field(default_factory=list)
    duplicates: dict[int, int] = field(default_factory=dict)
    skipped: list[int] = field(default_factory=list)
    parent_anomalies: list[tuple[int, int | None, str]] = field(default_factory=list)
    leaders: dict[str, LeaderStats] = field(default_factory=dict)

    @property
    def findings(self) -> int:
        return (
            len(self.missing)
            + sum(self.duplicates.values()) - len(self.duplicates)
            + len(self.parent_anomalies)
        )


def analyze_continuity(records: list[SlotRecord]) -> ContinuityReport:
    report = ContinuityReport(record_count=len(records))
    if not records:
        return report
