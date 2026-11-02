"""Headings as MoS 4.1 and 4.2 set them.

Sentence case; start at level 2 and go down one level at a time; no links, bold, italics or
templates; no final full stop; unique; never the article's title. Closing sections run Participants
(a nation's only), See also, Notes, References, and Iceria has no External links or Further reading section.
"""

import re

from checks import ERROR, HEADING, WARNING, Finding, lines

CLOSING = ["Participants", "See also", "Notes", "References"]
NOT_USED = {"external links", "further reading"}
# Section words that are lower case mid-heading in sentence case. Title Case is only guessed from
# these, since a capital on any other word may be a proper name ("Rise of the Vell League").
COMMON = set(
    """history geography economy culture politics government demographics military religion
    society early modern late foreign relations period era age life career death legacy background
    overview education transport infrastructure climate population language languages sports media
    administration divisions symbols etymology formation founding reception aftermath origins name
    names art arts music literature cuisine law policy trade industry agriculture people""".split()
)
FUNCTION_WORDS = {"And", "Or", "Of", "The", "In", "On", "For", "To", "With", "At", "By"}


def run(text: str, ctx: dict) -> list[Finding]:
    title = (ctx.get("title") or "").strip().lower()
    found, prev, seen, closing_at = [], 1, set(), -1

    def add(n, level, msg):
        found.append(Finding(n, "headings", level, msg))

    for n, line in enumerate(lines(text), 1):
        m = HEADING.match(line)
        if not m:
            continue
        level, name = min(len(m.group(1)), len(m.group(3))), m.group(2)
        low = name.lower()
        if level == 1:
            add(n, ERROR, "level 1 heading: start at == Heading == (MoS 4.1)")
        elif level > prev + 1:
            add(n, ERROR, f"heading skips a level: level {level} after level {prev} (MoS 4.1)")
        prev = level
        if re.search(r"\[\[|\{\{|''|<", name):
            add(n, ERROR, "markup in a heading: no links, bold, italics or templates (MoS 4.1)")
        letters = re.sub(r"[^A-Za-z]", "", name)
        if len(letters) >= 3 and letters.isupper():
            add(n, ERROR, "all-caps heading: use sentence case (MoS 4.1)")
        if name.endswith("."):
            add(n, ERROR, "heading ends with a full stop: drop it (MoS 4.1)")
        if low in seen:
            add(n, ERROR, f"duplicate heading: {name!r} is already used (MoS 4.1)")
        seen.add(low)
        if low in NOT_USED:
            add(n, ERROR, f"section not used on Iceria: {name!r} (MoS 4.2)")
        standard = next((c for c in CLOSING if c.lower() == low), None)
        if standard and name != standard:
            add(n, ERROR, f"standard heading in the wrong case: write {standard!r} (MoS 4.2)")
        if standard:
            at = CLOSING.index(standard)
            if at < closing_at:
                add(
                    n,
                    ERROR,
                    "closing sections out of order: Participants, See also, Notes, References "
                    "(MoS 4.2)",
                )
            closing_at = max(closing_at, at)
        elif not letters.isupper():
            words = name.split()[1:]
            known = {
                p.lower()
                for nm in (*ctx.get("names", []), *ctx.get("families", []), *ctx.get("nations", {}))
                for p in nm.split()
            }
            # Every word capitalized, none a known name, is Title Case; a lower-case word
            # ("of the") marks a proper-name phrase.
            all_caps = len(words) >= 1 and all(w[:1].isupper() for w in name.split())
            if (
                any(w[:1].isupper() and w.lower() in COMMON for w in words)
                or any(w in FUNCTION_WORDS for w in words)
                or (all_caps and not any(w.lower().strip(",") in known for w in name.split()))
            ):
                add(n, WARNING, "heading may be in title case: use sentence case (MoS 4.1)")
        # A linked title still repeats it: "History of [[Vell]]" reads as "History of Vell".
        plain = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", low)
        if title and (plain == title or plain.endswith(" of " + title)):
            add(n, WARNING, "heading repeats the title: name the topic of the section (MoS 4.1)")
    return found
