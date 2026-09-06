# Format contract

This document specifies the input format, every validation rule, the text
report sections, the JSON report fields, the exit codes, and the deterministic
rules the analysis follows. It is the contract between the two implementations
in this repository (Python in `src/slotdrift/`, Rust in `engine/`) and between
the tool and anyone writing an export for it.

## Input: one JSON object per line

The input file is JSONL. Blank lines are ignored. Every other line must decode
as a JSON object. The fields:

| Field | Type | Required | Rules |
|---|---|---|---|
| `slot` | integer | yes | `>= 0` |
| `parent` | integer or null | for produced slots | `>= 0`; required when `commitment` is not `skipped` |
| `commitment` | string | yes | one of `processed`, `confirmed`, `finalized`, `skipped` |
| `leader` | string or null | no | non-empty when present |
| `blockhash` | string or null | no | non-empty when present; forbidden on a `skipped` record |
| `tx_count` | integer or null | no | `>= 0` |

Unknown keys are ignored. A `null` value is treated as absent for the optional
fields. Strings are required to be strings: `"slot": "5"` is invalid, and so
is an empty `leader` or `blockhash`.

A produced block (any commitment except `skipped`) must carry a parent. A
skipped slot must not carry a blockhash, because no block exists for it.

### Validation errors

Every invalid line is collected with its line number and reported under
`PARSE ERRORS`. Parsing continues. The observed error messages are:

| Condition | Message |
|---|---|
| not a JSON object or a JSON syntax error | `line N: invalid JSON (...)` or `line N: record must be a JSON object` |
| missing `slot` | `line N: missing required field 'slot'` |
| negative or non-integer `slot` | `line N: field 'slot' must be an integer` / `must be >= 0` |
| missing `commitment` | `line N: missing required field 'commitment'` |
| unknown `commitment` | `line N: commitment must be one of skipped, processed, confirmed, finalized` |
| produced record without a parent | `line N: a produced slot must carry a parent` |
| skipped record with a blockhash | `line N: a skipped slot cannot carry a blockhash` |
| negative `tx_count` | `line N: field 'tx_count' must be >= 0` |

## Deterministic rules

These rules are implemented twice, once per language, and the parity script
asserts that both implementations agree on every fixture.

### Window

`min_slot` and `max_slot` are the smallest and largest slot numbers present,
counting skipped records. Every slot number in between with no record is a
`missing` slot.

### Duplicate slots

A slot number with more than one record is a duplicate. The continuity section
counts duplicate records; the fork section counts duplicate slots that show
more than one distinct blockhash.

### Parent anomalies

A produced block is anomalous when:

- its parent is absent from the export and the parent is inside the window;
- its parent is not earlier than the block itself;
- its parent slot is marked skipped;
- its parent is below the previous slot and the slots in between are not all
  marked skipped (a step over produced slots).

A parent below the window is not an anomaly: a window always starts mid chain.

### Canonical chain

1. The tip is the produced record with the strongest commitment. Ties break to
   the highest slot, then to the lexicographically smallest blockhash.
2. From the tip, walk parent links through the best record per slot, where
   "best" uses the same ordering.
3. The walk ends at a slot with no parent in the export.

### Orphaned blocks and segments

A produced block is orphaned when its identity `(slot, blockhash)` is not on
the canonical walk. Identity, not slot number: a block that loses a duplicate
slot is orphaned even though the slot number itself is canonical.

Orphaned blocks are grouped into segments by following parent links inside the
orphaned set. A segment reports its first and last slot, its length, its
attachment point (`root_parent`), and how many of its blocks were `processed`
or `finalized`.

### Leader statistics

For each `leader` value: `scheduled` counts every record, `skipped` counts
the skipped ones, `produced` the rest, and `skip_rate = skipped / scheduled`
as a fraction. Records without a leader field are not attributed.

## Text report

The `analyze` command prints, in order:

| Section | Content |
|---|---|
| header | tool name, input path, records, window, parse error count |
| `CONTINUITY` | counts for missing, duplicate, parent anomaly and skipped slots |
| `GAPS` | the first N missing slot numbers, then `... N more` |
| `PARENT ANOMALIES` | the first N as `slot S parent P: reason` |
| `FORKS` | duplicate slots, then orphan segments with attachment and mix |
| `LEADERS` | top five by skip rate, `skipped x/y (p.p%)` |
| `PARSE ERRORS` | the first N error messages verbatim |
| `FINDINGS` | the total count used for the exit code |

N defaults to 10 and is set by `--limit`. Lists are never silently truncated:
a cut list always prints how many entries were omitted.

## JSON report

`analyze --format json` prints one object. Field by field:

| Field | Type | Meaning |
|---|---|---|
| `input` | string | the path as given on the command line |
| `records` | int | accepted records |
| `window` | object | `min`, `max`, `size` (null when the export is empty) |
| `findings` | int | same total as the text report |
| `continuity.missing` | array of int | missing slot numbers |
| `continuity.duplicates` | object | slot number (string key) to record count |
| `continuity.parent_anomalies` | array | objects with `slot`, `parent`, `reason` |
| `continuity.skipped` | array of int | skipped slot numbers |
| `forks.canonical_tip` | int or null | the tip slot |
| `forks.canonical_length` | int | distinct canonical slots |
| `forks.duplicate_slots` | object | slot number (string key) to sorted blockhashes |
| `forks.orphan_segments` | array | objects with `start_slot`, `end_slot`, `length`, `root_parent`, `commitments` |
| `leaders` | object | leader name to `scheduled`, `skipped`, `produced`, `skip_rate` |
| `parse_errors` | array | objects with `line` and `message` |

Adding keys is a minor change. Renaming or removing a key needs a changelog
entry, because consumers diff this output in CI.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | no findings: no missing slots, no parent anomalies, no duplicates, no orphans, no parse errors |
| 1 | findings present |
| 2 | usage error: missing or unreadable input file |

Skipped slots are not findings. A cluster that skips a slot is behaving
normally, and a report that treated every skip as a problem would be noise.

## Determinism guarantees

- Two runs over the same input produce byte-identical output.
- JSON output uses stable key order and sorted collections.
- Nothing in the output depends on wall-clock time, locale, or randomness.
- The Rust engine prints `key: value` lines for the same numbers so
  `scripts/parity.py` can compare implementations without shared code.
