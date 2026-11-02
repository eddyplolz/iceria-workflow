"""The redlink list: which links in a draft point at pages nobody has written yet."""

import iceria_wiki
import redlinks

DRAFT = (
    "'''Vell''' lies on the [[river Aster|Aster]] near [[Mantua]].<ref>[[Nowhere Town]]</ref>\n"
    "[[File:Vell.png|thumb|Harbor]] [[Category:Cities]] [[:Category:Ports]]\n"
    "<!-- [[Hidden Page]] -->\n"
    "It trades with [[mantua#Trade|Mantua]] and [[Port Lune]].\n"
)


class FakeWiki:
    def __init__(self, written, down=False):
        self.written, self.down, self.asked = set(written), down, []

    def latest_revids(self, titles):
        self.asked.append(list(titles))
        if self.down:
            raise iceria_wiki.WikiUnavailable("timed out")
        return {t: (1 if t in self.written else None) for t in titles}


def test_each_link_target_is_asked_once_and_files_categories_and_comments_are_left_out():
    wiki = FakeWiki({"Mantua"})
    redlinks.find(redlinks.targets(DRAFT), wiki)
    assert wiki.asked == [["River Aster", "Mantua", "Nowhere Town", "Port Lune"]]


def test_the_red_ones_come_back_with_the_line_they_are_first_on():
    found = redlinks.find(redlinks.targets(DRAFT), FakeWiki({"Mantua", "River Aster"}))
    assert found == [(1, "Nowhere Town"), (4, "Port Lune")]


def test_the_cli_says_red_means_not_written_yet(tmp_path, capsys, monkeypatch):
    draft = tmp_path / "vell.wiki"
    draft.write_text(DRAFT, encoding="utf-8")
    monkeypatch.setattr(redlinks, "Wiki", lambda: FakeWiki({"Mantua", "River Aster"}))
    assert redlinks.main([str(draft)]) == 0
    out = capsys.readouterr().out
    assert "vell.wiki:4: [[Port Lune]]" in out
    assert "not written yet" in out and "Charter 1.4" in out
    assert "2 of 4 linked pages are not written yet" in out


def test_the_cli_exits_2_when_the_wiki_cannot_be_reached(tmp_path, capsys, monkeypatch):
    draft = tmp_path / "vell.wiki"
    draft.write_text(DRAFT, encoding="utf-8")
    monkeypatch.setattr(redlinks, "Wiki", lambda: FakeWiki((), down=True))
    assert redlinks.main([str(draft)]) == 2
    assert "could not check" in capsys.readouterr().err


def test_a_draft_saved_as_utf16_by_powershell_is_read(tmp_path, capsys, monkeypatch):
    draft = tmp_path / "vell.wiki"
    draft.write_bytes(DRAFT.replace("\n", "\r\n").encode("utf-16"))
    monkeypatch.setattr(redlinks, "Wiki", lambda: FakeWiki({"Mantua", "River Aster"}))
    assert redlinks.main([str(draft)]) == 0
    assert "2 of 4 linked pages are not written yet" in capsys.readouterr().out


def test_a_draft_that_is_not_there_is_named_and_the_wiki_is_not_asked(
    tmp_path, capsys, monkeypatch
):
    wiki = FakeWiki(())
    monkeypatch.setattr(redlinks, "Wiki", lambda: wiki)
    assert redlinks.main([str(tmp_path / "vell.wiki")]) == 2
    assert "no file at" in capsys.readouterr().err and wiki.asked == []
