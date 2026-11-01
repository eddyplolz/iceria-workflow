"""Turn live wiki pages into the kit's canon/, style/ and templates/ files. The stewards' export
and a member's refresh_canon.py both build with this, so the two always agree."""

import json
import re
import shutil
import sys
from pathlib import Path

from iceria_wiki import WikiUnavailable

# (wiki title, file in the kit)
PAGES = (
    ("World Standards", "canon/world-standards.md"),
    ("History of Iceria", "canon/history-of-iceria.md"),
    ("Culture zones of Iceria", "canon/culture-zones.md"),
    ("Manual of Style", "style/manual-of-style.md"),
    ("AI use on Iceria", "style/ai-use-on-iceria.md"),
    ("Template:Infobox Country/doc", "templates/infobox-cheatsheet.md"),
)
CHARTER = ("Charter", "style/charter-extract.md")
CHARTER_CLAUSES = ("1.4", "3.1", "3.8", "5.1", "5.4", "5.6", "6.1")
PROPOSAL = "Template:Proposal/preload"
INFOBOXES = ("Infobox country", "Infobox Country")
IN_WORLD_DATE = re.compile(r"^\d{1,2} \w+ \d{4}$")
REDIRECT = re.compile(r"^\s*#REDIRECT\s*\[\[([^\]|#]+)", re.I)
CLAUSE_HEADING = re.compile(r"^(?:===\s*(\d+\.\d+)\s+(.+?)\s*===|### +(\d+\.\d+)\s+(.+?))\s*$")
MOS_HEADING = re.compile(r"^=+\s*(\d+(?:\.\d+)*)[.\s]", re.M)
COVERAGE_ROW = re.compile(r"^\|\s*(\d+(?:\.\d+)*)\s*\|", re.M)


class BuildError(Exception):
    pass


class PageMissing(BuildError):
    """The wiki answered and has no such page."""


class NationMissing(PageMissing):
    """A nation on the list has no page; `name` is the nation."""

    def __init__(self, name: str, message: str):
        super().__init__(message)
        self.name = name


class Builder:
    """Reads pages and writes kit files. fallback(title) may return stand-in text for a page the
    wiki could not serve, or None; only the stewards' export passes one."""

    def __init__(self, wiki, today, fallback=None, allow_missing=()):
        self.wiki, self.today, self.fallback = wiki, today, fallback
        self.allow_missing = set(allow_missing)
        self.pages: list[dict] = []
        self.missing: list[str] = []

    def read(self, title: str, follow: bool = True) -> tuple[str, dict]:
        """(text, record) for a page, the record also kept in self.pages for VERSION.json. A
        redirect is followed one hop, so a moved page is copied from where it now lives."""
        try:
            page = self.wiki.get_page(title)
        except WikiUnavailable as e:
            text = self.fallback(title) if self.fallback else None
            if text is None:
                raise BuildError(f"{title}: the wiki failed ({e})") from e
            print(f"FALLBACK: {title} from the stewards' copy ({e})", file=sys.stderr)
            record = {"title": title, "revid": None, "source": "mirror"}
        else:
            if page is None:
                raise PageMissing(f"{title}: no such page on the wiki")
            text = page["text"]
            record = {"title": title, "revid": page["revid"], "source": self.wiki.source}
        self.pages.append(record)
        m = REDIRECT.match(text) if follow else None
        if m:
            record["redirect"] = True
            return self.read(m.group(1).strip(), follow=False)
        return text, record

    def provenance(self, record: dict) -> str:
        if record["source"] == "mirror":
            where = "the stewards' copy, because the wiki could not be read"
        else:
            where = f"revision {record['revid']}"
        return (
            f'Copied from the Iceria wiki page "{record["title"]}" ({where}) on {self.today}. '
            "The live page outranks this copy."
        )

    def page_file(self, tree: Path, title: str, dest: str):
        text, record = self.read(title)
        text = text.replace("{{Documentation subpage}}", "").strip()
        _write(tree / dest, f"# {title}\n\n{self.provenance(record)}\n\n{text}\n")

    def charter(self, tree: Path):
        title, dest = CHARTER
        text, record = self.read(title)
        found = _clause_sections(text)
        missing = [c for c in CHARTER_CLAUSES if c not in found]
        if missing:
            raise BuildError(f"{title}: no clause {', '.join(missing)}")
        body = "\n\n".join(found[c] for c in CHARTER_CLAUSES)
        head = (
            f"# Charter (extract)\n\n{self.provenance(record)} Only the clauses a member "
            "drafting pages needs are here; the full Charter is on the wiki.\n\n"
        )
        _write(tree / dest, head + body + "\n")

    def proposal(self, tree: Path):
        text, _ = self.read(PROPOSAL)
        text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.S)
        text = re.sub(r"</?includeonly>", "", text).strip()
        _write(tree / "templates" / "proposal.wiki", text + "\n")

    def nations(self, tree: Path, names: list[str]):
        for name in names:
            try:
                text, record = self.read(name)
            except PageMissing as e:
                if name not in self.allow_missing:
                    raise NationMissing(name, str(e)) from e
                print(f"MISSING: {name} has no page; built without it", file=sys.stderr)
                self.missing.append(name)
                continue
            name = record["title"]
            fields = template_fields(text, INFOBOXES)
            if not fields:
                raise BuildError(f"{name}: no Infobox Country on the page")
            lines = [f"# {name}", "", self.provenance(record), "", "## Infobox", ""]
            lines += [f"- {k}: {v}" for k, v in fields.items() if v]
            lines += ["", "## Lead", "", _lead(text)]
            _write(tree / "canon" / "nations" / f"{_slug(name)}.md", "\n".join(lines) + "\n")

    def in_world_date(self) -> tuple[str | None, str | None]:
        try:
            out = self.wiki.expand("{{Iceria date}}").strip()
        except WikiUnavailable as e:
            return None, f"the wiki could not expand {{{{Iceria date}}}} ({e})"
        if IN_WORLD_DATE.match(out):
            return out, None
        return None, f"the wiki's {{{{Iceria date}}}} reads: {out}"


