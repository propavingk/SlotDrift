"""Command line interface.

Exit codes, documented in docs/FORMAT.md:

- 0: the export is continuous, no forks and no parse errors
- 1: findings are present
- 2: usage error (bad arguments, missing or unreadable input)

The CLI never touches the network and never writes files unless asked.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .continuity import analyze_continuity
from .forks import find_forks
from .model import parse_file
from .report import Analysis, render_json, render_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slotdrift",
        description="Slot continuity and fork analysis for captured Solana slot records.",
    )
    parser.add_argument("--version", action="version", version=f"slotdrift {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="full continuity and fork report")
    analyze.add_argument("input", type=Path, help="slot export (JSONL)")
    analyze.add_argument("--format", choices=("text", "json"), default="text")
    analyze.add_argument("--limit", type=int, default=10, help="list entries shown per section")
    analyze.add_argument("--output", type=Path, default=None, help="write the report to a file")

    leaders = sub.add_parser("leaders", help="per-leader skip rates only")
    leaders.add_argument("input", type=Path, help="slot export (JSONL)")

    forks = sub.add_parser("forks", help="duplicate slots and orphan segments only")
    forks.add_argument("input", type=Path, help="slot export (JSONL)")

    return parser
