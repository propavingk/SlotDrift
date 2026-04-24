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
        return False, "readme terms: banned marketing term " + ", ".join(hits)
    return True, "readme terms: no banned marketing terms"


def check_svg_metadata() -> tuple[bool, str]:
    bad = []
    for path in svg_files():
        tree = ET.parse(path)
        root = tree.getroot()
        if "viewBox" not in root.attrib:
            bad.append(f"{path.name}: viewBox")
            continue
        if root.attrib.get("role") != "img":
            bad.append(f"{path.name}: role")
        if root.find("{http://www.w3.org/2000/svg}title") is None:
            bad.append(f"{path.name}: title")
        if root.find("{http://www.w3.org/2000/svg}desc") is None:
            bad.append(f"{path.name}: desc")
    if bad:
        return False, "svg metadata: " + "; ".join(bad)
    return True, "svg metadata: viewBox, role, title, desc present"


def _text_width(content: str, font_size: float, font_family: str) -> float:
    per_char = 0.60 if "mono" in font_family.lower() else 0.58
    return len(content) * font_size * per_char


def check_svg_label_overlap() -> tuple[bool, str]:
    bad = []
    ns = "{http://www.w3.org/2000/svg}"
    for path in svg_files():
        tree = ET.parse(path)
        labels = []
        for element in tree.getroot().iter(f"{ns}text"):
            content = "".join(element.itertext()).strip()
            if not content:
                continue
            try:
                x = float(element.attrib.get("x", "0"))
                y = float(element.attrib.get("y", "0"))
            except ValueError:
                continue
            font_size = float(element.attrib.get("font-size", "11"))
            family = element.attrib.get("font-family", "")
            anchor = element.attrib.get("text-anchor", "start")
            width = _text_width(content, font_size, family)
            if anchor == "middle":
                left = x - width / 2
            elif anchor == "end":
                left = x - width
            else:
                left = x
            labels.append((round(y), left, left + width, content))
        for baseline in {label[0] for label in labels}:
            row = sorted([label for label in labels if label[0] == baseline], key=lambda l: l[1])
            for previous, current in zip(row, row[1:]):
                if current[1] < previous[2] - 0.5:
                    bad.append(
                        f"{path.name}: '{previous[3]}' overlaps '{current[3]}' at y={baseline}"
                    )
    if bad:
        return False, "svg labels: " + "; ".join(bad)
    return True, "svg labels: no overlapping labels on shared baselines"


CHECKS = [
    ("svg parse", check_svg_parse),
    ("svg filters", check_svg_filters),
    ("svg comments", check_svg_comments),
    ("em dash", check_em_dash),
    ("readme attributes", check_readme_attr_blocks),
    ("readme terms", check_readme_terms),
    ("svg metadata", check_svg_metadata),
    ("svg labels", check_svg_label_overlap),
]


def main() -> int:
    failures = 0
    for name, check in CHECKS:
        try:
            ok, message = check()
        except Exception as exc:  # noqa: BLE001
            ok, message = False, f"{name}: crashed with {exc!r}"
        print(f"[{'pass' if ok else 'FAIL'}] {message}")
        if not ok:
            failures += 1
    print(f"verify: {len(CHECKS)} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