def build_canon(tree: Path, b: Builder, nations: list[str], strict_mos: bool = True) -> dict:
    """Every wiki-built file of the kit written into `tree`; the VERSION.json fields they set.
    The tree must already hold style/mos-coverage.md, which the live manual is checked against:
    a mismatch stops the stewards' export, and only warns a member, who cannot fix the map."""
    for title, dest in PAGES:
        b.page_file(tree, title, dest)
    drift = mos_drift(
        (tree / "style" / "manual-of-style.md").read_text(encoding="utf-8"),
        (tree / "style" / "mos-coverage.md").read_text(encoding="utf-8"),
    )
    if drift and strict_mos:
        raise BuildError(drift)
    if drift:
        print(
            f"WARNING: {drift} Until the stewards do, check those sections by hand.",
            file=sys.stderr,
        )
    b.charter(tree)
    b.proposal(tree)
    shutil.rmtree(tree / "canon" / "nations", ignore_errors=True)
    b.nations(tree, nations)
    date, reason = b.in_world_date()
    _write(tree / "canon" / "calendar.md", calendar(date, reason))
    fields = {"built": str(b.today), "source": b.wiki.source, "in_world_date": date}
    if reason:
        fields["in_world_date_reason"] = reason
    fields["nations"] = list(nations)
    if b.missing:
        fields["missing_nations"] = b.missing
    fields["pages"] = b.pages
    return fields


def knowledge(tree: Path):
    """project-pack/knowledge/: the kit's reading as flat files for a Projects upload."""
    dest = tree / "project-pack" / "knowledge"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    for path in sorted((tree / "style").glob("*.md")) + sorted((tree / "canon").glob("*.*")):
        shutil.copyfile(path, dest / path.name)
    for path in sorted((tree / "canon" / "nations").glob("*.md")):
        shutil.copyfile(path, dest / f"nation-{path.name}")
    for path in sorted((tree / "templates").glob("*.wiki")):
        shutil.copyfile(path, dest / f"template-{path.stem}.txt")
    shutil.copyfile(tree / "templates" / "infobox-cheatsheet.md", dest / "infobox-cheatsheet.md")
    shutil.copyfile(tree / "VERSION.json", dest / "VERSION.json")


