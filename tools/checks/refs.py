"""References as MoS 12.4, 13.1 and 13.3 set them.

A ref points to a wiki page: never an outside site, Discord, a talk, user, template, help or
project page, or the Water cooler. A nation's Participants list (8.5) is the one place a user page
is linked. Proposals may be cited, but a body link never leads to one.
Named refs are written in full inside <references> at the end, and every name defined there is
cited in the text and the other way round. A name is never only digits: Cite rejects it.
"""

import re

from checks import ERROR, WARNING, Finding, blank, mask, participants_lines, voice

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
# Category:Meta Iceria's rules pages (a ref may cite them; prose may not link them).
STEWARD_PAGE = re.compile(r"\[\[\s*(?:charter|world standards|manual of style)\s*[|\]]", re.I)
# The stewards' world-reference pages sit in Category:Meta Iceria too, but say things about the
# world, so a link is the writer's call.
SHARED_REFERENCE = re.compile(
    r"\[\[\s*(?:geography|history|culture zones|atlas) of iceria\s*[|\]]", re.I
)
# A page about the whole world ("Iceria", "List of nations of Iceria", "2000 in Iceria") belongs
# to no nation, so its links to the shared reference pages are not out of place.
WORLD_TITLE = re.compile(r"\s*(?:Iceria|.+ (?:of|in) Iceria)\s*", re.I)
# Links that leave the world: Wikipedia and its sister sites by prefix.
INTERWIKI = re.compile(r"\[\[\s*(?:w|wikipedia|wikt|wiktionary|commons|wikimedia)\s*:", re.I)
PERSON = re.compile(
    r"personal communication|\bpers\. comm\b|private message|\bin conversation\b", re.I
)
PROPOSAL_LINK = re.compile(r"\[\[\s*:?\s*proposal\s*:", re.I)
USER_LINK = re.compile(r"\[\[\s*user\s*:", re.I)


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
        if name and re.fullmatch(r"[0-9]+", name):
            found.append(
                Finding(
                    n,
                    "refs",
                    ERROR,
                    f"all-digit ref name {name!r}: MediaWiki's Cite shows a cite error for it; "
                    "give it a descriptive name, e.g. constitution1978",
                )
            )
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
        if PERSON.search(content):
            found.append(
                Finding(
                    n, "refs", ERROR, "ref cites a person: cite a wiki page, not a conversation"
                )
            )
        if hits := voice._out_of_world(content):
            found.append(
                Finding(
                    n,
                    "refs",
                    ERROR,
                    f"out-of-world voice in a ref: {', '.join(hits)}; cite a page of the wiki "
                    "world (MoS 13.1)",
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
    members = participants_lines(text)
    for m in (*META.finditer(outside_refs), *STEWARD_PAGE.finditer(outside_refs)):
        # MoS 8.5: the Participants list names its members by their user pages.
        if USER_LINK.match(m.group(0)) and line_of(m.start()) in members:
            continue
        found.append(
            Finding(
                line_of(m.start()),
                "refs",
                ERROR,
                "link to a meta page in the text: write about the world, and link only its "
                "articles (MoS 12.4)",
            )
        )
    title = ctx.get("title") or ""
    world_page = WORLD_TITLE.fullmatch(title) and title not in ctx.get("nations", {})
    shared = [] if world_page else SHARED_REFERENCE.finditer(outside_refs)
    for m in shared:
        found.append(
            Finding(
                line_of(m.start()),
                "refs",
                WARNING,
                "link to a shared reference page: a steward page, not part of this nation; "
                "link the nation's own article or cite it in a ref (MoS 12.4)",
            )
        )
    for m in INTERWIKI.finditer(outside_refs):
        found.append(
            Finding(
                line_of(m.start()),
                "refs",
                ERROR,
                "link to a meta page in the text: an outside wiki is not part of the world "
                "(MoS 12.4)",
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
