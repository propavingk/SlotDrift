# Contributing to slotdrift

Thanks for considering a contribution. slotdrift is an offline analysis tool:
it reads a slot export, validates it, and reports continuity and fork
findings. The whole tool is deterministic, and that property is part of the
contract, not an accident.

This file explains the setup, the checks, and what a good change looks like
here.

## Setup

There is nothing to install for the Python side. Python 3.11 or newer is the
only requirement, and the package uses the standard library only:

```bash
git clone <repository>
cd slotdrift
export PYTHONPATH=src
```

The Rust engine lives in `engine/` and uses the standard library only as well.
A stable Rust toolchain with `rustfmt` and `clippy` is enough:

```bash
rustup component add rustfmt clippy
```

## The checks

Run these before opening a pull request. They are the same checks CI runs.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
cargo test --manifest-path engine/Cargo.toml
python scripts/parity.py
python scripts/verify.py
```

`make test`, `make parity` and `make verify` wrap the same commands.

The parity script is the important one when you touch arithmetic. Any change
to the continuity or fork rules must be made in both implementations, and
`scripts/parity.py` must report that every fixture agrees. A change that only
edits one side will fail parity, and that failure is the point of the check.

## What a good change looks like

- One topic per pull request. A bug fix does not also reorganize a module.
- Tests for behavior changes. New validation rules need a fixture line that
  fails, and new analysis rules need an in-memory record set that exercises
  them.
- Re-run the CLI after a change and paste the real output into the pull
  request description if the report shape changed.
- Keep the report deterministic. If an output byte depends on wall-clock time,
  hash ordering that is not sorted, or randomness, it is a bug.
- Line-oriented output. New sections start with a label line and use two
  spaces of indentation, matching the existing report.

## Standing rules

1. Standard library only, in both languages. No new dependencies, including
   development dependencies, without discussing it first.
