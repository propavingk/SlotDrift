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
