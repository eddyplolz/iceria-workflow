"""Dates and time as MoS 1.3, 5.1 and 5.2 set them.

Write "14 March 1898"; a year range takes an en dash (1406–1632); decades have no apostrophe
(1890s). No event may be dated after the present (a scheduled one, "due by 2002", may): the in-world date in ctx["in_world_date"]
(VERSION.json) when the calendar has started, otherwise 2000, the year Iceria's figures are given
for (MoS 5.1). Relative words ("currently", "now") are replaced with a year.
"""

import re

from checks import ERROR, HEADING, MONTH, WARNING, Finding, lines, strip_refs

LAUNCH_YEAR = 2000
FORMS = [
    (
        re.compile(rf"\b{MONTH} \d{{1,2}}(?:st|nd|rd|th)?, \d{{3,4}}\b"),
        "month-first date: write 14 March 1898 (MoS 5.2)",
    ),
    (
        re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th) (?:of )?{MONTH}\b"),
        "ordinal date: write 14 March, not 14th March (MoS 5.2)",
    ),
    (
        re.compile(r"(?<![\d/-])\d{3,4}-\d{2,4}(?![\d-])"),
        "hyphen in a year range: use an en dash, 1406–1632 (MoS 5.2)",
    ),
    (re.compile(r"\b\d{3}0's|'\d0s\b"), "apostrophe in a decade: write 1890s (MoS 5.2)"),
    (
        re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"),
        "numeric date: write the month as a word (MoS 5.2)",
    ),
    (
        re.compile(rf"\b{MONTH}, \d{{3,4}}\b"),
        "comma between month and year: write March 1898 (MoS 5.2)",
    ),
]
# A year counts as a date only in date context, so populations and figures are not read as years.
DATED = re.compile(
    rf"(?:\b(?i:in|since|until|till|by|from|after|before|during|of|on|to|year)\s+|{MONTH}\s+|\d–)"
    r"(\d{4})\b(?![,.]\d)(?:\s+([a-z]+))?"
)
# A number followed by a lowercase word that does not open a clause is a count ("of 3000 men"),
# read as a year only when the word is one of these.
AFTER_A_YEAR = frozenset(
    "the a an and or but when as it its he she they there this that these those with under "
    "after before in on at by to of for from until while his her their".split()
)
# "a population of 4500", "a garrison of 2500 in the fort": a quantity noun before "of" makes the
# number a count whatever follows it.
QUANTITY = re.compile(
    r"\b(?:population|garrison|army|force|fleet|crew|total|strength|staff|workforce|tonnage"
    r"|capacity|budget|sum|area|length|height|depth|distance)\s+of\s+\d{4}$",
    re.I,
)
# A future date that is set, not reported ("the next election is due by 2002") is allowed: the
# clause before the year says it is scheduled.
SCHEDULED = re.compile(
    r"\b(?:due|scheduled|planned|expires?|will|next|set to|is to|are to)\b[^.;]*$", re.I
)
RELATIVE = re.compile(r"\b(currently|now|recently|today|at present|nowadays|presently)\b", re.I)


def _present(ctx: dict) -> tuple[int, str]:
    m = re.search(r"\b(\d{4})$", (ctx.get("in_world_date") or "").strip())
    if m:
        return int(m.group(1)), f"the in-world date is {ctx['in_world_date']}"
    return LAUNCH_YEAR, "the calendar has not started, so figures are given for 2000 (MoS 5.1)"


def run(text: str, ctx: dict) -> list[Finding]:
    year, why = _present(ctx)
    found = []
    for n, line in enumerate(lines(text), 1):
        prose = strip_refs(line)
        for rx, msg in FORMS:
            if rx.search(prose):
                found.append(Finding(n, "dates", ERROR, msg))
        late, counts = set(), set()
        for m in DATED.finditer(prose):
            if int(m.group(1)) <= year or SCHEDULED.search(prose[: m.start()]):
                continue
            count = (m.group(2) and m.group(2) not in AFTER_A_YEAR) or QUANTITY.search(
                prose[: m.end(1)]
            )
            (counts if count else late).add(int(m.group(1)))
        if late:
            found.append(
                Finding(
                    n,
                    "dates",
                    ERROR,
                    f"date after the present: {', '.join(map(str, sorted(late)))}; {why}",
                )
            )
        if counts:
            found.append(
                Finding(
                    n,
                    "dates",
                    WARNING,
                    f"number read as a count, not a year: {', '.join(map(str, sorted(counts)))}; "
                    f"if one is a year, it is after the present ({why})",
                )
            )
        if not HEADING.match(line):
            words = list(dict.fromkeys(m.group(0) for m in RELATIVE.finditer(prose)))
            if words:
                found.append(
                    Finding(
                        n,
                        "dates",
                        WARNING,
                        f"relative time word: {', '.join(words)}; give the year, as of 2000 (MoS 1.3)",
                    )
                )
    return found
