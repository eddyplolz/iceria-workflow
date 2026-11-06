"""The core of a {{Proposal}} form, as Template:Proposal sets it.

The stewards read six core answers: name, claim, family, history, capital, and one of differs,
problem or neighbor. Each must be filled in, the family must be one of the world's culture
families (ctx["families"]), and the capital must not be another nation's (World Standards 6,
ctx["nations"]). The name must not be a canon nation or a real-world place, the claim must name an
image file, and the prose answers are read, as warnings, for dashes, bold lead-ins and real-world
names. Only a form (ctx["form"]) is read.
"""

import re

from checks import ERROR, WARNING, Finding, blank_text, bold, clashes, dashes, lines, mask, voice

# A line that opens a {{Proposal}} form; text may sit above it (a note, a heading).
START = re.compile(r"^[ \t]*\{\{\s*Proposal\s*(?:\||<|$)", re.I | re.M)
BRACES = re.compile(r"\{\{|\}\}")
CORE = ("name", "claim", "family", "history", "capital")
ONE_OF = ("differs", "problem", "neighbor")
PROSE = ("history", "differs", "problem", "neighbor", "twist", "concept")
FIELD = re.compile(r"^\s*\|\s*(\w+)\s*=(.*)$")
CLAIM_FILE = re.compile(r"[^/\\|\[\]]+\.(?:png|jpe?g|svg)", re.I)


def scope(text: str) -> tuple[str, list[Finding]] | None:
    """For a page holding a {{Proposal}} form: the text with everything outside the form blanked
    (newlines kept, so line numbers hold), and a warning naming the lines left unread. None when
    the page holds no form."""
    hidden = mask(text)
    if not (m := START.search(hidden)):
        return None
    depth, end = 0, len(text)
    for b in BRACES.finditer(hidden, m.start()):
        depth += 1 if b.group() == "{{" else -1
        if depth == 0:
            end = b.end()
            break
    before, after = hidden[: m.start()], hidden[end:]
    outside = [
        n
        for n, ln in enumerate(lines(before + blank_text(text[m.start() : end]) + after), 1)
        if ln.strip()
    ]
    found = []
    if outside:
        found.append(
            Finding(
                outside[0],
                "proposal",
                WARNING,
                f"{len(outside)} line{'s' if len(outside) != 1 else ''} outside the {{{{Proposal}}}} "
                f"form {'were' if len(outside) != 1 else 'was'} not checked: the stewards read the form, so keep notes out of it or "
                "check them as a page of their own",
            )
        )
    return blank_text(text[: m.start()]) + text[m.start() : end] + blank_text(text[end:]), found


def _fields(text: str) -> dict[str, tuple[int, str]]:
    """{field: (line, value)} for the form's top-level fields, comments left out. A value runs on
    over the lines below it until the next field or the close of the form, since an answer may be
    paragraphs written under its "| history =" line. Any top-level "| x =" is a field, as it is on
    the wiki, whether or not Template:Proposal names it."""
    found, depth, current = {}, 0, None  # current: [key, line, value lines]
    for n, ln in enumerate(lines(text), 1):
        before = depth
        depth += ln.count("{{") - ln.count("}}")
        if before == 1 and (m := FIELD.match(ln)):
            current = [m.group(1).lower(), n, []]
            found.setdefault(current[0], current)
            ln = m.group(2)
        if before < 1 or not current:
            continue
        if depth <= 0:  # the line that closes the form
            current[2].append(ln[: ln.rfind("}}")])
            break
        current[2].append(ln)
    return {key: (n, "\n".join(value).strip()) for key, (_, n, value) in found.items()}


def _prose(n: int, value: str, ctx: dict) -> list[Finding]:
    """The dash, bold lead-in and real-world-name findings for one answer, put on its line.

    Warnings all: the history answer becomes the nation article later, but a proposal is not yet an
    article."""
    found = dashes.run(value, ctx) + [f for f in bold.run(value, ctx) if f.level == ERROR]
    found += [
        f
        for f in voice.run(value, {**ctx, "form": False})
        if f.message.startswith("real-world name")
    ]
    return [Finding(n, f.rule, WARNING, f.message) for f in found]


def run(text: str, ctx: dict) -> list[Finding]:
    if not ctx.get("form"):
        return []
    fields, found = _fields(text), []
    for key in PROSE:
        n, value = fields.get(key, (1, ""))
        if value:
            found += _prose(n, value, ctx)
        if value and key in ("history", *ONE_OF) and len(value.split()) < 3:
            found.append(
                Finding(
                    n,
                    "proposal",
                    WARNING,
                    f"{key} is too short to be an answer: write a sentence or two "
                    "(Template:Proposal)",
                )
            )
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
    n, claim = fields.get("claim", (1, ""))
    if claim and not CLAIM_FILE.fullmatch(claim):
        found.append(
            Finding(
                n,
                "proposal",
                ERROR,
                f"claim is not an image file name: {claim}; give the file you uploaded, such as "
                f"{clashes.plain(fields.get('name', (1, ''))[1]) or 'Name'}-claim.png "
                "(Template:Proposal)",
            )
        )
    n, capital = fields.get("capital", (1, ""))
    n_name, raw_name = fields.get("name", (1, ""))
    name = clashes.plain(raw_name)
    own = clashes.plain(ctx.get("own_nation", "")).lower()
    others = [nation for nation in ctx.get("nations", {}) if nation.lower() != own]
    if name and any(name.lower() == nation.lower() for nation in others):
        found.append(
            Finding(
                n_name,
                "proposal",
                ERROR,
                f"name is already a nation of Iceria: {name}; choose a name of your own "
                "(World Standards 6.5)",
            )
        )
    if name and voice.REAL_RX.fullmatch(name):
        found.append(
            Finding(
                n_name,
                "proposal",
                ERROR,
                f"name is a real-world place: {name}; Iceria has its own names "
                "(World Standards 6.2, MoS 7.2)",
            )
        )
    for nation, theirs in ctx.get("nations", {}).items():
        if (
            capital
            and theirs
            and nation != name
            and nation.lower() != own
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
