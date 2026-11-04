"""Check a wikitext draft against the Iceria Manual of Style.

    py tools/check.py drafts/my-nation.wiki --title "My Nation"

Prints one line per finding (file:line: check: level: message) and a count. Exits 1 when any
finding is an error, and 2 when the draft is not saved as UTF-8; warnings are for the writer to
judge and never fail the run. Reads the kit's canon/geography.json, canon/culture-zones.json and
VERSION.json when they exist, so names and dates are checked against the world as built. With
--humanizer, also runs humanizer-audit (README.md: step 7 on a Mac, step 5 on Windows) when it is installed.
"""

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import kit_python  # noqa: F401  stops on Python < 3.10

# isort: split
from checks import (
    ERROR,
    ai_tells,
    bold,
    clashes,
    dashes,
    dates,
    headings,
    links,
    markup,
    names,
    numbers,
    participants,
    proposal,
    refs,
    spelling,
    voice,
    wiring,
)
from iceria_wiki import Wiki, WikiUnavailable

CHECKS = [
    markup,
    headings,
    bold,
    dashes,
    refs,
    links,
    dates,
    numbers,
    names,
    participants,
    proposal,
    clashes,
    voice,
    ai_tells,
    spelling,
]
KIT_ROOT = Path(__file__).resolve().parent.parent
# The "# Title" heading and "- key: value" infobox lines that canon_pages.Builder.nations writes.
INFOBOX_LINE = re.compile(r"^- (common_name|capital): (.*)$", re.M)
HEADING = re.compile(r"^# (.+)$", re.M)


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def load_ctx(root: Path) -> dict:
    ctx = {}
    geo = _read(root / "canon" / "geography.json")
    if geo:
        ctx["names"] = [
            item["name"] for items in geo.values() if isinstance(items, list) for item in items
        ]
    zones = _read(root / "canon" / "culture-zones.json")
    if zones:
        ctx["families"] = sorted({z["family"] for z in zones["zones"]})
    nations, pages = {}, {}
    for page in sorted((root / "canon" / "nations").glob("*.md")):
        text = page.read_text(encoding="utf-8")
        fields = dict(INFOBOX_LINE.findall(text))
        if fields.get("common_name"):
            name, capital = clashes.plain(fields["common_name"]), fields.get("capital")
            nations[name] = capital and clashes.plain(capital)
            if (heading := HEADING.search(text)) and heading.group(1) != name:
                pages[heading.group(1)] = name
    if nations:
        ctx["nations"] = nations
    if pages:
        ctx["nation_pages"] = pages
    version = _read(root / "VERSION.json")
    if version and version.get("in_world_date"):
        ctx["in_world_date"] = version["in_world_date"]
    return ctx


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def pip_install(package: str) -> str:
    """The install command for this Python, so pip lands where the kit looks (a bare "python" may
    be another install or the Microsoft Store stub)."""
    exe = f'"{sys.executable}"' if " " in sys.executable else sys.executable
    return f"{exe} -m pip install {package}"


def humanizer_command() -> list[str] | None:
    """The command that runs the AI-tell audit, or None when humanizer-pro is not installed."""
    if audit := shutil.which("humanizer-audit"):
        return [audit]
    # On Windows pip puts the command in a Scripts folder that is often not on PATH.
    if importlib.util.find_spec("humanizer_audit"):
        return [sys.executable, "-m", "humanizer_audit"]
    return None


def read_draft(path: Path) -> str:
    # Notepad saves UTF-8 with a byte-order mark and PowerShell's > saves UTF-16; both are read
    # as the text they hold, since a BOM left in front of the lead hides its bold.
    data = path.read_bytes()
    encoding = "utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return data.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")


def open_draft(path: Path) -> str | None:
    """The draft's text, or None after saying on stderr why it could not be read and how to fix it."""
    try:
        return read_draft(path)
    # Windows refuses to open a folder with PermissionError, so a folder lands here too.
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        print(
            f"no file at {path.resolve()}: check the name and folder, or run the command from "
            "the folder that holds the draft.",
            file=sys.stderr,
        )
    except UnicodeDecodeError as e:
        print(
            f"{path.name} is not UTF-8 ({e.reason} at byte {e.start}): save it as UTF-8 and run "
            "the check again.",
            file=sys.stderr,
        )
    return None


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("draft", type=Path)
    ap.add_argument("--title", help="the page title, for the lead and heading checks")
    ap.add_argument(
        "--root", type=Path, default=KIT_ROOT, help="kit folder holding canon/ and VERSION.json"
    )
    ap.add_argument(
        "--humanizer", action="store_true", help="also run humanizer-audit if it is installed"
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="skip the read-only wiki query (categories, infobox fields and red links)",
    )
    args = ap.parse_args(argv)

    text = open_draft(args.draft)
    if text is None:
        return 2
    ctx = load_ctx(args.root)
    if args.title:
        ctx["title"] = args.title
    # A {{Proposal}} form is filled in on a Proposal: page, not written as an article: it has no
    # lead, short description or category, and its guidance comments are the form itself.
    form = re.match(r"\s*\{\{\s*Proposal\s*(?:\||\n|<)", text, re.I)
    ctx["form"] = bool(form)
    found = [f for c in CHECKS if not (form and c is markup) for f in c.run(text, ctx)]
    if not args.offline:
        try:
            found += wiring.run(text, {**ctx, "wiki": Wiki()})
        except WikiUnavailable as e:
            print(
                f"NOT CHECKED: the wiki could not be reached ({e}), so categories, infobox "
                "fields and links were not looked up. Check your connection and run again, or "
                "add --offline to skip them.",
                file=sys.stderr,
            )
            return 2
    found.sort(key=lambda f: f.line)
    name = args.draft.name
    for f in found:
        print(f.format(name))
    errors = sum(f.level == ERROR for f in found)
    print(f"{name}: {_plural(errors, 'error')}, {_plural(len(found) - errors, 'warning')}")

    if args.offline:
        print(
            "wiring skipped (--offline): categories, infobox fields and links not checked",
            file=sys.stderr,
        )

    if args.humanizer:
        # The audit writes to the same stream; flush so its report follows ours when piped.
        sys.stdout.flush()
        if audit := humanizer_command():
            subprocess.run([*audit, str(args.draft)], check=False)
        else:
            print(
                "humanizer-audit is not installed, so the AI-tell audit was skipped. Install it "
                f"with: {pip_install('humanizer-pro')} (README.md: 'Set up a Mac (once)' step 7, "
                "or 'Set up Windows (once)' step 5)",
                file=sys.stderr,
            )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
