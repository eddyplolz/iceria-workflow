from checks import bold

DRAFT = """{{Infobox country
| name = '''Vell'''
}}
'''Vell''' is a coastal state in [[Eostria]].

It was founded in 1802.

== History ==
'''Note:''' the old capital.
The war left '''deep''' scars.
"""


def test_bold_in_the_body_and_a_lead_in_are_errors():
    found = bold.run(DRAFT, {})
    assert [(f.line, f.level) for f in found] == [(9, "error"), (10, "error")]
    assert "bolded lead-in" in found[0].message
    assert "bold in the body" in found[1].message


def test_a_clean_lead_has_no_findings():
    clean = "'''Vell''' is a coastal state.\n\n== History ==\nIt was founded in 1802.\n"
    assert bold.run(clean, {}) == []


def test_bold_in_a_heading_is_an_error():
    found = bold.run("'''Vell''' is a state.\n\n== '''History''' ==\nText.\n", {})
    assert [(f.line, "heading" in f.message) for f in found] == [(3, True)]


def test_no_bold_in_the_lead_is_a_warning():
    found = bold.run("Vell is a state.\n\n== History ==\nText.\n", {})
    assert [(f.line, f.level) for f in found] == [(1, "warning")]


def test_a_magic_word_before_the_title_does_not_hide_its_bold():
    text = (
        '<div style="text-align:center">\n'
        "[[File:Vell banner.png|center]]\n"
        "__NOTOC__'''Vell''' is a state in '''Meridia'''.\n\n"
        "== History ==\nFounded in 1802.\n"
    )
    assert bold.run(text, {}) == []


def test_the_bold_name_in_the_lead_is_the_title():
    text = "'''Port Alba City''' is a port city.\n"
    found = bold.run(text, {"title": "Port Alba"})
    assert [(f.level, f.message.split(":")[0]) for f in found] == [
        ("warning", "bold name is not the title")
    ]
    assert bold.run("'''Port Alba''' is a port city.\n", {"title": "Port Alba"}) == []
    assert (
        bold.run("'''Alba''' is a port, also called '''Port Alba'''.\n", {"title": "Port Alba"})
        == []
    )


def test_an_unclosed_bold_runs_to_the_end_of_its_line_like_the_wiki_renders_it():
    text = "'''Vell''' is a city.\n\n== History ==\nIt grew '''fast and then stopped.\n"
    found = bold.run(text, {"title": "Vell"})
    assert [(f.line, f.level) for f in found] == [(4, "error")]
