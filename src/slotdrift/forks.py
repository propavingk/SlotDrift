"""Fork detection: duplicate slots, canonical ancestry and orphan segments.

The cluster can produce more than one block for the same slot, and roughly one
block in twenty never reaches finalization. This module makes both facts
visible in an export.

Canonical chain rule (deterministic, documented in docs/FORMAT.md):
1. The tip is the record with the strongest commitment; ties break to the
   highest slot, then to the lexicographically smallest blockhash.
2. From the tip, walk parent links through the best record per slot.
3. Every produced record outside that ancestry is orphaned and is grouped into
   segments by following parent links inside the orphaned set.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .model import SlotRecord


@dataclass
class OrphanSegment:
    start_slot: int
    end_slot: int
    length: int
    root_parent: int | None
    commitments: dict[str, int] = field(default_factory=dict)


@dataclass
class ForkReport:
    duplicate_slots: dict[int, list[str]] = field(default_factory=dict)
    orphan_segments: list[OrphanSegment] = field(default_factory=list)
    orphan_count: int = 0
    canonical_tip: int | None = None
    canonical_length: int = 0

    @property
    def findings(self) -> int:
        return len(self.duplicate_slots) + self.orphan_count


def _best(records: list[SlotRecord]) -> SlotRecord:
    """Strongest commitment, then highest slot, then smallest blockhash."""
    return max(
        records,
        key=lambda r: (r.rank, r.slot, tuple(-ord(c) for c in (r.blockhash or ""))),
    )


def find_forks(records: list[SlotRecord]) -> ForkReport:
    report = ForkReport()
    produced = [r for r in records if not r.skipped]
    if not produced:
        return report

    by_slot: dict[int, list[SlotRecord]] = {}
    for record in records:
        by_slot.setdefault(record.slot, []).append(record)

    for slot, group in sorted(by_slot.items()):
        hashes = sorted({r.blockhash for r in group if r.blockhash})
        if len(hashes) > 1:
            report.duplicate_slots[slot] = hashes

    best = {slot: _best([r for r in group if not r.skipped] or group) for slot, group in by_slot.items()}

    tip = _best(produced)
    report.canonical_tip = tip.slot

    def identity(r: SlotRecord) -> tuple[int, str]:
        return (r.slot, r.blockhash or "")

    canon: set[tuple[int, str]] = set()
    current: SlotRecord | None = tip
    while current is not None:
        key = identity(current)
        if key in canon:
            break
        canon.add(key)
        if current.parent is None:
            break
        current = best.get(current.parent)
    report.canonical_length = len({slot for slot, _ in canon})

    orphans: dict[int, SlotRecord] = {}
    for record in produced:
        if identity(record) not in canon:
            orphans.setdefault(record.slot, record)
    report.orphan_count = len(orphans)

    remaining = dict(orphans)
    while remaining:
        seed = remaining.pop(max(remaining))
        segment = [seed]
        parent = seed.parent
        while parent in remaining:
