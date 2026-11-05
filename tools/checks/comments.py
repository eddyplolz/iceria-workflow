"""Hidden comments: a page on Iceria carries none.

A <!-- --> comment does not show on the page but stays in its source, where every later editor
reads it, so the stewards want none left on any page: article, proposal form or project page.
Text inside <nowiki> or <pre> shows on the page, so it is not a comment. Runs on every draft.
"""

from checks import ERROR, HIDDEN, Finding


def run(text: str, ctx: dict) -> list[Finding]:
    return [
        Finding(
            text.count("\n", 0, m.start()) + 1,
            "comments",
            ERROR,
            "hidden comment: delete it, pages on Iceria carry no <!-- --> comments",
        )
        for m in HIDDEN.finditer(text)
        if m.group(0).startswith("<!--")
    ]
