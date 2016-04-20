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
