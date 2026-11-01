"""Check a wikitext draft against the Iceria Manual of Style.

    py tools/check.py drafts/my-nation.wiki --title "My Nation"

Prints one line per finding (file:line: check: level: message) and a count. Exits 1 when any
finding is an error, and 2 when the draft is not saved as UTF-8; warnings are for the writer to
judge and never fail the run. Reads the kit's canon/geography.json, canon/culture-zones.json and
VERSION.json when they exist, so names and dates are checked against the world as built. With
--humanizer, also runs humanizer-audit (setup step 5) when it is installed.
"""

import argparse
import importlib.util
import json
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
    dashes,
    dates,
    headings,
    markup,
    names,
    refs,
    spelling,
    voice,
)

CHECKS = [markup, headings, bold, dashes, refs, dates, names, voice, ai_tells, spelling]
KIT_ROOT = Path(__file__).resolve().parent.parent


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
    version = _read(root / "VERSION.json")
    if version and version.get("in_world_date"):
        ctx["in_world_date"] = version["in_world_date"]
    return ctx


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def read_draft(path: Path) -> str:
    # Notepad saves UTF-8 with a byte-order mark and PowerShell's > saves UTF-16; both are read
    # as the text they hold, since a BOM left in front of the lead hides its bold.
    data = path.read_bytes()
    encoding = "utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return data.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")


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
    args = ap.parse_args(argv)

    try:
        text = read_draft(args.draft)
    except UnicodeDecodeError as e:
        print(
            f"{args.draft.name} is not UTF-8 ({e.reason} at byte {e.start}): save it as UTF-8 "
            "and run the check again.",
            file=sys.stderr,
        )
        return 2
    ctx = load_ctx(args.root)
    if args.title:
        ctx["title"] = args.title
    found = sorted((f for c in CHECKS for f in c.run(text, ctx)), key=lambda f: f.line)
    name = args.draft.name
    for f in found:
        print(f.format(name))
    errors = sum(f.level == ERROR for f in found)
    print(f"{name}: {_plural(errors, 'error')}, {_plural(len(found) - errors, 'warning')}")

    if args.humanizer:
        audit = shutil.which("humanizer-audit")
        if audit:
            subprocess.run([audit, str(args.draft)], check=False)
        # On Windows pip puts the command in a Scripts folder that is often not on PATH.
        elif importlib.util.find_spec("humanizer_audit"):
            subprocess.run([sys.executable, "-m", "humanizer_audit", str(args.draft)], check=False)
        else:
            print(
                "humanizer-audit is not installed, so the AI-tell audit was skipped. Install it "
                "with: python -m pip install humanizer-pro (setup step 5 in README.md)",
                file=sys.stderr,
            )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
