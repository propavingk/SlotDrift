# Architecture

This document describes the modules that exist, the data flow between them,
and why the boundaries fall where they do. It was written by reading the
source, not by planning an ideal system.

## Shape of the program

slotdrift is a batch analyzer. One process reads one export, validates every
line, computes two independent analyses, renders one report, and exits with a
code that mirrors the findings. There is no server, no daemon, no state on
disk and no configuration file.

The Rust engine in `engine/` is a second implementation of the same
arithmetic. It exists to cross-check the Python rules, not to be called by
them. The two programs share a format contract (`docs/FORMAT.md`), not code.

## Python modules

```
src/slotdrift/
  __init__.py       __version__ only
  __main__.py       python -m slotdrift entry point
  model.py          SlotRecord, validation, JSONL parsing
  continuity.py     window analysis: gaps, skips, parent links, leaders
  forks.py          chain shape: duplicates, canonical ancestry, orphans
  report.py         deterministic text and JSON rendering
  cli.py            argparse, subcommands, exit codes, file IO
```

### model.py

Owns everything that can be said about a single line. `SlotRecord` is frozen,
so no later stage can accidentally mutate parsed data. `parse_record` applies
every validation rule in one place, and `parse_text` collects errors with
their line numbers instead of raising. That decision is fundamental: a
malformed export is a finding about the export, not a reason to stop reading
the file. A partially readable file still produces a full report, with the bad
lines listed at the end.

Validation is strict about fields that carry meaning (slot, parent,
commitment, tx_count ranges, skipped records carrying no blockhash) and
liberal about unknown keys, because exports recorded by different harnesses
add fields that this tool has no opinion about.

### continuity.py

Answers questions about the window as a sequence: which slot numbers have no
record, which slots claim more than one record, which parent links are
impossible, which slots were explicitly skipped, and how often each leader
skipped. Its only input is the record list; it never looks at blockhashes
beyond counting records per slot.
