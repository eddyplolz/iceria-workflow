"""Links, images and categories as MoS 12.2, 15.3, 15.4 and 17 set them.

Errors: a link to the article itself, a link to an outside site in the body (refs.py reads ref
bodies), and an article filed in Meta Iceria. Warnings: an image sized in pixels, a caption that
opens "A picture of", Category:Countries added by hand, and a category name that may be in title
case. Ref bodies are not read.
"""

import re

from checks import ERROR, WARNING, Finding, lines, prose_lines, strip_refs
from checks.headings import COMMON

LINK = re.compile(r"\[\[\s*:?\s*([^\]|#]+?)\s*(?:[|#][^\]]*)?\]\]")
OUTSIDE = re.compile(r"https?://|\bwww\.", re.I)
FILE = re.compile(r"\[\[\s*(?:File|Image)\s*:", re.I)
PIXELS = re.compile(r"^\d*x?\d+px$")
CAPTION_OPENER = re.compile(
    r"^(?:an? )?(?:picture|photo|photograph|image|view|drawing)\s+(?:of|showing)\b"
    r"|^(?:image|photo|picture) shows\b",
    re.I,
)
OPTIONS = re.compile(
    r"^(?:thumb|thumbnail|frame|framed|frameless|border|left|right|center|centre|none"
    r"|upright(?:=.*)?|\d*x?\d+px|(?:alt|link|page|lang|class)=.*)$",
    re.I,
)
CATEGORY = re.compile(r"\[\[\s*Category\s*:\s*([^\]|]+?)\s*(?:\|[^\]]*)?\]\]", re.I)
# Category nouns that are lower case after the first word in sentence case ("Cities and towns").
# A capital on any other word may be a proper name ("Rise of the Vell League").
CATEGORY_WORDS = COMMON | set(
    """towns cities villages settlements people persons rivers lakes mountains islands seas
    oceans bodies water heads state states organizations organisations companies parties
    nations countries regions provinces treaties events wars battles buildings ports""".split()
)


def _norm(title: str) -> str:
    title = title.replace("_", " ").strip()
    return title[:1].upper() + title[1:]


def _file_params(line: str, start: int) -> list[str]:
    """The |-separated parameters of the [[File:...]] link that starts at start."""
    params, depth, cur, i = [], 0, "", start + 2
    while i < len(line):
        two = line[i : i + 2]
        if two == "[[":
            depth, cur, i = depth + 1, cur + two, i + 2
        elif two == "]]":
            if depth == 0:
                break
            depth, cur, i = depth - 1, cur + two, i + 2
        elif line[i] == "|" and depth == 0:
            params, cur, i = params + [cur.strip()], "", i + 1
        else:
            cur, i = cur + line[i], i + 1
    return params[1:] + [cur.strip()]


def run(text: str, ctx: dict) -> list[Finding]:
    title = (ctx.get("title") or "").strip()
    found = []
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        if title and any(_norm(m.group(1)) == _norm(title) for m in LINK.finditer(prose)):
            found.append(
                Finding(
                    n,
                    "links",
                    ERROR,
                    "link to the article itself: bold the title, do not link it (MoS 12.2)",
                )
            )
        if OUTSIDE.search(prose):
            found.append(
                Finding(
                    n,
                    "links",
                    ERROR,
                    "link outside the wiki: Iceria pages link only to Iceria pages (MoS 12.2)",
                )
            )
    for n, line in enumerate(lines(text), 1):
        for m in FILE.finditer(line):
            params = _file_params(line, m.start())
            sized = [p for p in params if PIXELS.match(p)]
            if sized:
                found.append(
                    Finding(
                        n,
                        "links",
                        WARNING,
                        f"image size in pixels: {sized[0]}; use upright= (MoS 15.4)",
                    )
                )
            caption = params[-1] if len(params) > 1 and not OPTIONS.match(params[-1]) else ""
            opener = CAPTION_OPENER.search(caption)
            if opener:
                found.append(
                    Finding(
                        n,
                        "links",
                        WARNING,
                        f"caption opens with: {opener.group(0)!r}; name what is shown (MoS 15.3)",
                    )
                )
        for m in CATEGORY.finditer(line):
            name = m.group(1)
            if name.lower() == "meta iceria" and title and ":" not in title:
                found.append(
                    Finding(
                        n,
                        "links",
                        ERROR,
                        "article in Meta Iceria: that category is for project pages (MoS 17.1)",
                    )
                )
            elif name.lower() == "countries":
                found.append(
                    Finding(
                        n,
                        "links",
                        WARNING,
                        "Countries is filled by the nation infobox: do not add it by hand (MoS 17.2)",
                    )
                )
            elif any(w[:1].isupper() and w.lower() in CATEGORY_WORDS for w in name.split()[1:]):
                found.append(
                    Finding(
                        n,
                        "links",
                        WARNING,
                        "category may be in title case: use sentence case (MoS 17.6)",
                    )
                )
    return sorted(found, key=lambda f: f.line)
