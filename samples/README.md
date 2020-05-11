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
