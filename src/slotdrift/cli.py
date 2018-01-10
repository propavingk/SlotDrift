"""Command line interface.

Exit codes, documented in docs/FORMAT.md:

- 0: the export is continuous, no forks and no parse errors
- 1: findings are present
- 2: usage error (bad arguments, missing or unreadable input)

The CLI never touches the network and never writes files unless asked.
"""
from __future__ import annotations

