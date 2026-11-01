"""One spelling per page (MoS 6.1): American or British, the writer's choice, never both.

The check never asks for one variety. It only warns when a page uses both forms of the same word,
at the first line of the less common form (on a tie, the form that appears second).
"""

import re

from checks import WARNING, Finding, prose_lines, strip_refs

# (American, British) stems; inflected forms (colours, harbored, centres) count as the stem.
PAIRS = [
    ("color", "colour"),
    ("honor", "honour"),
    ("labor", "labour"),
    ("harbor", "harbour"),
    ("neighbor", "neighbour"),
    ("favor", "favour"),
    ("valor", "valour"),
    ("center", "centre"),
    ("theater", "theatre"),
    ("meter", "metre"),
    ("defense", "defence"),
    ("offense", "offence"),
    ("gray", "grey"),
    ("traveled", "travelled"),
    ("catalog", "catalogue"),
    ("analyze", "analyse"),
    ("organize", "organise"),
    ("recognize", "recognise"),
    ("realize", "realise"),
    ("organization", "organisation"),
    ("civilization", "civilisation"),
]


def _stem(word: str) -> re.Pattern:
    return re.compile(rf"\b{word}(?:s|es|ed|ing|d)?\b", re.I)


def run(text: str, ctx: dict) -> list[Finding]:
    rows = [(n, strip_refs(line)) for n, line in prose_lines(text)]
    found = []
    for us, uk in PAIRS:
        seen = {}
        for form in (us, uk):
            rx = _stem(form)
            hits = [n for n, line in rows for _ in rx.finditer(line)]
            if hits:
                seen[form] = hits
        if len(seen) < 2:
            continue
        # Fewer hits is the odd one out; on a tie, the form that shows up later.
        odd = min(seen, key=lambda f: (len(seen[f]), -seen[f][0]))
        other = uk if odd == us else us
        found.append(
            Finding(
                seen[odd][0],
                "spelling",
                WARNING,
                f"mixed spelling: '{odd}' here, '{other}' elsewhere; pick one for the page (MoS 6.1)",
            )
        )
    return sorted(found, key=lambda f: f.line)
