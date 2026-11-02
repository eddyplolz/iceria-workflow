"""Bold only where the Manual of Style allows it.

MoS 3.1 bolds the subject's name (and its other names) in the first sentence; 6.3 allows bold
"only in the lead, for the title and its other names"; 4.3 bans bolded lead-ins; 4.1 bans bold in
headings. Infobox lines and wikitable cells are not prose and are not read.
"""

import re

from checks import ERROR, FURNITURE, HEADING, WARNING, Finding, lines

# MediaWiki closes an unclosed ''' at the end of its line, so the span runs there.
BOLD = re.compile(r"'''.+?(?:'''|$)|<(b|strong)\b[^>]*>.*?</\1\s*>", re.IGNORECASE)


def _table_cells(rows: list[str]) -> set[int]:
    """0-indexed cell lines of a {| ... |} table that closes; an unclosed table exempts nothing."""
    inside: set[int] = set()
    stack: list[set[int]] = []
    for i, ln in enumerate(rows):
        s = ln.strip()
        if s.startswith("{|"):
            stack.append(set())
        elif s.startswith("|}"):
            if stack:
                inside |= stack.pop()
        elif stack and s[:1] in ("|", "!") and not s.startswith("|-"):
            stack[-1].add(i)
    return inside


def _lead_in(line: str, m: re.Match) -> bool:
    inner = re.sub(r"<[^>]*>|'", "", m.group(0)).strip()
    return not line[: m.start()].strip() and (
        inner.endswith(":") or line[m.end() :].lstrip().startswith(":")
    )


def run(text: str, ctx: dict) -> list[Finding]:
    rows = lines(text)
    cells = _table_cells(rows)
    found, depth, in_lead, para, lead_bold, first_line = [], 0, True, "before", False, None
    lead_names: list[str] = []
    for i, line in enumerate(rows):
        n = i + 1
        if HEADING.match(line):
            in_lead = False
            for m in BOLD.finditer(line):
                found.append(
                    Finding(n, "bold", ERROR, f"bold in a heading: {m.group(0)} (MoS 4.1)")
                )
            continue
        furniture = depth > 0 or bool(FURNITURE.match(line))
        depth = max(0, depth + line.count("{{") - line.count("}}"))
        if in_lead and not furniture:
            if line.strip():
                if para == "before":
                    para, first_line = "first", n
            elif para == "first":
                para = "after"
        for m in BOLD.finditer(line):
            if _lead_in(line, m):
                why = "bolded lead-in (MoS 4.3)"
            elif i in cells or line.lstrip().startswith("|+"):
                continue
            elif in_lead and furniture:
                continue
            elif in_lead and para == "first":
                lead_bold = True
                lead_names.append(re.sub(r"<[^>]*>|'", "", m.group(0)).strip())
                continue
            elif in_lead:
                why = "bold in the lead after its first paragraph (MoS 6.3)"
            else:
                why = "bold in the body (MoS 6.3)"
            found.append(Finding(n, "bold", ERROR, f"{m.group(0)}: {why}"))
    title = (ctx.get("title") or "").strip().lower()
    if lead_bold and title and title not in {b.lower() for b in lead_names}:
        found.append(
            Finding(
                first_line,
                "bold",
                WARNING,
                f"bold name is not the title: the first sentence bolds {lead_names[0]!r}; bold "
                f"the title {ctx['title'].strip()!r} there, or retitle the page (MoS 3.1)",
            )
        )
    if first_line and not lead_bold:
        found.append(
            Finding(first_line, "bold", WARNING, "the lead does not bold the title (MoS 3.1)")
        )
    return sorted(found, key=lambda f: f.line)
