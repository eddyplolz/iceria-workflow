"""Wiring against the live wiki: categories, infoboxes, red links. A fake wiki stands in."""

import check
import iceria_wiki
from checks import wiring

DOC = "<pre>{{Infobox Settlement\n| name =\n| subdivision_name =\n| population_total =\n}}</pre>"


class FakeWiki:
    def __init__(self, pages=(), categories=(), docs=None, down=False):
        self.pages, self.cats, self.docs, self.down = set(pages), set(categories), docs or {}, down

    def _guard(self):
        if self.down:
            raise iceria_wiki.WikiUnavailable("timed out")

    def latest_revids(self, titles):
        self._guard()
        return {t: (1 if t in self.pages else None) for t in titles}

    def categories_exist(self, names):
        self._guard()
        return {n: n in self.cats for n in names}

    def get_page(self, title):
        self._guard()
        text = self.docs.get(title)
        return None if text is None else {"title": title, "revid": 1, "text": text}


def _run(text, wiki=None, **ctx):
    ctx = {"wiki": wiki or FakeWiki(), **ctx}
    return [(f.level, f.message.split(":")[0]) for f in wiring.run(text, ctx)]


def test_without_a_wiki_nothing_is_checked():
    assert wiring.run("[[Category:Nowhere]]\n", {}) == []


def test_a_category_the_wiki_does_not_have_is_an_error():
    wiki = FakeWiki(categories={"Mantua"})
    assert _run("[[Category:Mantua]]\n", wiki) == []
    assert _run("[[Category:Mantoa]]\n", wiki) == [("error", "category does not exist")]


def test_a_category_link_with_a_colon_is_a_link_not_a_filing():
    assert _run("See [[:Category:Anything]].\n") == []


def test_the_category_placeholders_of_the_templates_are_not_looked_up():
    assert _run("[[Category:Nation]]\n[[Category:Other nation]]\n") == []


def test_a_nation_category_for_a_nation_the_draft_never_names_is_a_warning():
    wiki = FakeWiki(pages={"Mantua"}, categories={"Mantua", "Seltana"})
    nations = {"Mantua": "Cavaletta", "Seltana": "Selt"}
    text = "'''Vell''' is a port in [[Mantua]].\n[[Category:Seltana]]\n"
    assert _run(text, wiki, nations=nations) == [
        ("warning", "category names a nation the draft never mentions")
    ]
    assert _run(text.replace("Seltana]]", "Mantua]]"), wiki, nations=nations) == []


def test_a_broader_category_beside_the_specific_one_is_a_warning():
    wiki = FakeWiki(pages={"Mantua"}, categories={"Mantua", "Military of Mantua"})
    nations = {"Mantua": "Cavaletta"}
    both = "Of [[Mantua]].\n[[Category:Military of Mantua]]\n[[Category:Mantua]]\n"
    assert _run(both, wiki, nations=nations) == [
        ("warning", "category also filed in a broader one")
    ]


def test_a_nation_article_may_sit_in_its_own_category_with_a_space_sort_key():
    wiki = FakeWiki(categories={"Mantua"})
    text = "{{Infobox Country\n| common_name = Mantua\n}}\n'''Mantua''' is a nation.\n[[Category:Mantua| ]]\n"
    assert _run(text, wiki, nations={"Mantua": "Cavaletta"}, title="Mantua") == []


def test_an_infobox_the_manual_does_not_list_is_an_error():
    assert _run("{{Infobox City\n| name = Vell\n}}\n") == [("error", "unknown infobox")]
    assert _run("{{Infobox Settlement\n| name = Vell\n}}\n") == []
    assert _run("{{infobox settlement\n| name = Vell\n}}\n") == []


def test_an_infobox_for_another_kind_of_page_is_a_warning():
    text = "{{Infobox Country\n| common_name = Vell\n}}\n'''Vell''' is a port city on the bay.\n"
    assert _run(text, title="Vell") == [("warning", "infobox does not fit the page")]


def test_a_field_the_infobox_template_does_not_have_is_a_warning():
    wiki = FakeWiki(docs={"Template:Infobox Settlement/doc": DOC})
    ok = "{{Infobox Settlement\n| name = Vell\n| population_total = 9\n}}\n"
    bad = "{{Infobox Settlement\n| name = Vell\n| mayor_party = Blue\n}}\n"
    assert _run(ok, wiki) == []
    assert _run(bad, wiki) == [("warning", "infobox field not in the template")]


