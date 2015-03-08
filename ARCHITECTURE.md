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

The subtle rule here is the parent check. A block whose parent slot is marked
skipped is an anomaly, because a skipped slot produces no block and cannot be
an ancestor. A block that steps over produced slots without a skip record is
also an anomaly. A block whose parent falls just below the window is not an
anomaly: every captured window starts mid chain, so the boundary case is
normal and is documented rather than flagged.

### forks.py

Answers shape questions that are independent of gaps: where did two blocks
compete for one slot, which chain is canonical, and which produced blocks sit
outside it. Canonical selection is deterministic and documented in
`docs/FORMAT.md`: strongest commitment, then highest slot, then smallest
blockhash. From the chosen tip the walk follows parent links through the best
record per slot.

The orphan test compares identities, not slot numbers. Two blocks can claim
the same slot; if the loser is compared by slot number it silently disappears
from the orphan count. That exact bug was caught by the fixture in this
repository and is why `identity()` exists.

Orphan segments then group orphaned blocks by following parent links inside
the orphaned set, so a rival three-slot branch is reported as one segment with
a single attachment point rather than three unrelated blocks.

### report.py

Two renderers over one `Analysis` object. The text renderer is line oriented
and truncates every list with an explicit `... N more` line; the JSON renderer
mirrors the same numbers with sorted keys. Both are pure functions of the
analysis: no clock, no randomness, no environment reads. That is what makes
the two-run diff clean and what makes the parity script possible.

### cli.py

Argument parsing, subcommand dispatch, file reading, output writing, and the
mapping from findings to exit codes. The CLI contains no analysis logic on
purpose; everything it prints comes from the modules above.

## Rust engine

```
engine/src/lib.rs    parse_line, parse_text, analyze_continuity, find_forks
engine/src/main.rs   key: value output for the parity script
engine/tests/        integration tests over the same fixtures
```

The parser is a small top level JSON object reader. It is not a general JSON
parser and does not pretend to be one; it reads the fields this format defines
and skips nested containers in a balanced way. Value types are tracked
(strings versus other tokens) so `"slot": "5"` fails the same way in both
implementations.

The continuity and fork functions mirror the Python rules one for one,
including the boundary parent exception, the skipped parent rule, and the
identity based orphan test. `engine/tests/engine.rs` asserts the same designed
counts as the Python tests over the same fixture files.

## Data flow

```
export.jsonl
    |
    v
model.parse_text  ->  records[] + errors[]
    |                        |
    |                        +--> report parse error section
    v
continuity.analyze_continuity  ->  ContinuityReport
    |                                   |
    v                                   |
forks.find_forks (same records)  ->  ForkReport
    |                                   |
    +---------------+-------------------+
                    v
             report.Analysis
                    |
        +-----------+------------+
        v                        v
  render_text             render_json
        |                        |
        v                        v
   stdout or --output      stdout (--format json)
                    |
                    v
