"""List the links in a draft that point at pages nobody has written yet.

    python tools/redlinks.py drafts/my-city.wiki

A red link means "not written yet" and nothing more (Charter 1.4): the place, person or treaty may
well exist in Iceria, and the link waits for its page. Use the list to decide which links you mean
to keep, and never as proof that something does not exist. It reads the wiki, one request per 50
links, and writes nothing. Exit 0 with the list, 2 when the wiki could not be reached.
"""

import argparse
import re
import sys
from pathlib import Path

import kit_python  # noqa: F401  stops on Python < 3.10

# isort: split
from check import read_draft
from checks import lines
from checks.links import LINK, _norm
from iceria_wiki import Wiki, WikiUnavailable

NOT_PAGES = re.compile(r"^(?:File|Image|Media|Category)\s*:", re.I)


def targets(text: str) -> dict[str, int]:
    """{page title: line it is first linked on}, leaving out files, categories and comments."""
    first = {}
    for n, line in enumerate(lines(text), 1):
        for m in LINK.finditer(line):
            title = _norm(m.group(1))
            if not NOT_PAGES.match(title):
                first.setdefault(title, n)
    return first


def find(first: dict[str, int], wiki) -> list[tuple[int, str]]:
    """(line first linked on, title) for each of targets() with no page on the wiki."""
    live = wiki.latest_revids(list(first))
    return [(n, t) for t, n in first.items() if live.get(t) is None]


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("draft", type=Path)
    args = ap.parse_args(argv)
    first = targets(read_draft(args.draft))
    try:
        red = find(first, Wiki())
    except WikiUnavailable as e:
        print(f"could not check: {e}", file=sys.stderr)
        return 2
    for n, title in red:
        print(f"{args.draft.name}:{n}: [[{title}]]")
    print(
        f"{len(red)} of {len(first)} linked pages are not written yet. A red link is open, never "
        "proof that something does not exist (Charter 1.4)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