def test_a_redirected_template_doc_is_followed():
    wiki = FakeWiki(
        docs={
            "Template:Infobox Settlement/doc": "#REDIRECT [[Template:Infobox town/doc]]",
            "Template:Infobox town/doc": DOC,
        }
    )
    assert _run("{{Infobox Settlement\n| mayor_party = Blue\n}}\n", wiki) == [
        ("warning", "infobox field not in the template")
    ]


def test_a_page_link_with_no_page_is_a_warning_and_a_written_page_is_not():
    wiki = FakeWiki(pages={"Mantua"})
    assert _run("A town in [[Mantua]] by [[Port Lune]].\n", wiki) == [
        ("warning", "page not written yet")
    ]


def test_the_checker_asks_the_wiki_unless_told_offline(tmp_path, capsys, monkeypatch):
    draft = tmp_path / "d.wiki"
    draft.write_text(
        "{{SHORTDESC:Port}}\n'''Vell''' is a port.<ref>x</ref>\n<references />\n[[Category:Nowhere]]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check, "Wiki", lambda: FakeWiki())
    assert check.main([str(draft), "--root", str(tmp_path)]) == 1
    assert "category does not exist" in capsys.readouterr().out
    assert check.main([str(draft), "--root", str(tmp_path), "--offline"]) == 0
    assert "skipped" in capsys.readouterr().err


def test_a_wiki_that_cannot_be_reached_is_loud_and_never_a_pass(tmp_path, capsys, monkeypatch):
    draft = tmp_path / "d.wiki"
    draft.write_text(
        "{{SHORTDESC:Port}}\n'''Vell''' is a port.<ref>x</ref>\n<references />\n[[Category:Nowhere]]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check, "Wiki", lambda: FakeWiki(down=True))
    assert check.main([str(draft), "--root", str(tmp_path)]) == 2
    out = capsys.readouterr()
    assert "NOT CHECKED" in out.err and "--offline" in out.err


def test_a_nation_subcategory_outside_the_manual_list_is_a_warning():
    wiki = FakeWiki(pages={"Mantua"}, categories={"Ports of Mantua", "Military of Mantua"})
    nations = {"Mantua": "Cavaletta"}
    body = "Of [[Mantua]].\n"
    assert _run(body + "[[Category:Ports of Mantua]]\n", wiki, nations=nations) == [
        ("warning", "nation subcategory not in the manual's list")
    ]
    assert _run(body + "[[Category:Military of Mantua]]\n", wiki, nations=nations) == []


def test_a_category_for_another_nation_than_the_one_the_page_is_in_is_a_warning():
    wiki = FakeWiki(pages={"Alexandria", "Mantua"}, categories={"Mantua", "Alexandria"})
    nations = {"Alexandria": "Port Alba", "Mantua": "Cavaletta"}
    head = "{{Infobox Settlement\n| subdivision_name = [[Alexandria]]\n}}\n"
    text = head + "'''Vell''' is a port in [[Alexandria]], south of [[Mantua]].\n"
    assert _run(text + "[[Category:Mantua]]\n", wiki, nations=nations) == [
        ("warning", "category names another nation than the page is in")
    ]
    assert _run(text + "[[Category:Alexandria]]\n", wiki, nations=nations) == []


def test_a_nation_category_beside_a_generic_topic_category_is_a_warning():
    wiki = FakeWiki(pages={"Alexandria"}, categories={"Alexandria", "Geography"})
    nations = {"Alexandria": "Port Alba"}
    text = (
        "'''Vell''' is a port in [[Alexandria]].\n[[Category:Alexandria]]\n[[Category:Geography]]\n"
    )
    assert _run(text, wiki, nations=nations) == [
        ("warning", "generic category beside the nation's own")
    ]


def test_the_written_work_infobox_is_one_the_manual_lists():
    assert _run("{{Infobox written work\n| name = Vell Saga\n}}\n") == []


def test_the_country_infobox_fields_are_known_even_when_the_wiki_doc_is_unreadable():
    assert _run("{{Infobox Country\n| common_name = Vell\n| GDP_nominal = 1\n}}\n") == []
    assert _run("{{Infobox Country\n| common_name = Vell\n| prime_minister = X\n}}\n") == [
        ("warning", "infobox field not in the template")
    ]


def test_a_member_s_user_page_is_never_a_red_link():
    assert _run("== Participants ==\n* [[User:Sample]] (creator)\n", FakeWiki()) == []
