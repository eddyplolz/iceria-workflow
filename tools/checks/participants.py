"""A nation's Participants section, as MoS 8.4 and 8.5 set it.

A nation's article (one with an Infobox Country) ends with its Participants: a bulleted list, one
line per member, "* [[User:Name]] (creator)" or "(participant)", then an optional short note. Only
the current holder is the creator, and a shared power has none, so one creator at most. Other
kinds of page carry no Participants section.
"""

import re

from checks import WARNING, Finding, is_nation, lines, participants_lines

HEADING = re.compile(r"^\s*==\s*Participants\s*==\s*$", re.I)
MEMBER = re.compile(
    r"^\*\s*\[\[\s*User\s*:\s*([^\]|]+?)\s*(?:\|[^\]]*)?\]\]\s*\((creator|participant)\)", re.I
)
# The names the template and the manual's own wording stand in with.
PLACEHOLDERS = {"yourname", "your name", "name"}


def run(text: str, ctx: dict) -> list[Finding]:
    rows = lines(text)
    at = next((n for n, ln in enumerate(rows, 1) if HEADING.match(ln)), None)
    nation = is_nation(text)
    if at is None:
        if nation:
            return [
                Finding(
                    1,
                    "participants",
                    WARNING,
                    "no Participants section: a nation's article ends with its members, its "
                    "creator where it has one (MoS 8.4, 8.5)",
                )
            ]
        return []
    if not nation:
        return [
            Finding(
                at,
                "participants",
                WARNING,
                "Participants on a page that is not a nation: only a nation's article lists its "
                "members (MoS 8.5)",
            )
        ]
    found, members, creators = [], 0, 0
    for n in sorted(participants_lines(text)):
        m = MEMBER.match(rows[n - 1].strip())
        if not m:
            found.append(
                Finding(
                    n,
                    "participants",
                    WARNING,
                    "not a member line: write * [[User:Name]] (creator) or (participant), then "
                    "an optional short note (MoS 8.5)",
                )
            )
            continue
        members += 1
        if m.group(1).replace("_", " ").lower() in PLACEHOLDERS:
            found.append(
                Finding(
                    n,
                    "participants",
                    WARNING,
                    f"placeholder member: put the member's user name in place of {m.group(1)} "
                    "(MoS 8.5)",
                )
            )
        if m.group(2).lower() == "creator":
            creators += 1
            if creators > 1:
                found.append(
                    Finding(
                        n,
                        "participants",
                        WARNING,
                        "more than one creator: only the nation's current holder is its creator "
                        "(MoS 8.5)",
                    )
                )
    if not members:
        found.append(
            Finding(
                at,
                "participants",
                WARNING,
                "Participants lists no member: add at least one, its creator where it has one "
                "(MoS 8.4)",
            )
        )
    return sorted(found, key=lambda f: f.line)
