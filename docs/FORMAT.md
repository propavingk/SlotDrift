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
