<p align="center">
  <img src="docs/assets/banner.svg" alt="slotdrift banner: the 61-slot sample window as one cell per slot, with skipped slots pale, orphaned slots in moss, a rust bracket under the duplicated slots, and the real report line records 64, findings 12 being typed below" width="640">
</p>

# SlotDrift

Slot continuity and fork analysis for captured Solana slot records.

Feed it a JSONL export of slot records and it tells you what the window looks
like as a chain: which slots are missing, which produced blocks sit outside
the canonical chain, where two blocks competed for one slot, which parent
links are impossible, and how often each leader skipped. It is offline,
deterministic, and runs in one pass with no dependencies beyond the standard
library.

<details>
<summary>Contents</summary>

- [The problem](#the-problem)
- [What it does](#what-it-does)
- [Quick start](#quick-start)
- [A real run: clean window](#a-real-run-clean-window)
- [A real run: cluster window](#a-real-run-cluster-window)
- [Commands](#commands)
- [The input format](#the-input-format)
- [A worked walkthrough](#a-worked-walkthrough)
- [Findings and what to do about them](#findings-and-what-to-do-about-them)
- [Exit codes and CI integration](#exit-codes-and-ci-integration)
- [Determinism and diffing two runs](#determinism-and-diffing-two-runs)
- [The second engine](#the-second-engine)
- [Design decisions](#design-decisions)
- [Repository layout](#repository-layout)
- [Tests and verification](#tests-and-verification)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Glossary](#glossary)
- [The mark](#the-mark)
- [License](#license)

</details>

---

## The problem

Solana slots are a clock. Each slot is a short window in which one leader is
scheduled to produce a block. When the leader is unavailable, or when the
cluster abandons a fork for a better alternative, the slot produces nothing
and is recorded as skipped. The next produced block does not point at the
skipped slot; it points at the most recent block that actually exists. About
one block in twenty never reaches finalization, so forks are not an anomaly in
this chain, they are weather.

That makes a captured window hard to read by eye. Two things in particular are
easy to miss:

1. A gap in the slot numbering is not automatically a problem. Some gaps are
   explicit skips, some are records your export simply did not capture, and
   the two mean very different things.
2. A missing record can silently change the shape of the chain. If the block
   at slot 100 is absent from the export, then the block at slot 101 pointing
   at parent 99 looks like a two-slot detour, and a naive check reports an
   anomaly that is really an export limitation.

slotdrift reads the window the way the chain reads it: produced blocks are
connected through their parent links, skipped slots are explicit facts, and
anything that does not fit that picture is reported with the reason.

---

## What it does

- Validates every line and reports bad ones with line numbers instead of
  aborting on the first.
- Computes the window, missing slots, duplicate slots, parent anomalies and
  skipped slots.
- Detects duplicate slots by distinct blockhash, and splits the window into a
  canonical chain and orphaned segments using deterministic rules.
- Attributes skips per leader with a scheduled, skipped, produced and skip
  rate summary.
- Emits a line-oriented text report or a JSON report with fixed field names.
- Cross-checks every rule with a second implementation in Rust. The two
  engines are compared on every fixture by `scripts/parity.py`.

<p align="center">
  <img src="docs/assets/continuity.svg" alt="One cell per slot in the sample window: finalized slots in paper, skipped slots pale, slots whose rival block was orphaned in moss, and a rust bracket under the three duplicated slots at 320400040 to 320400042" width="592">
</p>

The picture above is built from the actual numbers in this repository's
fixtures: 61 slots, 64 records, 2 explicit skips, 3 duplicated slots, 2
orphan segments, 1 parent anomaly, 12 findings.

---

## Quick start

There is nothing to install for the Python core. Clone the repository and run
the module directly:

```bash
export PYTHONPATH=src
python -m slotdrift analyze samples/cluster-window.jsonl
```

Or install the console script with `pip install .` and run
`slotdrift analyze samples/cluster-window.jsonl`.

The Rust engine builds with a stable toolchain and no external crates:

```bash
cargo run --manifest-path engine/Cargo.toml -- analyze samples/cluster-window.jsonl
```

---

## A real run: clean window

The clean fixture has 30 records, two skipped slots, and no structural
problems. This is the actual output, captured from the command shown:

```bash
PYTHONPATH=src python -m slotdrift analyze samples/clean-window.jsonl
```

```text
SLOTDRIFT REPORT
input: samples\clean-window.jsonl
records: 30 | window: 100000000..100000029 | parse errors: 0

CONTINUITY
  missing slots: 0
  duplicate slots: 0
  parent anomalies: 0
  skipped slots: 2

GAPS (first 10)
  none

PARENT ANOMALIES (first 10)
  none

FORKS (first 10)
  none

LEADERS (top 5 by skip rate)
  4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T  skipped 1/4 (25.0%)
  CvSb7Md3jUWLtR9jRUnL2t9RzZ9k6NQmE7u8vCqQv7fE  skipped 1/4 (25.0%)
  3VfJ8kMzY2nQpR6tWsLxE1uHcD4yA9bG7eN5mK2qSvT  skipped 0/4 (0.0%)
  7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2  skipped 0/4 (0.0%)
  9xQeWvG816bUx9EPfCDsRkHr2D3y6dM4nA8bV5cL7pQt  skipped 0/4 (0.0%)

PARSE ERRORS (first 10)
  none

FINDINGS: 0
```

The exit code is 0. Note what is not reported: the two skipped slots do not
count as findings, because a skipped slot is normal cluster behavior. They are
recorded and visible, not flagged.

---

## A real run: cluster window

The cluster fixture is built to exercise every finding class. The command,
then the full capture collapsed so this page stays scannable:

```bash
PYTHONPATH=src python -m slotdrift analyze samples/cluster-window.jsonl
```

<details>
<summary>Full report for the cluster window (12 findings)</summary>

```text
SLOTDRIFT REPORT
input: samples\cluster-window.jsonl
records: 64 | window: 320400000..320400060 | parse errors: 0

CONTINUITY
  missing slots: 0
  duplicate slots: 3
  parent anomalies: 1
  skipped slots: 3

GAPS (first 10)
  none

PARENT ANOMALIES (first 10)
  slot 320400058 parent 320400055: step over slots not marked skipped

FORKS (first 10)
  duplicate slot 320400040: 2 blockhashes
  duplicate slot 320400041: 2 blockhashes
  duplicate slot 320400042: 2 blockhashes
  orphan segment 320400040..320400042 (3 slots, attached at parent 320400039, processed 3)
  orphan segment 320400056..320400057 (2 slots, attached at parent 320400055, finalized 2)

LEADERS (top 5 by skip rate)
  Hm4kP9sV2xC7zQ1nB5yR8tL3wE6uA2jD9gF4vK7oM1qS  skipped 1/7 (14.3%)
  7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2  skipped 1/9 (11.1%)
  GdnSyH3YtwcxFvQrVVJMm1tr2ojebqjFEuiEcWm2mSx5  skipped 1/9 (11.1%)
  3VfJ8kMzY2nQpR6tWsLxE1uHcD4yA9bG7eN5mK2qSvT  skipped 0/7 (0.0%)
  4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T  skipped 0/9 (0.0%)

PARSE ERRORS (first 10)
  none

FINDINGS: 12
```

</details>

The exit code is 1. Read the report from the bottom up: 12 findings, made of
3 duplicate slots (2 extra records beyond the first per slot), 1 parent
anomaly, and the two orphan segments carrying 5 blocks between them.

---

## Commands

| Command | What it prints | Exit codes |
|---|---|---|
| `slotdrift version` (also `--version`) | `slotdrift <version>` | 0 |
| `slotdrift analyze PATH [--format text\|json] [--limit N] [--output FILE]` | the full report | 0 clean, 1 findings, 2 usage |
| `slotdrift leaders PATH` | one line per leader with skip rate | 0, or 1 when parse errors exist |
| `slotdrift forks PATH` | duplicate slots and orphan segments only | 0, or 1 when findings exist |

`--limit N` sets how many entries each list section prints before the explicit
`... N more` line. The default is 10, and a list is never silently truncated.

---

## The input format

One JSON object per line. The fields, their types and their rules:

| Field | Type | Required | Rules |
|---|---|---|---|
| `slot` | integer | yes | 0 or greater |
| `parent` | integer or null | for produced slots | 0 or greater; required unless the record is skipped |
| `commitment` | string | yes | `processed`, `confirmed`, `finalized` or `skipped` |
| `leader` | string or null | no | non-empty when present |
| `blockhash` | string or null | no | non-empty when present; forbidden on a skipped record |
| `tx_count` | integer or null | no | 0 or greater |

Unknown keys are ignored, so exports with extra fields stay readable. Bad
lines are collected with their line numbers and reported under `PARSE ERRORS`;
parsing continues and the good records still produce a full report. The
complete contract, including the JSON report fields, is in
[docs/FORMAT.md](docs/FORMAT.md).

The fixtures in `samples/` are synthetic test vectors, and
[samples/README.md](samples/README.md) says so explicitly and documents how
each one is constructed. `samples/build_fixture.py` rebuilds them byte for
byte.

---

## A worked walkthrough

Follow one record from the cluster fixture, the block that bridges the first
pair of skips. In `samples/cluster-window.jsonl` the record for slot
320400017 carries `parent: 320400014`, `commitment: finalized` and a leader.

**Step 1, validation.** Slot is an integer, parent is an integer,
commitment is a known value, leader is a non-empty string, and the record is
produced so a parent is required and present. The record is accepted.

**Step 2, continuity.** The window is 320400000 to 320400060. Slot 320400017
is present, so it is not missing. Its parent, 320400014, is also present. The
parent is below the previous slot by more than one, so the analyzer looks at
the slots in between, 320400015 and 320400016. Both are present as explicit
skipped records, so this is the normal post-skip bridge and no anomaly is
recorded. If only one of them had been skipped, the other would be an
unexplained gap and the block would be flagged.

**Step 3, forks and leaders.** The record is produced and its identity is on
the canonical walk, so it is not orphaned and it has no duplicate. Its leader
gets one more `scheduled` and one more `produced` in the per-leader summary;
a skipped record at that leader would add to `skipped` instead.

**Step 4, report.** The record itself never appears in the report, because
nothing about it is a finding. Records appear only through the counts they
contribute. That is the design: the report is a list of problems and
summaries, not a dump of the input.

---

## Findings and what to do about them

| Finding | What it means | What to do |
|---|---|---|
| missing slots | slot numbers inside the window with no record at all | check the exporter first; a capture gap is more common than a real hole |
| duplicate slots | two or more records claim one slot, usually with different blockhashes | expected during a fork; check which branch finalized before treating it as a problem |
| parent absent from export | a block points at a parent that is inside the window but not in the file | the export is incomplete and the chain shape near that block cannot be trusted |
| parent not earlier than block | the parent slot is equal to or above the block itself | corruption in the export; the record cannot be part of a chain |
| parent slot is marked skipped | a block claims a skipped slot as its ancestor | inconsistent data; a skipped slot produces no block to be a parent |
| step over slots not marked skipped | a block skips over produced slots with no skip records | either a missing skip record or a real fork; look at the blockhash trail |
| orphan segment | a run of blocks outside the canonical walk | these are the blocks the cluster abandoned, or the ones your export did not follow |
| parse error | a line failed validation | fix the exporter; the message includes the line number and the rule |

---

## Exit codes and CI integration

| Code | Meaning |
|---|---|
| 0 | no findings |
| 1 | findings present |
| 2 | usage error: missing or unreadable input |

A CI job that captures a window and wants to fail on structural problems can
call the tool directly, because the exit code already encodes the answer:

```bash
PYTHONPATH=src python -m slotdrift analyze window.jsonl --format json > report.json
```

The JSON output is stable, so `report.json` can be committed as a build
artifact, attached to a ticket, or diffed between runs. Adding keys is a minor
change; renaming or removing one needs a changelog entry, because consumers
depend on them.

---

## Determinism and diffing two runs

Two runs over the same input produce byte-identical output. Nothing depends on
wall-clock time, locale, or hash ordering that is not sorted. That makes the
report diffable in git:

```bash
PYTHONPATH=src python -m slotdrift analyze window.jsonl --output before.txt
PYTHONPATH=src python -m slotdrift analyze window.jsonl --output after.txt
git diff --no-index before.txt after.txt
```

The interesting diffs are usually a changed `FINDINGS:` line and new entries
in `ORPHAN SEGMENTS`. Because every list is sorted and every count is derived,
a diff of two reports reads like a diff of two chain states.

---

## The second engine

`engine/` is an independent implementation of the same arithmetic in Rust,
standard library only. It exists to cross-check the rules, not to be faster or
smaller. The two programs share the format contract, not code.

| | Python core | Rust engine |
|---|---|---|
| Location | `src/slotdrift/` | `engine/src/` |
| Entry point | `python -m slotdrift` | `slotdrift-engine` |
| Output | text report, JSON report | `key: value` lines for parity |
| Tests | 39 unit tests | 5 integration tests |
| Dependencies | none | none |

```bash
cargo run --manifest-path engine/Cargo.toml -- analyze samples/cluster-window.jsonl
```

It prints one `key: value` line per number, ending with `findings: 12` on the
cluster fixture, which is the same total the Python report shows.

The parity script runs both engines on every fixture and compares the numbers:

```bash
python scripts/parity.py
```

```text
clean-window.jsonl: OK
cluster-window.jsonl: OK
broken-lines.jsonl: OK
parity: 3/3 fixtures agree
```

The parity check earned its keep during development. The first version of the
Rust parser did not validate `tx_count`, so it accepted a line the Python
parser rejected, and the fixture comparison refused the disagreement
immediately. That is the entire reason the second engine exists.

---

## Design decisions

**Canonical chain by commitment rank, then slot, then blockhash.** The
alternative was to follow the export order and treat the last record per slot
as the winner. Export order is a property of the exporter, not the chain, and
it makes the report unstable across exports of the same window. The
documented ordering is arbitrary in its tie-breaks but deterministic, and
determinism is what a report needs.

**Orphans compared by identity, not by slot number.** The first version
compared slots, which silently absorbed the losing block of a duplicate slot
into the canonical set. Two blocks at slot 40 with different hashes are two
different blocks, and the loser is an orphan. The fixture caught it, and
`tests/test_forks.py` locks the behavior in.

**A parent below the window is not an anomaly.** Every captured window starts
mid chain. Flagging the first block of every export would train users to
ignore the anomaly list, which is worse than having no list.

**Skipped slots are recorded, not flagged.** Skips are how the cluster
handles an absent leader. They belong in the report as facts and in the
per-leader summary as rates, but treating each one as a finding would drown
the real problems.

**A second implementation instead of shared code.** The alternative was to
generate one implementation from the other or extract a shared library. Both
would preserve bugs as easily as they preserve behavior. Two independent
readings of the same written contract catch interpretation errors, which are
the errors that actually happen.

**JSON keys are a contract.** The alternative was to call the JSON output
experimental and change it freely. CI consumers need stable keys, and a
contract that is written down is the only kind that can be kept.

---

## Repository layout

```
slotdrift/
  README.md                      this document
  LICENSE                        MIT
  CHANGELOG.md                   release history
  CONTRIBUTING.md                setup, checks, standing rules
  SECURITY.md                    threat model and reporting
  CODE_OF_CONDUCT.md             Contributor Covenant 2.1
  ARCHITECTURE.md                module by module, data flow, boundaries
  CITATION.cff                   citation metadata
  Makefile                       help, test, verify, run, parity, clean
  .editorconfig                  editor defaults
  .gitattributes                 LF enforcement, text classification
  .gitignore                     caches and build output
  pyproject.toml                 package metadata and console script
  docs/
    FORMAT.md                    the input and output contract
    assets/logo.svg              wordmark
    assets/continuity.svg        the cluster window as a graphic
  engine/
    Cargo.toml                   Rust crate, no dependencies
    src/lib.rs                   parser and both analyses
    src/main.rs                  key: value output for parity
    tests/engine.rs              integration tests over the fixtures
  samples/
    README.md                    how each fixture was built
    build_fixture.py             deterministic fixture builder
    clean-window.jsonl           no findings, exit 0
    cluster-window.jsonl         every finding class, exit 1
    broken-lines.jsonl           validation errors, exit 1
  scripts/
    parity.py                    compares both engines on every fixture
    verify.py                    the eight mechanical quality checks
  src/slotdrift/
    __init__.py                  version
    __main__.py                  module entry point
    cli.py                       argparse, subcommands, exit codes
    continuity.py                window, gaps, parents, leaders
    forks.py                     duplicates, canonical chain, orphans
    model.py                     record model and validation
    report.py                    deterministic text and JSON renderers
  tests/
    test_cli.py                  end to end exit codes and formats
    test_continuity.py           window and parent rules
    test_forks.py                duplicates, orphans, identity
    test_model.py                validation and error collection
  .github/
    PULL_REQUEST_TEMPLATE.md     checklists tied to the real checks
    ISSUE_TEMPLATE/              bug and feature forms
    workflows/ci.yml             python, rust and parity jobs
```

---

## Tests and verification

The suite is run before every push, and the numbers below are the actual
results from this repository:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

```text
Ran 39 tests in 0.009s

OK
```

`cargo test --manifest-path engine/Cargo.toml` reports 5 passed, 0 failed.

What the tests actually cover:

| Area | Examples |
|---|---|
| validation | every rejection rule has a failing line, and unknown keys are ignored |
| continuity | missing slots, duplicates, boundary parents, skipped parents, step overs, leader rates, empty exports |
| forks | designed counts on the cluster fixture, identity based orphan detection, skips are not forks |
| CLI | exit codes 0, 1 and 2, JSON shape, list truncation, subcommand output |

The eight mechanical checks, including em dash and SVG label overlap:

```bash
python scripts/verify.py
```

```text
[pass] svg parse: 2 files well formed
[pass] svg filters: none present
[pass] svg comments: no illegal double hyphen
[pass] em dash: none in any text file
[pass] readme attributes: no pandoc style blocks
[pass] readme terms: no banned marketing terms
[pass] svg metadata: viewBox, role, title, desc present
[pass] svg labels: no overlapping labels on shared baselines
verify: 8 checks, 0 failures
```

---

## Limitations

- **No streaming.** The whole export is held in memory, and the window loop
  walks every slot between the minimum and the maximum. A sparse window of ten
  million slots costs proportionally.
- **Canonical selection is a heuristic.** It is deterministic and documented,
  but it is not the cluster's fork choice. It decides which branch a report
  treats as primary; it does not decide which branch the network chose.
- **No leader schedule.** Skip attribution uses the leader field in the
  export. The tool does not compute who was supposed to lead a slot.
- **Blockhashes are strings, and consistency is not provenance.** Any
  non-empty string is accepted, and a clean report means the export is
  internally coherent. It says nothing about whether the export is truthful or
  current.
- **One window per run.** Comparing two windows is done by diffing two report
  files, not by a built-in comparison mode.

---

## Roadmap

No dates, and nothing here is promised. In rough priority order:

- a `--summary` mode that prints only the counts, for dashboards;
- optional per-epoch grouping of skip rates;
- a strict mode that also exits nonzero on skips above a threshold;
- sample fixtures contributed from real captures, with provenance noted.

---

## Glossary

| Term | Meaning |
|---|---|
| slot | a short, numbered window in which one leader may produce a block |
| skipped slot | a slot that produced no block, because the leader was unavailable or the fork was abandoned |
| blockhash | the identifier of a produced block; two blocks can share a slot, not a hash |
| parent | the previous produced block on this branch, which may be several slots back when slots were skipped |
| commitment | the strength of a block's acceptance: processed, confirmed, finalized |
| duplicate slot | a slot with more than one produced block, usually during a fork |
| orphan | a produced block outside the canonical walk |
| orphan segment | a run of orphaned blocks connected by parent links, with one attachment point |
| window | the range from the smallest to the largest slot present in the export |
| finding | a condition the report counts toward the exit code |

---

## The mark

The wordmark is the project name set in one weight, split at the compound
boundary: `slot` in ink and `drift` in rust. The split is the single
typographic decision, and it means something: the slot is the neutral clock,
and the drift is the divergence from it that this tool measures. The tagline
underneath is set in moss, one step down in hierarchy.

The data graphic uses the same palette, and the accent appears exactly once,
on the bracket under the duplicated slots, because that is the first thing a
reader should look at in that picture. Every number in the graphic comes from
running the CLI on `samples/cluster-window.jsonl`. Both assets are static:
the motion decision is none, because nothing in this tool is a sequence that a
static frame misrepresents.

The palette was derived from the subject: warm paper and ink, with a single
rust accent, chosen against the common dark dashboard look. Contrast on the
paper background is 11.5:1 for ink, 6.1:1 for rust, and 5.1:1 for moss, which
clears WCAG AA for the text sizes used. The banner carries one animation: the
report summary line types itself once per loop, which encodes the report being
written after the scan. Under reduced motion the line is simply fully visible,
and the banner reads the same. The wordmark asset stays static.

---

## License

MIT. See [LICENSE](LICENSE).

<!-- draft note 1063 -->
