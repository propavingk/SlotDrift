"""Executable quality gate for slotdrift.

Runs eight mechanical checks over the repository and prints one line per
check. Exit code 0 when every check passes, 1 otherwise.

    python scripts/verify.py

The checks implement the standing lessons for this project tree. They are
deliberately mechanical: a claim of correctness is the exit code of this
script, not a sentence in a report.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"

TEXT_EXTENSIONS = {
    ".py", ".md", ".svg", ".yml", ".yaml", ".toml", ".cff", ".jsonl",
    ".txt", ".cfg", ".ini", ".editorconfig", ".gitattributes", ".gitignore",
    ".html", ".css", ".js", ".ts", ".rs", ".go", ".sh",
}

BANNED_TERMS = [
    "AI powered", "seamless", "revolutionary", "enterprise-grade",
    "next generation", "cutting edge", "blazing fast", "production ready",
    "battle tested", "lightning fast", "effortless",
]

# The forms are assembled from parts so this file does not contain them
# literally: a checker that flags itself is not a checker.
EM_DASH_FORMS = [chr(0x2014), "&#" + "8212;", "&mdash" + ";"]


def svg_files() -> list[Path]:
    return sorted(ASSETS.glob("*.svg"))


def check_svg_parse() -> tuple[bool, str]:
    bad = []
    for path in svg_files():
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            bad.append(f"{path.name}: {exc}")
    if bad:
        return False, "svg parse: " + "; ".join(bad)
    return True, f"svg parse: {len(svg_files())} files well formed"


def check_svg_filters() -> tuple[bool, str]:
    bad = []
    for path in svg_files():
        text = path.read_text(encoding="utf-8")
        for token in ("feGaussianBlur", "feDropShadow", "feTurbulence"):
            if token in text:
                bad.append(f"{path.name}: {token}")
    if bad:
        return False, "svg filters: " + "; ".join(bad)
    return True, "svg filters: none present"


