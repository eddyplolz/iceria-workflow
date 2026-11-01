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
