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
