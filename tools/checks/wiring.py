"""Wiring against the live wiki: categories, infoboxes and links, read-only.

Needs ctx["wiki"] (an iceria_wiki.Wiki); without it nothing is checked. A category the wiki does
not have and an infobox the Manual of Style does not list are errors; a red page link, an
infobox field the template lacks, a nation category the draft never mentions and a doubled
category are warnings, since a red link only means "not written yet" (Charter 1.4).
"""

import re

from checks import ERROR, WARNING, Finding, lines, prose_lines, strip_refs
from checks.links import CATEGORY, LINK, _norm

# User pages are not articles: a member's own page (MoS 8.5) may well be unwritten.
NOT_PAGES = re.compile(r"^(?:File|Image|Media|Category|User)\s*:", re.I)
PLACEHOLDERS = {"nation", "other nation", "name"}
# MoS 14.1.
INFOBOXES = {
    n.lower()
    for n in (
        "Country|Person|officeholder|Settlement|building|royal house|order|national military|"
        "military conflict|legislature|political party|election|written work"
    ).split("|")
}
# Infobox Country/doc, from the infobox draft: the fallback when the wiki's /doc cannot be read.
COUNTRY_FIELDS = {
    f.lower()
    for f in (
        "conventional_long_name common_name native_name image_flag image_coat symbol_type "
        "national_motto national_anthem image_map map_caption capital largest_city "
        "official_languages languages_type languages ethnic_groups ethnic_groups_year religion "
        "religion_year demonym government_type leader_title1 leader_name1 leader_title2 "
        "leader_name2 legislature upper_house lower_house sovereignty_type established_event1 "
        "established_date1 area_km2 percent_water population_estimate population_estimate_year "
        "population_census population_census_year GDP_nominal GDP_nominal_year Gini Gini_year "
        "HDI HDI_year currency currency_code utc_offset time_zone drives_on calling_code "
        "continent culture_zone culture_twist people tier status"
    ).split()
}
INFOBOX = re.compile(r"\{\{\s*infobox[ _]+([^|{}\n]+?)\s*(?=[|}]|$)", re.I)
PARAM = re.compile(r"^\s*\|\s*([\w ]+?)\s*=")
DOC_PARAM = re.compile(r"\|\s*([\w ]+?)\s*=")
REDIRECT = re.compile(r"#REDIRECT\s*\[\[([^\]|]+)", re.I)
PLACE_LEAD = re.compile(r"\bis an? [^.]*?\b(?:city|town|village|port|settlement|harbou?r)\b", re.I)
NATION_LEAD = re.compile(
    r"\bis an? [^.]*?\b(?:nation|country|kingdom|republic|state|empire)\b", re.I
)


def targets(text: str) -> dict[str, int]:
    """{page title: line it is first linked on}, leaving out files, categories, user pages and comments."""
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


def _doc_fields(wiki, name: str) -> set[str]:
    """Field names in the <pre> block of the template's /doc page, following a redirect."""
    title = f"Template:Infobox {name}/doc"
    for _ in range(3):
        page = wiki.get_page(title)
        if page is None:
            return set()
        if redirect := REDIRECT.match(page["text"].strip()):
            title = redirect.group(1).strip()
            continue
        pre = re.search(r"<pre>(.*?)</pre>", page["text"], re.S | re.I)
        return {p.strip().lower() for p in DOC_PARAM.findall(pre.group(1))} if pre else set()
    return set()


def _infoboxes(text: str, ctx: dict) -> list[Finding]:
    found, wiki, rows = [], ctx["wiki"], lines(text)
    lead = next((strip_refs(ln) for _, ln in prose_lines(text)), "")
    for i, row in enumerate(rows):
        m = INFOBOX.search(row)
        if not m:
            continue
        n, name = i + 1, m.group(1).replace("_", " ")
        if name.lower() not in INFOBOXES:
            found.append(
                Finding(n, "wiring", ERROR, f"unknown infobox: {{{{Infobox {name}}}}} (MoS 14.1)")
            )
            continue
        key = name.lower()
        if (key == "country" and PLACE_LEAD.search(lead)) or (
            key == "settlement" and NATION_LEAD.search(lead) and not PLACE_LEAD.search(lead)
        ):
            found.append(
                Finding(
                    n,
                    "wiring",
                    WARNING,
                    f"infobox does not fit the page: {{{{Infobox {name}}}}} on this kind of page (MoS 14.1)",
                )
            )
        fields, depth = _doc_fields(wiki, name), 0
        if not fields and key == "country":
            fields = COUNTRY_FIELDS
        for j in range(i, len(rows)):
            depth += rows[j].count("{{") - rows[j].count("}}")
            p = PARAM.match(rows[j]) if depth >= 1 and j > i else None
            if p and fields and p.group(1).lower() not in fields:
                found.append(
                    Finding(
                        j + 1,
                        "wiring",
                        WARNING,
                        f"infobox field not in the template: {p.group(1)} (Infobox {name})",
                    )
                )
            if depth <= 0:
                break
    return found


