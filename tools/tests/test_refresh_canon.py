"""A member's refresh: rebuilds canon/ and style/ from the live wiki, or leaves the kit as it was."""

import datetime
import json
import shutil
from pathlib import Path

import canon_pages
import iceria_wiki
import pytest
import refresh_canon

KIT = Path(__file__).resolve().parents[2]
TODAY = datetime.date(2026, 11, 20)
OLD = {
    "kit_version": "0.1.0",
    "map_lock_version": 7,
    "read_as": "anonymous",
    "built": "2026-10-01",
    "source": "live",
    "nations": ["Mantua", "Xuna"],
    "missing_nations": ["Xuna"],
    "pages": [],
}
PW = "r" * 8  # a stand-in; never the 32-character shape the leak gate looks for


class FakeWiki:
    """The wiki client boundary: serves pages from a dict and keeps every call made."""

    source = "live"

    def __init__(self, pages, refuse=None, down=(), rights=("read", "writeapi")):
        self.pages, self.refuse, self.down, self.rights = pages, refuse, set(down), list(rights)
        self.calls = []

    def login(self, user, password):
        self.calls.append(("login", user))
        if self.refuse:
            raise iceria_wiki.LoginFailed(self.refuse)

    def whoami(self):
        return {"name": "Ana", "rights": self.rights}

    def get_page(self, title):
        self.calls.append(("get_page", title))
        if title in self.down:
            raise iceria_wiki.WikiUnavailable("timed out")
        text = self.pages.get(title)
        return {"title": title, "revid": 5000, "text": text} if text is not None else None

    def expand(self, text):
        return "The calendar starts at launch"

    def latest_revids(self, titles):
        self.calls.append(("latest_revids", tuple(titles)))
        if self.down:
            raise iceria_wiki.WikiUnavailable("timed out")
        return {t: (5000 if t in self.pages else None) for t in titles}


@pytest.fixture
def kit(tmp_path):
    """A built kit as a member has it: the hand-written files plus an older canon/."""
    kit = tmp_path / "kit"
    for folder in ("style", "templates"):
        shutil.copytree(KIT / folder, kit / folder)
    (kit / "canon").mkdir()
    (kit / "canon" / "world-standards.md").write_text("Old standards.\n", encoding="utf-8")
    (kit / "canon" / "geography.json").write_text('{"rivers": []}\n', encoding="utf-8")
    (kit / "templates" / "infobox-cheatsheet.md").write_text("Old fields.\n", encoding="utf-8")
    (kit / "VERSION.json").write_text(json.dumps(OLD), encoding="utf-8")
    return kit


def wiki_pages(kit) -> dict:
    rows = canon_pages.coverage_rows((kit / "style" / "mos-coverage.md").read_text("utf-8"))
    mos = "".join(f"=== {s} Section ===\n" if "." in s else f"== {s}. Section ==\n" for s in rows)
    pages = {title: f"The live page {title}.\n" for title, _ in canon_pages.PAGES}
    pages["Manual of Style"] = mos
    pages["Charter"] = "".join(f"=== {c} Clause ===\nText.\n" for c in canon_pages.CHARTER_CLAUSES)
    pages[canon_pages.PROPOSAL] = "== Nation ==\n"
    pages["Mantua"] = "{{Infobox Country\n| common_name = Mantua\n}}\n'''Mantua''' is a land.\n"
    return pages


def version(kit) -> dict:
    return json.loads((kit / "VERSION.json").read_text(encoding="utf-8"))


def test_an_anonymous_refresh_rebuilds_from_the_wiki_and_says_so(kit, capsys):
    wiki = FakeWiki(wiki_pages(kit))
    assert refresh_canon.refresh(kit, wiki, TODAY, None) == 0
    assert "The live page World Standards." in (kit / "canon/world-standards.md").read_text("utf-8")
    v = version(kit)
    assert (v["built"], v["read_as"], v["kit_version"]) == ("2026-11-20", "anonymous", "0.1.0")
    assert v["missing_nations"] == ["Xuna"]
    assert (kit / "canon/geography.json").read_text("utf-8") == '{"rivers": []}\n'
    assert (kit / "style/mos-coverage.md").exists()  # the hand-written files stay
    assert (kit / "project-pack/knowledge/world-standards.md").exists()
    assert "NOTICE" in capsys.readouterr().err


