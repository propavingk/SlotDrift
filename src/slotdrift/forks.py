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


