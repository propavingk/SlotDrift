"""Deterministic builder for the sample fixtures.

The two JSONL files next to this script are synthetic test vectors. They were
not captured from a cluster. This script rebuilds them byte for byte, so any
reader can inspect exactly how the data was produced:

- samples/clean-window.jsonl: 30 slots, one explicit pair of skipped slots, no
  findings. The first block's parent sits just below the window, which is the
  normal boundary case for any export.
- samples/cluster-window.jsonl: 61 slots that exercise every finding class:
  two explicit skips, a duplicated slot with a competing orphan branch, a
  later mini-reorg that orphans two blocks, and one parent that steps over
  produced slots without a skip record.

Run from the repository root:

    python samples/build_fixture.py

The script writes both files with LF endings and no trailing whitespace, and
it is idempotent: running it twice produces identical bytes.
"""
from __future__ import annotations

import json
from pathlib import Path

LEADERS = [
    "7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2",
    "GdnSyH3YtwcxFvQrVVJMm1tr2ojebqjFEuiEcWm2mSx5",
    "4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T",
    "CvSb7Md3jUWLtR9jRUnL2t9RzZ9k6NQmE7u8vCqQv7fE",
    "9xQeWvG816bUx9EPfCDsRkHr2D3y6dM4nA8bV5cL7pQt",
    "3VfJ8kMzY2nQpR6tWsLxE1uHcD4yA9bG7eN5mK2qSvT",
    "Fq6zXjB4nM8vC2rT5yH7kL9pQ1wE3sD6gA4uJ0oI8bNx",
    "Hm4kP9sV2xC7zQ1nB5yR8tL3wE6uA2jD9gF4vK7oM1qS",
]


def leaders_for(index: int) -> str:
    return LEADERS[index % len(LEADERS)]


def record(slot, parent, commitment, leader, blockhash=None, tx_count=None):
    obj = {"slot": slot, "commitment": commitment, "leader": leader}
    if parent is not None:
        obj["parent"] = parent
    if blockhash is not None:
        obj["blockhash"] = blockhash
    if tx_count is not None:
        obj["tx_count"] = tx_count
    return obj


def write_jsonl(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(obj, separators=(",", ":"), sort_keys=True) for obj in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_clean() -> list[dict]:
    base = 100_000_000
    records: list[dict] = []
    last_produced: int | None = None
    for offset in range(30):
        slot = base + offset
        if offset in (10, 11):
            records.append(record(slot, None, "skipped", leaders_for(offset)))
            continue
        parent = base - 1 if last_produced is None else last_produced
        records.append(
            record(slot, parent, "finalized", leaders_for(offset),
                   blockhash=f"Clean{offset:02d}hashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", tx_count=120 + offset)
        )
        last_produced = slot
    return records


def build_cluster() -> list[dict]:
    base = 320_400_000
    records: list[dict] = []

    def produced(slot, parent, blockhash, commitment="finalized", tx_count=700):
        records.append(record(slot, parent, commitment, leaders_for(slot - base),
                              blockhash=blockhash, tx_count=tx_count))

    def skipped(slot):
        records.append(record(slot, None, "skipped", leaders_for(slot - base)))

    # Streak one: blocks 0..14, then skips at 15 and 16.
    produced(base + 0, base - 1, "StreakA00hashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    for offset in range(1, 15):
        produced(base + offset, base + offset - 1,
                 f"StreakA{offset:02d}hashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    skipped(base + 15)
    skipped(base + 16)

    # Block 17 bridges the two skipped slots and reports parent 14.
    produced(base + 17, base + 14, "StreakA17hashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    for offset in range(18, 33):
        produced(base + offset, base + offset - 1,
                 f"StreakA{offset:02d}hashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

    # Skip at 33, block 34 bridges to parent 32.
    skipped(base + 33)
