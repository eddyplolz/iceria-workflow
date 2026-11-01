"""Dashes and quotation marks as MoS 6.4 sets them.

No dashes in running prose; the en dash appears only in ranges, unspaced unless a side of the
range has a space in it ("14 March – 2 April 1898"); hyphens join compound modifiers; quotation
marks are straight. Infobox, table and heading lines are not prose and are not read; nor are ref
bodies, which quote page titles as they are.
"""

import re

from checks import ERROR, MONTH, Finding, prose_lines, strip_refs

RULES = [
    (re.compile("—"), "em dash: recast the sentence; MoS 6.4 allows no dashes in prose"),
    (re.compile(r"(?<!-)--(?!-)"), "double hyphen: recast the sentence (MoS 6.4)"),
    (re.compile("[“”‘’]"), "curly quote: use straight quotes (MoS 6.4)"),
    (re.compile(r"(?<=\w) - (?=\w)"), "spaced hyphen: recast the sentence (MoS 6.4)"),
]
SPACED_EN = re.compile(r"(\S+) – (\S+)")
# A tight range joins years, decades or months, and may run to "present" (MoS 5.2).
RANGE_END = rf"(?:\d{{1,4}}s?|{MONTH})"
TIGHT_EN = re.compile(r"(\S+?)–(\S+)")
TIGHT_RANGE = re.compile(rf"(?:^|\W){RANGE_END}–(?:{RANGE_END}|present)(?:\W|$)")


def _range_side(before: str, after: str) -> bool:
    return bool(re.search(rf"(\d|{MONTH})\W*$", before)) and (
        after[:1].isdigit() or after.startswith("present")
    )


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        for rx, msg in RULES:
            if rx.search(prose):
                found.append(Finding(n, "dashes", ERROR, msg))
        for m in SPACED_EN.finditer(prose):
            if not _range_side(m.group(1), m.group(2)):
                found.append(
                    Finding(n, "dashes", ERROR, "spaced en dash in prose: recast it (MoS 6.4)")
                )
                break
        for m in TIGHT_EN.finditer(prose):
            if not TIGHT_RANGE.search(m.group(0)):
                found.append(
                    Finding(
                        n,
                        "dashes",
                        ERROR,
                        "en dash outside a range: use it for ranges only (MoS 6.4)",
                    )
                )
                break
    return found
