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

    by_slot: dict[int, list[SlotRecord]] = defaultdict(list)
    for record in records:
        by_slot[record.slot].append(record)

    slots = sorted(by_slot)
    report.min_slot = slots[0]
    report.max_slot = slots[-1]
    report.window = report.max_slot - report.min_slot + 1

    present = set(slots)
    report.missing = [s for s in range(report.min_slot, report.max_slot + 1) if s not in present]

    for slot, group in by_slot.items():
        if len(group) > 1:
            report.duplicates[slot] = len(group)

    skipped_slots = {r.slot for r in records if r.skipped}
    report.skipped = sorted(skipped_slots)

    for slot, group in by_slot.items():
        for record in group:
            if record.skipped:
                continue
            parent = record.parent
            if parent is None:
                continue
            if parent not in present:
                if report.min_slot is not None and parent < report.min_slot:
                    # The parent is simply outside the exported window. A
                    # window always starts mid-chain, so this is expected.
                    continue
                report.parent_anomalies.append((slot, parent, "parent absent from export"))
                continue
            if parent in skipped_slots:
                report.parent_anomalies.append((slot, parent, "parent slot is marked skipped"))
                continue
            if parent >= slot:
                report.parent_anomalies.append((slot, parent, "parent not earlier than block"))
                continue
            if parent < slot - 1:
                bridge = range(parent + 1, slot)
                not_skipped = [s for s in bridge if s not in skipped_slots]
                if not_skipped:
                    report.parent_anomalies.append(
                        (slot, parent, "step over slots not marked skipped")
                    )

    leaders: dict[str, LeaderStats] = {}
    for record in records:
        if not record.leader:
            continue
        stats = leaders.setdefault(record.leader, LeaderStats(leader=record.leader))
        stats.scheduled += 1
        if record.skipped:
            stats.skipped += 1
        else:
            stats.produced += 1
    report.leaders = leaders
    return report