def test_with_a_bot_password_it_logs_in_first(kit):
    wiki = FakeWiki(wiki_pages(kit))
    assert refresh_canon.refresh(kit, wiki, TODAY, ("Ana@kitbot", PW)) == 0
    assert wiki.calls[0] == ("login", "Ana@kitbot")
    assert version(kit)["read_as"] == "bot"


def test_a_refused_login_fails_loud_and_reads_nothing(kit, capsys):
    wiki = FakeWiki(wiki_pages(kit), refuse="Incorrect username or password")
    assert refresh_canon.refresh(kit, wiki, TODAY, ("Ana@kitbot", PW)) == 1
    assert wiki.calls == [("login", "Ana@kitbot")]
    err = capsys.readouterr().err
    assert "FAILED" in err and "2026-10-01" in err and PW not in err
    assert version(kit) == OLD


def test_a_bot_password_with_more_than_basic_rights_is_refused_before_reading(kit, capsys):
    # Audit risk 6: a password set in the environment never passed setup_bot's rights check.
    wiki = FakeWiki(wiki_pages(kit), rights=("read", "writeapi", "block", "delete"))
    assert refresh_canon.refresh(kit, wiki, TODAY, ("Ana@kitbot", PW)) == 1
    assert wiki.calls == [("login", "Ana@kitbot")]
    err = capsys.readouterr().err
    assert "FAILED" in err and "block, delete" in err and "2026-10-01" in err and PW not in err
    assert version(kit) == OLD
    assert not list(kit.glob(".refresh-*"))


def test_a_wiki_failure_keeps_the_old_kit_and_never_uses_a_copy(kit, capsys):
    wiki = FakeWiki(wiki_pages(kit), down={"Charter"})
    assert refresh_canon.refresh(kit, wiki, TODAY, None) == 1
    err = capsys.readouterr().err
    assert "FAILED" in err and "keeps the copy from 2026-10-01" in err
    assert "FALLBACK" not in err
    assert version(kit) == OLD
    assert (kit / "canon/world-standards.md").read_text("utf-8") == "Old standards.\n"


@pytest.mark.parametrize(
    "target, file",
    [
        ("..\\..\\Evil Land", "evil-land.md"),
        ("C:\\Evil Land", "c-evil-land.md"),
        ("../../Evil Land", "evil-land.md"),
    ],
)
def test_a_redirect_to_a_path_like_title_stays_inside_canon_nations(kit, tmp_path, target, file):
    pages = wiki_pages(kit)
    pages["Mantua"] = f"#REDIRECT [[{target}]]\n"
    pages[target] = "{{Infobox Country\n| common_name = Evil\n}}\n'''Evil''' is a land.\n"
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    written = sorted(p.name for p in (kit / "canon" / "nations").iterdir())
    assert written == [file]
    assert not list(tmp_path.glob("*.md")) and not (tmp_path / "evil-land.md").exists()


def test_a_redirected_style_or_canon_page_is_copied_from_its_target(kit):
    # Audit bug 4: only nations followed a redirect, so a moved page was copied as one #REDIRECT line.
    pages = wiki_pages(kit)
    pages["World Standards"] = "#REDIRECT [[World standards]]\n"
    pages["World standards"] = "The live page World standards.\n"
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    text = (kit / "canon" / "world-standards.md").read_text(encoding="utf-8")
    assert "#REDIRECT" not in text
    assert "The live page World standards." in text
    assert 'wiki page "World standards"' in text


