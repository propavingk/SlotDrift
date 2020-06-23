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

