# Sample fixtures

Every file here is a synthetic test vector. None of it was captured from a
live cluster. `build_fixture.py` rebuilds `clean-window.jsonl` and
`cluster-window.jsonl` byte for byte, so the construction is inspectable and
reproducible:

```bash
python samples/build_fixture.py
clean-window.jsonl: 30 records
cluster-window.jsonl: 64 records
```

## clean-window.jsonl

30 records, slots 100000000 to 100000029. All blocks are finalized, two slots
(100000010 and 100000011) carry explicit skipped records, and the block at
100000012 reports parent 100000009 because a skipped slot is never an
ancestor. The first block's parent sits just below the window, which is the
normal boundary case for a captured window. Expected result: zero findings,
exit code 0.

## cluster-window.jsonl

64 records, slots 320400000 to 320400060. Built to exercise every finding
class in one window:

- two explicit skips at 320400015 and 320400016, bridged by the block at
  320400017 whose parent is 320400014;
- one more skip at 320400033;
- a duplicated slot at 320400040 with two competing blockhashes. The rival
  branch occupies slots 320400040 to 320400042 and is orphaned when the
  finalized branch wins;
- a later mini-reorg where blocks 320400056 and 320400057 are orphaned by the
  branch that continues from 320400055, and block 320400058 steps over both
  without a skip record, which is a separate parent anomaly.

Expected result: 3 duplicate slots, 2 orphan segments (3 slots and 2 slots),
1 parent anomaly, 12 findings in total, exit code 1.

## broken-lines.jsonl

Nine lines, seven of them deliberately invalid, covering every validation
rule: invalid JSON, missing commitment, unknown commitment, a skipped slot
carrying a blockhash, a produced slot without a parent, a negative slot, and a
negative transaction count. Two valid records surround the bad lines to prove
that parsing continues and the good data still lands in the report. Expected
result: 2 records and 7 parse errors, exit code 1.

## Why synthetic

Producing an honest fixture of this shape requires either a mainnet capture
with a logged reorg (unlikely to hit every case in a small window) or a
constructed vector. Constructed vectors are labelled as such here rather than
presented as captured data. If you have a real capture that shows a fork, the
tool will read it; the format is documented in `docs/FORMAT.md`.