# MoS 17.3: the only subcategories a nation may have, each named "<Topic> of <Nation>".
SUBCATEGORY_TOPICS = {
    "people",
    "politics",
    "history",
    "geography",
    "military",
    "economy",
    "culture",
    "organizations",
}


def _case_and_shape(n: int, cat: str, nations) -> list[Finding]:
    found = []
    if (m := re.match(r"(.+?) of (.+)$", cat)) and m.group(2) in nations:
        if m.group(1).lower() not in SUBCATEGORY_TOPICS:
            found.append(
                Finding(
                    n,
                    "wiring",
                    WARNING,
                    f"nation subcategory not in the manual's list: {cat}; only people, politics, "
                    "history, geography, military, economy, culture and organizations (MoS 17.3)",
                )
            )
    return found


def _home_nation(text: str, nations) -> str | None:
    """The nation an infobox places the page in (subdivision_name), else None."""
    m = re.search(
        r"^\s*\|\s*subdivision_name\s*=\s*\[\[\s*([^\]|#]+?)\s*(?:[|#][^\]]*)?\]\]", text, re.M
    )
    name = _norm(m.group(1)) if m else None
    return name if name in nations else None


def _nation_of(category: str, nations) -> str | None:
    for nation in nations:
        if category == nation or category.endswith(" of " + nation):
            return nation
    return None


def _categories(text: str, ctx: dict) -> list[Finding]:
    found, wiki, nations = [], ctx["wiki"], ctx.get("nations", {})
    title = (ctx.get("title") or "").strip()
    filed = [
        (n, _norm(m.group(1)))
        for n, ln in enumerate(lines(text), 1)
        for m in CATEGORY.finditer(ln)
        if m.group(1).strip().lower() not in PLACEHOLDERS
    ]
    body = "\n".join(ln for ln in lines(text) if not CATEGORY.search(ln))
    live = wiki.categories_exist([c for _, c in filed]) if filed else {}
    for n, cat in filed:
        if not live.get(cat, False):
            found.append(
                Finding(
                    n,
                    "wiring",
                    ERROR,
                    f"category does not exist: {cat}; use an existing category (MoS 17.6). If "
                    f"{cat} is your own new nation, a steward makes its category once the nation "
                    "is provisional (MoS 17.2): keep the line, and the page waits for that "
                    "before it is posted",
                )
            )
        found += _case_and_shape(n, cat, nations)
        nation = _nation_of(cat, nations)
        if nation and nation != title and not re.search(rf"\b{re.escape(nation)}\b", body):
            found.append(
                Finding(
                    n,
                    "wiring",
                    WARNING,
                    f"category names a nation the draft never mentions: {cat} (MoS 17.2)",
                )
            )
    by_nation = {}
    for n, cat in filed:
        if nation := _nation_of(cat, nations):
            by_nation.setdefault(nation, []).append((n, cat))
    for nation, cats in by_nation.items():
        if nation != title and any(c == nation for _, c in cats) and len(cats) > 1:
            found.append(
                Finding(
                    next(n for n, c in cats if c == nation),
                    "wiring",
                    WARNING,
                    f"category also filed in a broader one: {nation} beside "
                    f"{', '.join(c for _, c in cats if c != nation)}; keep the most specific "
                    "(MoS 17.4)",
                )
            )
    home = _home_nation(text, nations)
    if home and home != title:
        for nation, cats in by_nation.items():
            if nation != home and home not in by_nation:
                found.append(
                    Finding(
                        cats[0][0],
                        "wiring",
                        WARNING,
                        f"category names another nation than the page is in: {cats[0][1]}, "
                        f"but the page is in {home} (MoS 17.2)",
                    )
                )
    for nation, cats in by_nation.items():
        generic = [(n, c) for n, c in filed if c.lower() in SUBCATEGORY_TOPICS]
        if nation != title and generic:
            found.append(
                Finding(
                    generic[0][0],
                    "wiring",
                    WARNING,
                    f"generic category beside the nation's own: {generic[0][1]} beside "
                    f"{cats[0][1]}; use '{generic[0][1]} of {nation}' (MoS 17.4)",
                )
            )
            break
    return found


def run(text: str, ctx: dict) -> list[Finding]:
    wiki = ctx.get("wiki")
    if wiki is None:
        return []
    found = _infoboxes(text, ctx) + _categories(text, ctx)
    first = targets(text)
    own = _norm(ctx.get("title") or "")
    first.pop(own, None)
    for n, page in find(first, wiki) if first else []:
        found.append(
            Finding(n, "wiring", WARNING, f"page not written yet: [[{page}]] is a red link")
        )
    return sorted(found, key=lambda f: f.line)
