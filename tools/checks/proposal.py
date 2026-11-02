"""The core of a {{Proposal}} form, as Template:Proposal sets it.

The stewards read six core answers: name, claim, family, history, capital, and one of differs,
problem or neighbor. Each must be filled in, the family must be one of the world's culture
families (ctx["families"]), and the capital must not be another nation's (World Standards 6,
ctx["nations"]). Only a form (ctx["form"]) is read.
"""

import re

from checks import ERROR, Finding, clashes, lines

CORE = ("name", "claim", "family", "history", "capital")
ONE_OF = ("differs", "problem", "neighbor")
FIELD = re.compile(r"^\s*\|\s*(\w+)\s*=(.*)$")


def _fields(text: str) -> dict[str, tuple[int, str]]:
    """{field: (line, value)} for the form's top-level fields, comments left out."""
    found, depth = {}, 0
    for n, ln in enumerate(lines(text), 1):
        if depth == 1 and (m := FIELD.match(ln)):
            found.setdefault(m.group(1).lower(), (n, m.group(2).strip()))
        depth += ln.count("{{") - ln.count("}}")
    return found


def run(text: str, ctx: dict) -> list[Finding]:
    if not ctx.get("form"):
        return []
    fields, found = _fields(text), []
    for key in CORE:
        n, value = fields.get(key, (1, ""))
        if not value:
            found.append(
                Finding(
                    n,
                    "proposal",
                    ERROR,
                    f"the core field '{key}' is empty: fill it in before the form goes to the "
                    "stewards (Template:Proposal)",
                )
            )
    if not any(fields.get(key, (0, ""))[1] for key in ONE_OF):
        found.append(
            Finding(
                1,
                "proposal",
                ERROR,
                "the core asks for one of differs, problem or neighbor: answer one of them in a "
                "few sentences (Template:Proposal)",
            )
        )
    families = ctx.get("families", [])
    n, family = fields.get("family", (1, ""))
    if family and families and family.lower() not in {f.lower() for f in families}:
        found.append(
            Finding(
                n,
                "proposal",
                ERROR,
                f"family is not a culture family of Iceria: {family}; use one from "
                f"canon/culture-zones.md, such as {' or '.join(families[:2])} "
                "(Culture zones of Iceria)",
            )
        )
    n, capital = fields.get("capital", (1, ""))
    name = clashes.plain(fields.get("name", (1, ""))[1])
    for nation, theirs in ctx.get("nations", {}).items():
        if (
            capital
            and theirs
            and nation != name
            and clashes.plain(capital).lower() == theirs.lower()
        ):
            found.append(
                Finding(
                    n,
                    "proposal",
                    ERROR,
                    f"capital is already the capital of {nation}: {capital}; give your nation a "
                    "capital of its own (World Standards 6)",
                )
            )
    return sorted(found, key=lambda f: f.line)
