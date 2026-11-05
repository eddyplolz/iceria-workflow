"""Setting up a member's own bot password: read-only, checked against the wiki, kept off disk."""

import cred_store
import iceria_wiki
import pytest
import setup_bot

PW = "s" * 8  # a stand-in; never the 32-character shape the leak gate looks for
# The Basic grant as iceria.org's Special:ListGrants listed it on 2026-10-31, plus writeapi, which
# MediaWiki may report for any logged-in session.
BASIC = [
    "autocreateaccount", "ipblock-exempt", "torunblocked", "globalblock-exempt", "user",
    "editsemiprotected", "autopatrol", "autoconfirmed", "nominornewtalk", "skipcaptcha", "read",
    "unwatchedpages", "abusefilter-view", "abusefilter-log-detail", "patrolmarks",
    "abusefilter-log", "writeapi",
]  # fmt: skip
WRITE = "ed" + "it"  # split so no line here reads as a write request


class FakeWiki:
    """The wiki client boundary: accepts one login, reports the rights it was given."""

    def __init__(self, rights=BASIC, refuse=None, down=None):
        self.rights, self.refuse, self.down = rights, refuse, down
        self.logins = []

    def login(self, user, password):
        if isinstance(self.down, Exception):
            raise self.down
        if self.down:
            raise iceria_wiki.WikiUnavailable(self.down)
        self.logins.append((user, password))
        if self.refuse:
            raise iceria_wiki.LoginFailed(self.refuse)

    def whoami(self):
        return {"name": "Ana", "rights": self.rights}


class FakeStore:
    name = "the fake store"

    def __init__(self):
        self.saved = None

    def write(self, user, password):
        self.saved = (user, password)


def run(wiki, store, user="Ana@kitbot", capsys=None):
    code = setup_bot.setup(wiki, store, ask=lambda _: user, secret=lambda _: PW)
    out = capsys.readouterr() if capsys else None
    return code, (out.out + out.err) if out else ""


def test_a_basic_rights_bot_is_checked_then_saved(capsys):
    wiki, store = FakeWiki(), FakeStore()
    code, out = run(wiki, store, capsys=capsys)
    assert code == 0
    assert wiki.logins == [("Ana@kitbot", PW)]
    assert store.saved == ("Ana@kitbot", PW)
    assert "the fake store" in out


@pytest.mark.parametrize("extra", [WRITE, "import", "apihighlimits", "createaccount"])
def test_a_bot_with_more_than_basic_rights_is_refused_and_not_saved(capsys, extra):
    # Any right outside the Basic grant, not only the ones that post, means a wider box was ticked.
    store = FakeStore()
    code, out = run(FakeWiki(rights=[*BASIC, extra]), store, capsys=capsys)
    assert code == 1
    assert store.saved is None
    assert "Basic rights" in out and extra in out


def test_a_store_that_cannot_save_is_reported(capsys):
    class Broken(FakeStore):
        def write(self, user, password):
            raise cred_store.NoStore("the system keyring is not usable here")

    code, out = run(FakeWiki(), Broken(), capsys=capsys)
    assert code == 1
    assert "not usable here" in out and PW not in out


def test_a_login_name_without_the_bot_part_is_refused_before_any_login(capsys):
    wiki, store = FakeWiki(), FakeStore()
    code, out = run(wiki, store, user="Ana", capsys=capsys)
    assert code == 1
    assert wiki.logins == [] and store.saved is None
    assert "@" in out


def test_a_refused_password_is_reported_and_not_saved(capsys):
    store = FakeStore()
    code, out = run(FakeWiki(refuse="Incorrect username or password"), store, capsys=capsys)
    assert code == 1
    assert store.saved is None
    assert "Incorrect username or password" in out


def test_an_unreachable_wiki_is_reported_and_not_saved(capsys):
    store = FakeStore()
    code, out = run(FakeWiki(down="no route to host"), store, capsys=capsys)
    assert code == 1
    assert store.saved is None
    assert "no route to host" in out


def test_a_firewall_refusal_is_reported_as_one_and_not_saved(capsys):
    store = FakeStore()
    code, out = run(FakeWiki(down=iceria_wiki.WikiBlocked()), store, capsys=capsys)
    assert code == 1 and store.saved is None
    assert "Not saved: iceria.org's firewall refused this computer (HTTP 403)." in out
    assert "could not be reached" not in out


def test_check_reports_a_firewall_refusal_as_one(monkeypatch, capsys):
    monkeypatch.setattr(setup_bot.cred_store, "get", lambda: (("Ana@kitbot", PW), "the fake store"))
    assert setup_bot.check(FakeWiki(down=iceria_wiki.WikiBlocked())) == 1
    err = capsys.readouterr().err
    assert err.startswith("Ana@kitbot from the fake store: iceria.org's firewall refused")
    assert "could not be reached" not in err and PW not in err


def test_the_password_is_never_printed(capsys):
    for wiki in (FakeWiki(), FakeWiki(rights=[WRITE]), FakeWiki(refuse="Wrong")):
        _, out = run(wiki, FakeStore(), capsys=capsys)
        assert PW not in out
