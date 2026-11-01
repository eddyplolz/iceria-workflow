"""Numbers and units as MoS 5.3 and 5.5 set them.

A unit symbol is spaced from its number (18 °C, 120 km): an error, since the glued form is never
right. A sentence that opens with a numeral and "percent" as a word are warnings: a list entry or
a quoted title may want them. Ref bodies are not read.
"""

import re

from checks import ERROR, WARNING, Finding, prose_lines, strip_refs

GLUED = re.compile(r"\d+(?:[.,]\d+)*(?:km²|km|m²|cm|mm|kg|ha|°C|°F|m)(?![A-Za-z²])")
# group 1 is the word before the full stop, so "c. 480" and "St. 12" are not sentence starts.
OPENER = re.compile(r"^\d|(\w+)?[.!?][\"')\]]*\s+\d")
ABBREVIATIONS = frozenset("c ca no nos st mt p pp vol fig".split())
PERCENT = re.compile(r"\d\s*(?:percent|per cent)\b", re.I)


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        glued = [m.group(0) for m in GLUED.finditer(prose)]
        if glued:
            found.append(
                Finding(
                    n,
                    "numbers",
                    ERROR,
                    f"no space between number and unit: {', '.join(glued)} (MoS 5.5)",
                )
            )
        if any(
            (m.group(1) or "").lower() not in ABBREVIATIONS for m in OPENER.finditer(prose.lstrip())
        ):
            found.append(
                Finding(
                    n,
                    "numbers",
                    WARNING,
                    "numeral opens a sentence: spell it out or reword (MoS 5.3)",
                )
            )
        if PERCENT.search(prose):
            found.append(Finding(n, "numbers", WARNING, "percent as a word: write 25% (MoS 5.3)"))
    return found
