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
