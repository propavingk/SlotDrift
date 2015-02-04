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
