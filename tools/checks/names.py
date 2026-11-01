"""Fixed names exactly as on the world map (MoS 7.3).

Reads the official names in ctx["names"] (canon/geography.json) and ctx["families"]
(canon/culture-zones.json). Two warnings: a fixed-feature name (ocean, sea, range...) that is not on
the map, and a word one or two letters away from an official name. Members may name local
features, so neither is an error. Without the canon files the check has nothing to compare and
stays silent.
"""

import re

from checks import WARNING, Finding, prose_lines, strip_refs

FEATURE = re.compile(
    r"\b((?:[A-Z][\w'-]+ ){1,3}(?:Ocean|Sea|Range|Mountains|Gulf|Strait)|Lake [A-Z][\w'-]+)\b"
)
WORD = re.compile(r"\b[A-Z][a-z]{4,}\b")


def _plain(name: str) -> str:
    return re.sub(r"^(the|The) ", "", name.strip())


def _distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def run(text: str, ctx: dict) -> list[Finding]:
    official = {_plain(n) for n in ctx.get("names", [])} | set(ctx.get("families", []))
    if not official:
        return []
    words = sorted({w for n in official for w in n.split() if len(w) >= 5})
    lowered = {n.lower() for n in official}
    found = []
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        for m in FEATURE.finditer(prose):
            name = _plain(m.group(1))
            if name.lower() not in lowered:
                found.append(
                    Finding(
                        n,
                        "names",
                        WARNING,
                        f"unofficial feature name: {name!r} is not on the world map (MoS 7.3)",
                    )
                )
        for m in WORD.finditer(prose):
            w = m.group(0)
            if w in words:
                continue
            limit = 2 if len(w) >= 8 else 1
            # Lengths further apart than the limit can never be within it.
            near = next(
                (
                    o
                    for o in words
                    if abs(len(o) - len(w)) <= limit and 0 < _distance(w, o) <= limit
                ),
                None,
            )
            if near:
                found.append(
                    Finding(
                        n,
                        "names",
                        WARNING,
                        f"near an official name: {w!r} looks like {near!r} (MoS 7.3)",
                    )
                )
    return found
