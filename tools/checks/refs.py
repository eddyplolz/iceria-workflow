"""References as MoS 12.4, 13.1 and 13.3 set them.

A ref points to a wiki page: never an outside site, Discord, a talk, user, template, help or
project page, or the Water cooler. Proposals may be cited, but a body link never leads to one.
Named refs are written in full inside <references> at the end, and every name defined there is
cited in the text and the other way round.
"""

import re

from checks import ERROR, WARNING, Finding, blank, mask

# A self-closing ref has no group 3; a full ref has its body there.
REF = re.compile(r"<ref\b([^>]*?)/>|<ref\b([^>]*)>(.*?)</ref\s*>", re.I | re.S)
NAME = re.compile(r"""\bname\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s/>]+))""", re.I)
BLOCK = re.compile(r"<references\b[^>]*>(.*?)</references\s*>", re.I | re.S)
OUTSIDE = re.compile(r"https?://|\bwww\.|discord", re.I)
META = re.compile(
    r"\[\[\s*(?:(?:\w+ )?talk|user|template|help|project|the world of iceria|mediawiki)\s*:"
    r"|\[\[\s*water cooler",
    re.I,
)
PROPOSAL_LINK = re.compile(r"\[\[\s*:?\s*proposal\s*:", re.I)


def _name(attrs: str) -> str | None:
    m = NAME.search(attrs)
    return next(g for g in m.groups() if g is not None).strip() if m else None


def run(text: str, ctx: dict) -> list[Finding]:
    body = mask(text)

    def line_of(pos: int) -> int:
        return body.count("\n", 0, pos) + 1

    blocks = [(m.start(1), m.end(1)) for m in BLOCK.finditer(body)]
    found, cited, defined = [], {}, {}
    for m in REF.finditer(body):
        n, content = line_of(m.start()), m.group(3)
        name = _name(m.group(1) if content is None else m.group(2))
        in_list = any(a <= m.start() < b for a, b in blocks)
        if content is None:
            if name:
                cited.setdefault(name, n)
            continue
        if name:
            defined.setdefault(name, n)
            if not in_list:
                cited.setdefault(name, n)
        if not in_list:
            found.append(
                Finding(
                    n,
                    "refs",
                    WARNING,
                    "full ref in the body: name it and write it inside <references> (MoS 13.3)",
                )
            )
        if OUTSIDE.search(content):
            found.append(
                Finding(
                    n, "refs", ERROR, "outside source: refs point to wiki pages only (MoS 13.1)"
                )
            )
        if META.search(content):
            found.append(
                Finding(
                    n,
                    "refs",
                    ERROR,
                    "ref to a meta page: cite articles, Library pages or proposals (MoS 13.1)",
                )
            )
    outside_refs = REF.sub(blank, body)
    for m in PROPOSAL_LINK.finditer(outside_refs):
        found.append(
            Finding(
                line_of(m.start()),
                "refs",
                ERROR,
                "body link to a proposal: link the article, cite the proposal in a ref (MoS 12.4)",
            )
        )
    for name, n in cited.items():
        if name not in defined:
            found.append(
                Finding(n, "refs", ERROR, f"ref cited but never defined: {name!r} (MoS 13.3)")
            )
    for name, n in defined.items():
        if name not in cited:
            found.append(
                Finding(n, "refs", ERROR, f"ref defined but never cited: {name!r} (MoS 13.3)")
            )
    return sorted(found, key=lambda f: f.line)
