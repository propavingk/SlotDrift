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

