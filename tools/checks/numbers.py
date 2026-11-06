"""Numbers and units as MoS 5.3 and 5.5 set them.

A unit symbol is spaced from its number (18 °C, 120 km): an error, since the glued form is never
right. A sentence that opens with a numeral and "percent" as a word are warnings: a list entry or
a quoted title may want them. Ref bodies are not read.
"""

import re

from checks import ERROR, MONTH, QUOTED, WARNING, Finding, prose_lines, strip_refs

GLUED = re.compile(r"\d+(?:[.,]\d+)*(?:km²|km|m²|cm|mm|kg|ha|°C|°F|m)(?![A-Za-z²])")
# group 1 is the word before the full stop, so "c. 480" and "St. 12" are not sentence starts.
OPENER = re.compile(r"^\d|(\w+)?[.!?][\"')\]]*\s+\d")
ABBREVIATIONS = frozenset("c ca no nos st mt p pp vol fig".split())
# A clause number at the start of a line ("1.", "12)"), as a constitution numbers its articles.
# Four digits ("1534.") stay a year.
CLAUSE = re.compile(r"^\s*\d{1,3}[.)]\s+")
PERCENT = re.compile(r"\d\s*(?:percent|per cent)\b", re.I)
# A lone digit 0-9 that is a count (MoS 5.3). Not part of a longer number, ordinal, unit, percent
# or range; not a date, a quantity in millions, a numbered item ("Article 3") or a signed offset
# ("UTC+2").
SMALL = re.compile(r"(?<![\w.,/$€£+−±-])\d(?![\w%/°²-]|[.,]\d)")
SMALL_AFTER = re.compile(
    rf"\s*(?:km|m|cm|mm|kg|ha|million|billion|trillion|percent|per cent|{MONTH}|écu)\b", re.I
)
SMALL_BEFORE = re.compile(
    rf"(?:{MONTH}|Article|Section|Chapter|Clause|Part|Book|Volume|Table|Figure|Phase|Stage|"
    r"Level|Class|Type|Rule|Act|Line|Page|No\.|Nos\.|Mk\.?|c\.|ca\.)\s+$",
    re.I,
)
BIG = re.compile(r"\d{2,}|\d,\d{3}")
FIGURE = re.compile(
    r"\b\d{1,3}(?:,\d{3})+\b(?!\s*(?:km|m|cm|mm|kg|ha|°|mi|t)\b|\s*km²)|\b\d+(?:\.\d+)?\s+(?:million|billion|trillion)\b",
    re.I,
)
LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
CITED_END = re.compile(r"[.!?](?:<ref\b[^>]*/>|<ref\b[^>]*>.*?</ref>)*(?=\s+\S)", re.S)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _small_numbers(prose: str) -> list[str]:
    """Digits 0-9 used as counts, sentence by sentence; a sentence that also holds a larger
    number keeps its numerals so that numbers compared together share one form (MoS 5.3)."""
    prose = TEMPLATE.sub(" ", QUOTED.sub(" ", LINK.sub(r"\1", prose)))
    hits = []
    for sentence in SENTENCE_END.split(prose):
        if BIG.search(sentence):
            continue
        hits += [
            m.group(0)
            for m in SMALL.finditer(sentence)
            if not SMALL_AFTER.match(sentence, m.end())
            and not SMALL_BEFORE.search(sentence[: m.start()])
        ]
    return hits


def _cited(line: str) -> list[str]:
    """The sentences of a line, each with the refs that follow its full stop."""
    start, sentences = 0, []
    for m in CITED_END.finditer(line):
        sentences.append(line[start : m.end()])
        start = m.end()
    return sentences + [line[start:]]


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    for n, line in prose_lines(text):
        prose = CLAUSE.sub("", strip_refs(line))
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
        if small := _small_numbers(prose):
            found.append(
                Finding(
                    n,
                    "numbers",
                    WARNING,
                    f"small number as a numeral: {', '.join(dict.fromkeys(small))}; spell out "
                    "zero to nine (MoS 5.3)",
                )
            )
        if any(
            FIGURE.search(strip_refs(sentence)) and not re.search(r"<ref\b", sentence, re.I)
            for sentence in _cited(line)
        ):
            found.append(
                Finding(
                    n,
                    "numbers",
                    WARNING,
                    "figure without a reference: skip this if this page is the first to publish the "
                    "number; a number taken from another page cites that page (MoS 13.2)",
                )
            )
        if PERCENT.search(prose):
            found.append(Finding(n, "numbers", WARNING, "percent as a word: write 25% (MoS 5.3)"))
    return found
