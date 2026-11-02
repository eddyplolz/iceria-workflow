"""Check this computer's setup for the kit, one line per part, and change nothing.

    python tools/doctor.py

Each line starts OK or FIX, and a FIX line says the one step that fixes it; an optional part that
is not installed is an OK line saying how to add it. It reads the wiki once as a guest, looks up
the saved bot login's name (never its password), and writes nothing. It ends with a block to send
the kit's maintainer when something breaks, which says whether a login is saved but never which one. Exit 0 when
every check is OK, 1 when any needs a fix.
"""

import argparse
import datetime
import json
import platform
import ssl
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import kit_python  # noqa: F401  stops on Python < 3.10, which is the Python check's FIX

# isort: split
import check
import cred_store
from iceria_wiki import Wiki, WikiUnavailable

KIT_ROOT = Path(__file__).resolve().parent.parent
NO_LOGIN = "none saved"
STALE_DAYS = 30  # the wiki moves in weeks; past a month a draft may cite a page that changed


class Result(NamedTuple):
    name: str
    detail: str
    fix: str | None = None


def _ca_count() -> int:
    return ssl.create_default_context().cert_store_stats()["x509_ca"]


def python() -> Result:
    return Result("Python", sys.version.split()[0])


def certificates() -> Result:
    # python.org's Python on a Mac ships with no root certificates until its installer step runs.
    n = _ca_count()
    if n:
        return Result("certificates", f"{n} root certificates")
    return Result(
        "certificates",
        "this Python has no root certificates, so it cannot reach the wiki",
        "on a Mac, open Applications > Python 3.x and double-click Install Certificates.command",
    )


def login() -> Result:
    try:
        found = cred_store.who()
    except cred_store.NoStore as e:
        return Result("bot login", "no credential store on this computer", str(e))
    if not found:
        return Result(
            "bot login",
            f"{NO_LOGIN}, so the tools read the wiki as a guest (to add one: python tools/setup_bot.py)",
        )
    user, where = found
    return Result("bot login", f"{user}, kept in {where}")


def wiki_reachable(wiki) -> Result:
    try:
        wiki.latest_revids(["Main Page"])
    except WikiUnavailable as e:
        return Result("wiki", "could not reach iceria.org", f"{e}; then run this again")
    return Result("wiki", "iceria.org answers")


def canon_copy(kit: Path, today: datetime.date) -> Result:
    path = kit / "VERSION.json"
    if not path.is_file():
        return Result(
            "canon copy", "VERSION.json is missing", "run git pull in the kit folder to get it back"
        )
    built = json.loads(path.read_text(encoding="utf-8"))["built"]
    age = (today - datetime.date.fromisoformat(built)).days
    fix = "python tools/refresh_canon.py --check, and refresh if it says a refresh is due"
    return Result(
        "canon copy", f"copied {built}, {age} days old", fix if age > STALE_DAYS else None
    )


def humanizer() -> Result:
    if check.humanizer_command():
        return Result("humanizer", "installed")
    # Optional: the checker skips the AI-tell audit without it, so a clean install is not broken.
    return Result(
        "humanizer", f"optional, not installed: to add it, {check.pip_install('humanizer-pro')}"
    )


def kit_commit(kit: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(kit), "rev-parse", "--short", "HEAD"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return "unknown (git is not installed)"
    return out.stdout.strip() if out.returncode == 0 else "unknown (not a git clone)"


def support_block(kit: Path, results: list[Result]) -> str:
    """What the maintainer needs to help: the setup and each check's status, never the login's name."""
    bot = next(r for r in results if r.name == "bot login")
    saved = "no" if bot.fix or bot.detail.startswith(NO_LOGIN) else "yes"
    checks = ", ".join(f"{r.name} {'FIX' if r.fix else 'OK'}" for r in results)
    return "\n".join(
        [
            "--- for the maintainer: copy from here ---",
            f"OS: {platform.platform()}",
            f"Python: {sys.version.split()[0]} at {sys.executable}",
            f"Kit commit: {kit_commit(kit)}",
            f"Checks: {checks}",
            f"Bot login saved: {saved}",
            "--- to here ---",
        ]
    )


def main(kit: Path = KIT_ROOT, wiki=None, today: datetime.date | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = [
        python(),
        certificates(),
        login(),
        wiki_reachable(wiki or Wiki()),
        canon_copy(kit, today or datetime.date.today()),
        humanizer(),
    ]
    for r in results:
        if r.fix:
            print(f"FIX {r.name}: {r.detail}\n    do this: {r.fix}")
        else:
            print(f"OK  {r.name}: {r.detail}")
    ok = sum(not r.fix for r in results)
    fixes = len(results) - ok
    if fixes:
        print(f"{ok} of {len(results)} checks are OK; fix the {fixes} above, then run this again.")
    else:
        print(f"{ok} of {len(results)} checks are OK.")
    print("\nStuck? Send the kit's maintainer everything this printed.")
    print(support_block(kit, results))
    return 1 if fixes else 0


def cli(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    return main()


if __name__ == "__main__":
    sys.exit(cli())
