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


def check_svg_comments() -> tuple[bool, str]:
    bad = []
    for path in svg_files():
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"<!--(.*?)-->", text, re.S):
            if "--" in match.group(1):
                bad.append(path.name)
                break
    if bad:
        return False, "svg comments: double hyphen in " + ", ".join(bad)
    return True, "svg comments: no illegal double hyphen"


def check_em_dash() -> tuple[bool, str]:
    bad = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix not in TEXT_EXTENSIONS and path.name not in {
            ".editorconfig", ".gitattributes", ".gitignore", "Makefile",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for form in EM_DASH_FORMS:
            if form in text:
                bad.append(str(path.relative_to(ROOT)))
                break
    if bad:
        return False, "em dash: found in " + ", ".join(bad)
    return True, "em dash: none in any text file"


def check_readme_attr_blocks() -> tuple[bool, str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    if re.search(r"\)\{(?:[^}]*)(?:width|height)", text):
        return False, "readme attributes: pandoc style block found"
    return True, "readme attributes: no pandoc style blocks"


def check_readme_terms() -> tuple[bool, str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    hits = [term for term in BANNED_TERMS if term.lower() in text]
    if hits:
