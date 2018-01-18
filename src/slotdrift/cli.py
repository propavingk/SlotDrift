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

