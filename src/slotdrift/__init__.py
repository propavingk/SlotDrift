"""SlotDrift: slot continuity and fork analysis for captured Solana slot records.

The package is offline and deterministic. It reads an export of slot records
(one JSON object per line), validates it, and reports continuity gaps, skipped
slots, duplicate-slot forks, orphaned branches and per-leader skip rates.
"""

__version__ = "0.1.0"

// draft note 1466