def test_a_swap_stopped_part_way_puts_the_old_kit_back(kit, monkeypatch, capsys):
    # Path.rename, not os.rename: on Python 3.10 pathlib calls its own saved copy of os.rename.
    real = Path.rename

    def held_open(src, dst):  # a file in the new templates/ held open by a virus scanner
        new = Path(src).parent  # the new tree, not the old copy set aside beside it
        if (
            new.name == "kit"
            and new.parent.name.startswith(".refresh-")
            and Path(src).name == "templates"
        ):
            raise PermissionError(13, "in use", str(src))
        return real(src, dst)

    monkeypatch.setattr(Path, "rename", held_open)
    assert refresh_canon.refresh(kit, FakeWiki(wiki_pages(kit)), TODAY, None) == 1
    err = capsys.readouterr().err
    assert "FAILED" in err and "put back canon, style, templates" in err
    assert version(kit) == OLD
    assert (kit / "canon/world-standards.md").read_text("utf-8") == "Old standards.\n"
    assert (kit / "templates/infobox-cheatsheet.md").read_text("utf-8") == "Old fields.\n"
    assert (kit / "style/mos-coverage.md").exists()
    assert not (kit / "project-pack").exists()
    assert not list(kit.glob(".refresh-*"))


def test_a_changed_manual_warns_and_still_refreshes(kit, capsys):
    # Audit R12: only a steward can update style/mos-coverage.md, so a member's refresh must not
    # stall on a manual that gained a section.
    pages = wiki_pages(kit)
    pages["Manual of Style"] += "== 21. A new section ==\n"
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    err = capsys.readouterr().err
    assert "WARNING: Manual of Style changed: no row for 21" in err
    assert version(kit)["built"] == "2026-11-20"
    assert "21. A new section" in (kit / "style/manual-of-style.md").read_text("utf-8")


def test_a_password_in_a_kit_file_stops_it_before_any_wiki_call(kit, capsys):
    (kit / "notes.md").write_text("q7" * 16 + "\n", encoding="utf-8")
    wiki = FakeWiki(wiki_pages(kit))
    assert refresh_canon.refresh(kit, wiki, TODAY, None) == 1
    assert wiki.calls == []
    assert "notes.md:1: bot password" in capsys.readouterr().err


def test_an_unexpected_error_still_removes_the_work_folder(kit, monkeypatch):
    # Audit P1-3: only the expected failures cleaned up, so any other error left .refresh-* behind.
    def broken(tree):
        raise RuntimeError("disk full")

    monkeypatch.setattr(refresh_canon, "knowledge", broken)
    with pytest.raises(RuntimeError):
        refresh_canon.refresh(kit, FakeWiki(wiki_pages(kit)), TODAY, None)
    assert not list(kit.glob(".refresh-*"))
    assert version(kit) == OLD


def test_when_the_old_copy_cannot_go_back_its_folder_is_kept_and_named(kit, monkeypatch, capsys):
    real = Path.rename  # see test_a_swap_stopped_part_way_puts_the_old_kit_back

    def stuck(
        src, dst
    ):  # the new templates/ will not move in, and the old canon/ will not move back
        src = Path(src)
        if src.name == "templates" and src.parent.name == "kit":
            raise PermissionError(13, "in use", str(src))
        if src.name == "canon" and src.parent.name == "old":
            raise PermissionError(13, "in use", str(src))
        return real(src, dst)

    monkeypatch.setattr(Path, "rename", stuck)
    assert refresh_canon.refresh(kit, FakeWiki(wiki_pages(kit)), TODAY, None) == 1
    err = capsys.readouterr().err
    (work,) = kit.glob(".refresh-*")
    assert (work / "old" / "canon" / "world-standards.md").read_text("utf-8") == "Old standards.\n"
    assert "canon" in err and str(work / "old") in err


def checked_kit(kit, pages):
    """The kit's VERSION.json as a refresh on 2026-10-01 left it, every page at revision 5000."""
    v = {**OLD, "pages": [{"title": t, "revid": 5000, "source": "live"} for t in pages]}
    (kit / "VERSION.json").write_text(json.dumps(v), encoding="utf-8")
    return kit


