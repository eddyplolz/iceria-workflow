from checks import markup

BAD = """{{SHORTDESC:The former coastal state in the far west of Eostria on the Serenian Ocean.}}
{{Infobox country
| capital = Vell
| currency = N/A
}}
'''Vell''' is a **coastal** state, e.g. a port.<ref name="a" />
## Economy
- Fishing
It uses `code` and [a link](https://x.y) etc.
"""


def _summary(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_each_markup_fault_is_named():
    assert _summary(markup.run(BAD, {})) == [
        (1, "error", "short description too long"),
        (1, "error", "short description starts with an article"),
        (1, "error", "short description ends with a full stop"),
        (1, "warning", "short description says current or former"),
        (4, "error", "empty infobox value"),
        (6, "error", "Markdown bold"),
        (6, "error", "Latin abbreviation"),
        (7, "error", "Markdown heading"),
        (8, "warning", "Markdown bullet"),
        (9, "error", "Markdown code"),
        (9, "error", "Markdown link"),
        (9, "error", "Latin abbreviation"),
        (9, "error", "no category"),
        (9, "error", "no reference list"),
    ]


def test_missing_short_description_and_refs_are_warnings():
    found = markup.run("'''Vell''' is a state.\n[[Category:Nations]]\n", {})
    assert _summary(found) == [
        (1, "warning", "no short description"),
        (1, "warning", "no references"),
    ]


def test_a_clean_article_passes():
    clean = """{{SHORTDESC:Coastal state in western Eostria}}
{{Infobox country
| capital = Vell
}}
'''Vell''' is a coastal state, for example a port.<ref name="a" />

== References ==
<references>
<ref name="a">[[History of Iceria]]</ref>
</references>

[[Category:Nations]]
"""
    assert markup.run(clean, {}) == []


def test_a_nested_numbered_list_is_no_markdown_heading():
    # Audit: wikitext writes a nested numbered list as "##", which the heading rule flagged.
    text = "# The council meets.\n## It votes.\n## It adjourns.\n"
    assert "Markdown heading" not in [f.message.split(":")[0] for f in markup.run(text, {})]


def test_a_self_closing_nowiki_hides_nothing_after_it():
    # Review: <nowiki/> masked the rest of the page, so refs and categories went unseen.
    text = (
        "{{SHORTDESC:State in Iceria}}\n'''Vell'''<nowiki/>'s capital is Ost.<ref name=\"a\" />\n\n"
        '== References ==\n<references>\n<ref name="a">[[Vell]]</ref>\n</references>\n\n'
        "[[Category:Vell]]\n"
    )
    assert markup.run(text, {}) == []


def _msgs(text, ctx=None):
    return [(f.level, f.message.split(":")[0]) for f in markup.run(text, ctx or {})]


LEAD = "{{SHORTDESC:Port city in Alexandria}}\n"


def test_a_markdown_h1_is_an_error_but_a_numbered_list_is_not():
    assert ("error", "Markdown heading") in _msgs(
        LEAD + "'''Vell''' is a port.\n# Economy\nGrain.\n"
    )
    listed = LEAD + "# The council meets.\n# It votes on the budget.\n"
    assert ("error", "Markdown heading") not in _msgs(listed)


def test_the_short_description_must_be_first_and_start_with_a_capital():
    late = "{{Infobox Settlement\n| name = Vell\n}}\n{{SHORTDESC:Port city in Alexandria}}\n"
    assert ("error", "short description is not the first line") in _msgs(late)
    assert ("error", "short description starts in lower case") in _msgs(
        "{{SHORTDESC:port city in Alexandria}}\n"
    )
    after_comment = "<!-- guidance -->\n{{SHORTDESC:Port city in Alexandria}}\n"
    assert ("error", "short description is not the first line") not in _msgs(after_comment)


def test_a_comment_left_in_the_draft_is_a_warning_naming_the_fix():
    found = markup.run("{{SHORTDESC:Port city}}\n<!-- guidance -->\ntext\n", {})
    hit = [f for f in found if f.message.startswith("comment left in the draft")]
    assert [(f.line, f.level) for f in hit] == [(2, "warning")]
    assert "delete" in hit[0].message


def test_an_empty_section_is_a_warning_and_a_subsection_makes_it_whole():
    assert ("warning", "empty section") in _msgs(
        "== History ==\n\n== Economy ==\nGrain.\n== See also ==\n\n== References ==\n"
    )
    nested = "== History ==\n=== Early ===\nText.\n"
    assert ("warning", "empty section") not in _msgs(nested)
    assert _msgs("== See also ==\n\n== Notes ==\nx\n").count(("warning", "empty section")) == 1


def test_a_comment_only_section_is_not_called_empty():
    assert ("warning", "empty section") not in _msgs("== History ==\n<!-- say what -->\n")


def test_categories_belong_once_each_at_the_end():
    page = "text\n[[Category:Alexandria]]\n\n== Notes ==\nmore\n"
    assert ("error", "category not at the end of the page") in _msgs(page)
    twice = "text\n[[Category:Alexandria]]\n[[category:alexandria]]\n"
    assert ("error", "category listed twice") in _msgs(twice)
    ok = "text\n\n[[Category:Alexandria]]\n[[Category:Geography]]\n"
    assert ("error", "category not at the end of the page") not in _msgs(ok)


def test_a_meta_template_in_the_draft_is_an_error():
    assert ("error", "meta template") in _msgs(LEAD + "{{Written for Iceria|user=Eddy}}\n")
