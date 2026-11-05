"""The kit's draft checks. Each module has run(text, ctx) -> list[Finding].

ctx is a dict: title (the article's title), names (official place names from
canon/geography.json), families (culture families from canon/culture-zones.json) and
in_world_date ("14 March 2000" or None, from VERSION.json). Every key is optional.
"""

import re
from dataclasses import dataclass

ERROR, WARNING = "error", "warning"


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    level: str
    message: str

    def format(self, name: str) -> str:
        return f"{name}:{self.line}: {self.rule}: {self.level}: {self.message}"


# Comments, nowiki/pre/syntaxhighlight/source text and behavior switches (__NOTOC__) are not
# prose, so no check reads them; a switch glued to the lead would otherwise hide its first line.
HIDDEN = re.compile(
    r"<!--.*?(?:-->|\Z)|<(?:nowiki|pre|syntaxhighlight|source)\b[^>]*/>"
    r"|<(nowiki|pre|syntaxhighlight|source)\b[^>]*>.*?(?:</\1\s*>|\Z)"
    r"|__[A-Z]+__",
    re.DOTALL | re.IGNORECASE,
)
HEADING = re.compile(r"^\s*(=+)\s*(.*?)\s*(=+)\s*$")
# Lines that are page furniture (templates, tables, files, categories), not prose.
FURNITURE = re.compile(
    r"^\s*(\{\{|\}\}|\{\||\||!|\[\[(File|Image|Category):|__|#REDIRECT)", re.IGNORECASE
)
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"


def blank_text(s: str) -> str:
    """The text with every character but newlines turned to spaces, so line numbers hold."""
    return re.sub(r"[^\n]", " ", s)


def blank(m: re.Match) -> str:
    """blank_text for a match, as a re.sub replacement."""
    return blank_text(m.group(0))


def mask(text: str) -> str:
    """The text with hidden spans blanked out, newlines kept so line numbers still match."""
    return HIDDEN.sub(blank, text)


def lines(text: str) -> list[str]:
    return [ln.rstrip("\r") for ln in mask(text).split("\n")]


# A nation's article is one with an Infobox Country; only nations list Participants (MoS 8.5).
NATION = re.compile(r"\{\{\s*infobox[ _]+country\s*(?=[|}]|$)", re.I | re.M)


def is_nation(text: str) -> bool:
    return bool(NATION.search(mask(text)))


def participants_lines(text: str) -> set[int]:
    """1-based numbers of the lines in a nation's == Participants == list, up to the next heading,
    leaving out furniture such as categories and templates, even ones spanning lines. MoS 1.1 and
    8.5 put the list outside the story, like the categories, so prose checks skip it; anywhere
    else a Participants heading is prose."""
    if not is_nation(text):
        return set()
    inside, out, depth = False, set(), 0
    for i, ln in enumerate(lines(text), 1):
        furniture = depth > 0 or bool(FURNITURE.match(ln))
        depth = max(0, depth + ln.count("{{") - ln.count("}}"))
        if m := HEADING.match(ln):
            inside = m.group(1) == m.group(3) == "==" and m.group(2).lower() == "participants"
        elif inside and ln.strip() and not furniture:
            out.add(i)
    return out


def prose_lines(text: str) -> list[tuple[int, str]]:
    """(1-based line number, line) for running prose: not headings, templates, tables, lists of
    files or categories, the Participants list, and nothing inside a {{template}} that spans
    lines."""
    out, depth, members = [], 0, participants_lines(text)
    for i, ln in enumerate(lines(text), 1):
        furniture = depth > 0 or bool(FURNITURE.match(ln)) or i in members
        depth = max(0, depth + ln.count("{{") - ln.count("}}"))
        if furniture or HEADING.match(ln) or not ln.strip():
            continue
        out.append((i, ln))
    return out


def strip_refs(line: str) -> str:
    """The line with <ref>...</ref> bodies and self-closing refs blanked (same length)."""
    return re.sub(
        r"<ref\b[^>/]*/>|<ref\b[^>]*>.*?</ref\s*>",
        blank,
        line,
        flags=re.I,
    )
