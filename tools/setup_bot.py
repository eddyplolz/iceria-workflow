"""Set up your own bot password so refresh_canon.py can read the wiki as you.

    python tools/setup_bot.py            make the bot password, test it, save it
    python tools/setup_bot.py --check    test the saved one

The password is typed at a hidden prompt, tested against the wiki, and kept in your computer's
credential store, never in a file of the kit. A bot password with more than Basic rights is
refused: the kit only reads, so its bot password carries Basic rights and nothing more.
"""

import argparse
import getpass
import sys

import kit_python  # noqa: F401  stops on Python < 3.10

# isort: split
import cred_store
from iceria_wiki import LoginFailed, Wiki, WikiUnavailable

STEPS = """\
1. Log in to the wiki and open https://www.iceria.org/wiki/Special:BotPasswords
2. Under "Create a new bot password", type a bot name, for example kit, and click Create.
3. Tick "Basic rights" only. Leave every other box empty, then click Create.
4. The wiki shows a login name (YourName@kit) and a password, once. Keep the page open.
"""
# Every right the Basic grant gives, from iceria.org's Special:ListGrants (2026-10-31), plus
# writeapi, which MediaWiki may report for any logged-in session. A right outside this set means a
# box beyond Basic was ticked, whether or not that right posts.
BASIC_RIGHTS = frozenset(
    {
        "autocreateaccount", "ipblock-exempt", "torunblocked", "globalblock-exempt", "user",
        "editsemiprotected", "autopatrol", "autoconfirmed", "nominornewtalk", "skipcaptcha", "read",
        "unwatchedpages", "abusefilter-view", "abusefilter-log-detail", "patrolmarks",
        "abusefilter-log", "writeapi",
    }
)  # fmt: skip


def vet_login(wiki, user: str, password: str) -> str | None:
    """None when the bot password logs in with Basic rights only, else what is wrong."""
    try:
        wiki.login(user, password)
        rights = set(wiki.whoami()["rights"])
    except LoginFailed as e:
        return f"the wiki refused the login: {e}"
    except WikiUnavailable as e:
        return f"the wiki could not be reached: {e}"
    if extras := sorted(rights - BASIC_RIGHTS):
        return (
            f"this bot password has more than Basic rights ({', '.join(extras)}). Delete it at "
            "Special:BotPasswords and make a new one with Basic rights only."
        )
    return None


def setup(wiki, store, ask=input, secret=getpass.getpass) -> int:
    print(STEPS)
    user = ask("Login name the wiki showed (YourName@kit): ").strip()
    if "@" not in user:
        print(
            "That is not a bot login name: it has the form YourName@botname, with the @.",
            file=sys.stderr,
        )
        return 1
    password = secret("Password the wiki showed (hidden as you type): ").strip()
    problem = vet_login(wiki, user, password)
    if problem:
        print(f"Not saved: {problem}", file=sys.stderr)
        return 1
    try:
        store.write(user, password)
    except cred_store.NoStore as e:
        print(f"Not saved: {e}", file=sys.stderr)
        return 1
    print(f"Saved {user} to {store.name}. Next: python tools/refresh_canon.py")
    return 0


def check(wiki) -> int:
    found = cred_store.get()
    if not found:
        print("No bot password set up. Run python tools/setup_bot.py first.", file=sys.stderr)
        return 1
    (user, password), where = found
    problem = vet_login(wiki, user, password)
    if problem:
        print(f"{user} from {where}: {problem}", file=sys.stderr)
        return 1
    print(f"{user} from {where}: logs in with Basic rights only.")
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="test the saved bot password")
    args = ap.parse_args(argv)
    if args.check:
        return check(Wiki())
    try:
        store = cred_store.store()
    except cred_store.NoStore as e:
        print(f"Cannot save a password here: {e}", file=sys.stderr)
        return 1
    return setup(Wiki(), store)


if __name__ == "__main__":
    sys.exit(main())