def _split(body: str) -> list[str]:
    """Split a template's body on its own pipes, not those inside links or nested templates."""
    parts, depth, cur, i = [], 0, [], 0
    while i < len(body):
        two = body[i : i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            cur.append(two)
            i += 2
        elif body[i] == "|" and depth == 0:
            parts.append("".join(cur))
            cur, i = [], i + 1
        else:
            cur.append(body[i])
            i += 1
    parts.append("".join(cur))
    return parts


def template_fields(text: str, names) -> dict:
    """The named fields of the first box on the page whose template is one of `names`."""
    for m in re.finditer(r"\{\{\s*([^|{}\n]+?)\s*\n?\|", text):
        if m.group(1).strip() not in names:
            continue
        depth, i = 1, m.start() + 2
        while depth and i < len(text):
            two = text[i : i + 2]
            if two == "{{":
                depth, i = depth + 1, i + 2
            elif two == "}}":
                depth, i = depth - 1, i + 2
            else:
                i += 1
        body = text[m.start() + 2 : i - 2]
        fields = {}
        for part in _split(body)[1:]:
            k, eq, v = part.partition("=")
            if eq:
                fields[k.strip()] = v.strip()
        return fields
    return {}


def _clause_sections(text: str) -> dict[str, str]:
    """{clause: its heading and text} for every clause given its own heading, wiki or Markdown."""
    found, current = {}, None
    for line in text.splitlines():
        m = CLAUSE_HEADING.match(line)
        if m:
            current = m.group(1) or m.group(3)
            found[current] = [f"## {current} {m.group(2) or m.group(4)}"]
        elif re.match(r"^(?:==|#{1,2} )", line):
            current = None
        elif current:
            found[current].append(line)
    return {k: "\n".join(v).strip() for k, v in found.items()}


def _lead(text: str) -> str:
    """The article's lead: from the first bold line up to the first heading."""
    lines, started = [], False
    for line in text.splitlines():
        if line.startswith("=="):
            break
        if not started and line.startswith("'''"):
            started = True
        if started:
            lines.append(line)
    return "\n".join(lines).strip()


def _slug(name: str) -> str:
    # The name comes from the wiki (a redirect target), so it becomes a file name only through
    # word characters: a title like ..\x or C:\x must never write outside canon/nations.
    slug = re.sub(r"[^\w-]+", "-", name.lower()).strip("-")
    if not slug:
        raise BuildError(f"{name!r}: no letters to name its file by")
    return slug


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data):
    _write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def calendar(date: str | None, reason: str | None) -> str:
    if date:
        now = f"Today's in-world date is {date}."
    else:
        now = (
            f"The in-world calendar has not started ({reason}). Until it does, history ends in "
            "1999 and figures are given for 2000 (Manual of Style 5.1)."
        )
    return (
        f"# Calendar\n\n{now}\n\nHow the calendar runs is World Standards section 5 "
        "(canon/world-standards.md).\n"
    )


def mos_sections(text: str) -> set[str]:
    """The numbered sections of the manual that have no numbered subsections. The manual's own
    examples (== References ==, == Summary ==) carry no number and are skipped."""
    numbers = set(MOS_HEADING.findall(text))
    return {n for n in numbers if not any(m.startswith(n + ".") for m in numbers)}


def coverage_rows(text: str) -> list[str]:
    """The section numbers in the first column of style/mos-coverage.md, in table order."""
    return COVERAGE_ROW.findall(text)


def mos_drift(mos: str, coverage: str) -> str | None:
    """Why the coverage map no longer matches the manual, or None when every section has a row."""
    live, rows = mos_sections(mos), set(coverage_rows(coverage))

    def key(n):
        return [int(p) for p in n.split(".")]

    problems = []
    if unmapped := sorted(live - rows, key=key):
        problems.append(f"no row for {', '.join(unmapped)}")
    if stale := sorted(rows - live, key=key):
        problems.append(f"no such section for rows {', '.join(stale)}")
    if not problems:
        return None
    return (
        f"Manual of Style changed: {'; '.join(problems)}. "
        "Update style/mos-coverage.md to match the live manual."
    )
