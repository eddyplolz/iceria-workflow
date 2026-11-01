"""Rebuild canon/, style/ and templates/ from the live wiki, so the kit matches today's pages.

    python tools/refresh_canon.py            exit 0 refreshed, 1 if anything failed
    python tools/refresh_canon.py --check    exit 0 current, 1 a refresh is due, 2 could not check

With a bot password (python tools/setup_bot.py) it reads the wiki logged in as your bot; without
one it reads as a visitor, which works until the wiki asks visitors for a browser check. Either
way it reads only, and a bot password with more than Basic rights is refused. The new copy is
built aside and renamed in path by path; a failure puts back each path already renamed, and names
any it could not.
"""

import argparse
import datetime
import json
import shutil
import sys
import tempfile
from pathlib import Path

import kit_python  # noqa: F401  stops on Python < 3.10

# isort: split
import cred_store
import secrets_scan
import setup_bot
from canon_pages import Builder, BuildError, build_canon, knowledge, write_json
from iceria_wiki import Wiki, WikiUnavailable

KIT = Path(__file__).resolve().parents[1]
# What a refresh rewrites; everything else in the kit (tools, skills, your drafts) is left alone.
REBUILT = ("canon", "style", "templates", "project-pack/knowledge", "VERSION.json")


def refresh(kit: Path, wiki, today: datetime.date, creds: tuple[str, str] | None) -> int:
    hits = secrets_scan.scan(kit)
    if hits:
        print("\n".join(hits), file=sys.stderr)
        print(
            "FAILED: a file of the kit holds what looks like a bot password; nothing was read. "
            "Remove it, and if it was real, revoke it at Special:BotPasswords.",
            file=sys.stderr,
        )
        return 1
    old = json.loads((kit / "VERSION.json").read_text(encoding="utf-8"))
    keeps = f"your kit keeps the copy from {old['built']}"
    # Built inside the kit, so the swap is a rename on one drive: never a copy that can stop
    # half-done.
    work = Path(tempfile.mkdtemp(prefix=".refresh-", dir=kit))
    keep_work = False
    try:
        try:
            if creds:
                # A password from the environment never went through setup_bot, so its rights
                # are checked here too.
                problem = setup_bot.vet_login(wiki, *creds)
                if problem:
                    print(f"FAILED: {problem}; {keeps}.", file=sys.stderr)
                    print("Check it with python tools/setup_bot.py --check.", file=sys.stderr)
                    return 1
                read_as = "bot"
            else:
                print(
                    "NOTICE: no bot password set up, so the wiki is read as a visitor. "
                    "Run python tools/setup_bot.py to read as your own bot.",
                    file=sys.stderr,
                )
                read_as = "anonymous"
            tree = work / "kit"
            for folder in ("canon", "style", "templates"):
                shutil.copytree(kit / folder, tree / folder)
            # No fallback: a member's kit holds only what the wiki served today.
            b = Builder(wiki, today, None, old.get("missing_nations", ()))
            fields = build_canon(tree, b, old["nations"], strict_mos=False)
            write_json(
                tree / "VERSION.json",
                {
                    "kit_version": old["kit_version"],
                    "map_lock_version": old["map_lock_version"],
                    "read_as": read_as,
                    **fields,
                },
            )
            knowledge(tree)
        except (BuildError, WikiUnavailable) as e:
            print(f"FAILED: {e}; {keeps}.", file=sys.stderr)
            return 1
        try:
            _swap(kit, tree, work / "old")
        except SwapFailed as e:
            # A file held open (an editor, a virus scanner) stopped the swap.
            if e.stranded:
                keep_work = True
                print(
                    f"FAILED: could not swap in the new copy ({e.cause}), nor put all of the old "
                    f"one back: {', '.join(e.stranded)} are in {work / 'old'}. Move them back "
                    "into the kit by hand.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"FAILED: could not swap in the new copy ({e.cause}); put back "
                    f"{', '.join(e.restored)}, so {keeps}.",
                    file=sys.stderr,
                )
                print("Close any editor open on the kit and run it again.", file=sys.stderr)
            return 1
    finally:
        if not keep_work:
            shutil.rmtree(work, ignore_errors=True)
    print(f"refreshed {len(fields['pages'])} pages as {read_as} on {today}")
    return 0


def check(kit: Path, wiki, today: datetime.date, creds: tuple[str, str] | None) -> int:
    """Compare the copy with the live wiki in one request per 50 pages, and write nothing."""
    v = json.loads((kit / "VERSION.json").read_text(encoding="utf-8"))
    copied = {p["title"]: p["revid"] for p in v["pages"]}
    titles = list(dict.fromkeys([*copied, *v.get("missing_nations", ())]))
    if creds and (problem := setup_bot.vet_login(wiki, *creds)):
        print(f"could not check: {problem}", file=sys.stderr)
        return 2
    try:
        live = wiki.latest_revids(titles)
    except WikiUnavailable as e:
        print(f"could not check: {e}", file=sys.stderr)
        return 2
    age = (today - datetime.date.fromisoformat(v["built"])).days
    # A copy without a revid came from the stewards' copy, so it is due a live read too.
    changed = [t for t in copied if copied[t] is None or live.get(t) != copied[t]]
    written = [t for t in v.get("missing_nations", ()) if live.get(t)]
    if not changed and not written:
        print(f"current: the copy from {v['built']} ({age} days old) matches the wiki")
        return 0
    print(f"a refresh is due: the copy from {v['built']} is {age} days old")
    for t in changed:
        print(f"  changed since the copy: {t}")
    for t in written:
        print(f"  now has a page: {t}")
    print("Run python tools/refresh_canon.py to update the kit.")
    return 1


class SwapFailed(Exception):
    """The swap stopped on `cause`. `restored` names the kit paths put back as they were;
    `stranded` names those whose old copy is still set aside, which only a person can move."""

    def __init__(self, cause: OSError, restored: list[str], stranded: list[str]):
        super().__init__(cause)
        self.cause, self.restored, self.stranded = cause, restored, stranded


def _swap(kit: Path, tree: Path, old: Path):
    """Each rebuilt path renamed in from `tree`, the kit's copy set aside in `old` first.

    On a failure every rename already made is undone, newest first, and SwapFailed raised.
    """
    done = []
    try:
        for rel in REBUILT:
            done.append(rel)
            if (kit / rel).exists():
                (old / rel).parent.mkdir(parents=True, exist_ok=True)
                (kit / rel).rename(old / rel)
            (kit / rel).parent.mkdir(parents=True, exist_ok=True)
            (tree / rel).rename(kit / rel)
    except OSError as e:
        restored, stranded = [], []
        for rel in reversed(done):
            try:
                if (kit / rel).exists() and not (tree / rel).exists():
                    (kit / rel).rename(tree / rel)
                if (old / rel).exists():
                    (old / rel).rename(kit / rel)
                    restored.insert(0, rel)
            except OSError:
                stranded.insert(0, rel)
        raise SwapFailed(e, restored, stranded) from e


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--check", action="store_true", help="say whether a refresh is due; write nothing"
    )
    args = ap.parse_args()
    found = cred_store.get()
    if found:
        print(f"reading as the bot password from {found[1]}")
    run = check if args.check else refresh
    return run(KIT, Wiki(), datetime.date.today(), found[0] if found else None)


if __name__ == "__main__":
    sys.exit(main())