def test_check_says_current_when_every_page_is_at_its_copied_revision(kit, capsys):
    kit = checked_kit(kit, ["Charter", "World Standards"])
    wiki = FakeWiki({"Charter": "x", "World Standards": "x"})
    assert refresh_canon.check(kit, wiki, TODAY, None) == 0
    out = capsys.readouterr().out
    assert "current" in out and "50 days old" in out
    assert [c[0] for c in wiki.calls] == ["latest_revids"]  # one request, nothing read in full


def test_check_names_each_changed_page_and_a_nation_now_written(kit, capsys):
    kit = checked_kit(kit, ["Charter", "World Standards"])
    wiki = FakeWiki({"Charter": "x", "World Standards": "x", "Xuna": "x"})
    wiki.latest_revids = lambda titles: {"Charter": 5000, "World Standards": 5100, "Xuna": 9}
    before = (kit / "VERSION.json").read_text("utf-8")
    assert refresh_canon.check(kit, wiki, TODAY, None) == 1
    out = capsys.readouterr().out
    assert "World Standards" in out and "Xuna" in out and "Charter" not in out
    # The reason is the wiki, not the copy's age: a copy made today is due when a page changed.
    first = out.splitlines()[0]
    assert first == (
        "a refresh is due: the wiki changed since your copy from 2026-10-01 "
        "(World Standards edited; Xuna now has a page): run python tools/refresh_canon.py"
    )
    assert "days old" not in first
    assert (kit / "VERSION.json").read_text("utf-8") == before  # a check writes nothing


def test_check_with_many_changed_pages_counts_them_and_lists_each(kit, capsys):
    titles = [f"Page {i}" for i in range(5)]
    kit = checked_kit(kit, titles)
    wiki = FakeWiki(dict.fromkeys(titles, "x"))
    wiki.latest_revids = lambda t: dict.fromkeys(titles, 6000)
    assert refresh_canon.check(kit, wiki, TODAY, None) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith(
        "a refresh is due: the wiki changed since your copy from 2026-10-01 (5 pages edited)"
    )
    assert all(f"  changed since the copy: Page {i}" in out for i in range(5))


def test_check_counts_a_deleted_page_as_changed(kit, capsys):
    kit = checked_kit(kit, ["Charter"])
    assert refresh_canon.check(kit, FakeWiki({}), TODAY, None) == 1
    assert "Charter" in capsys.readouterr().out


def test_check_that_cannot_reach_the_wiki_exits_2(kit, capsys):
    kit = checked_kit(kit, ["Charter"])
    assert refresh_canon.check(kit, FakeWiki({"Charter": "x"}, down={"Charter"}), TODAY, None) == 2
    assert "could not check" in capsys.readouterr().err


def test_check_with_a_bot_password_vets_it_first(kit, capsys):
    kit = checked_kit(kit, ["Charter"])
    wiki = FakeWiki({"Charter": "x"}, rights=("read", "edit"))
    assert refresh_canon.check(kit, wiki, TODAY, ("Ana@kitbot", PW)) == 2
    assert "more than Basic rights" in capsys.readouterr().err
    assert ("latest_revids", ("Charter", "Xuna")) not in wiki.calls


def test_a_refresh_copies_the_calendar_start_from_the_module(kit):
    pages = wiki_pages(kit)
    pages["Module:Iceria date"] = 'local p = {}\np.START = "2026-11"\nreturn p\n'
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    assert version(kit)["calendar_start"] == "2026-11"


def test_a_refresh_copies_a_start_day_from_the_module(kit):
    pages = wiki_pages(kit)
    pages["Module:Iceria date"] = 'local p = {}\np.START = "2027-01-15"\nreturn p\n'
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    assert version(kit)["calendar_start"] == "2027-01-15"


@pytest.mark.parametrize("module", [None, 'p.START = ""\n'])
def test_before_launch_the_calendar_start_is_none(kit, module):
    pages = wiki_pages(kit)
    if module:
        pages["Module:Iceria date"] = module
    assert refresh_canon.refresh(kit, FakeWiki(pages), TODAY, None) == 0
    assert version(kit)["calendar_start"] is None
