"""Cross-engine parity check.

Runs the Python implementation and the Rust engine on the same fixtures and
compares the numbers they report. This is a build-time check, not part of the
offline tool: the CLI itself never spawns processes.

Usage (from the repository root):

    python scripts/parity.py

Exit 0 when every fixture agrees, 1 otherwise.
