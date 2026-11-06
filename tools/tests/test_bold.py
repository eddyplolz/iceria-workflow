from checks import bold, lead

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


def test_a_noinclude_line_above_the_lead_is_not_the_lead():
    # An old infobox page closes its table, then an empty <noinclude> block, then the first sentence.
    text = "{|\n| Vell\n|}\n<noinclude>\n</noinclude>\n\nThe '''Vell''' is a state.\n"
    assert bold.run(text, {"title": "Vell"}) == []
    assert lead(text) == (7, "The '''Vell''' is a state.")


def test_the_bold_name_in_the_lead_is_the_title():
    text = "'''Port Alba City''' is a port city.\n"
    found = bold.run(text, {"title": "Port Alba"})
    assert [(f.level, f.message.split(":")[0]) for f in found] == [
        ("warning", "bold name is not the title")
    ]
    assert found[0].message == (
        "bold name is not the title: the first sentence bolds 'Port Alba City'; bold the title "
        "'Port Alba' there, or retitle the page (MoS 3.1)"
    )
    assert bold.run("'''Port Alba''' is a port city.\n", {"title": "Port Alba"}) == []
    assert (
        bold.run("'''Alba''' is a port, also called '''Port Alba'''.\n", {"title": "Port Alba"})
        == []
    )


def test_an_unclosed_bold_runs_to_the_end_of_its_line_like_the_wiki_renders_it():
    text = "'''Vell''' is a city.\n\n== History ==\nIt grew '''fast and then stopped.\n"
    found = bold.run(text, {"title": "Vell"})
    assert [(f.line, f.level) for f in found] == [(4, "error")]


# A styled banner or navigation bar above the article is layout, not its lead (Tleyew-Pas pages
# open with two or three <div> lines before the first sentence).
BANNER = """<div style="padding:25px;"><div>THE REPUBLIC OF VELL · DISCOVER</div></div>
<div style="text-align:center;">'''Explore the republic''' · [[Vell|Welcome]] · [[Vell: People|People]]</div>

'''Vell''' is a coastal state.

== History ==
It was founded in 1802.
"""


def test_a_banner_above_the_lead_is_not_the_lead():
    assert bold.run(BANNER, {"title": "Vell"}) == []


def test_the_lead_under_a_banner_is_still_checked():
    unbolded = BANNER.replace("'''Vell''' is", "Vell is")
    found = bold.run(unbolded, {"title": "Vell"})
    assert [(f.line, f.message) for f in found] == [
        (4, "the lead does not bold the title (MoS 3.1)")
    ]


NO_LEAD = """<div style="padding:25px;">THE REPUBLIC OF VELL</div>

== History ==
Vell was founded in 1802.
"""


def test_a_page_that_opens_on_a_heading_has_no_lead():
    found = bold.run(NO_LEAD, {"title": "Vell"})
    assert [(f.line, f.level, f.message) for f in found] == [
        (
            3,
            "warning",
            "the page has no lead: write an opening paragraph above the first heading "
            "that bolds the title (MoS 3.1)",
        )
    ]


def test_a_page_with_no_prose_has_no_lead_warning():
    assert (
        bold.run("{{Infobox nation\n| name = Vell\n}}\n[[Category:Vell]]\n", {"title": "Vell"})
        == []
    )


def test_a_lead_written_inside_a_banner_is_the_lead():
    # Review: a whole first sentence on one <div> line was skipped as layout.
    wrapped = (
        "<div style=\"text-align:center\">'''Vell''' is a coastal state.</div>\n\n"
        "== History ==\nVell was founded in 1802.\n"
    )
    assert bold.run(wrapped, {"title": "Vell"}) == []
    unbolded = (
        '<div style="text-align:center">Vell is a coastal state.</div>\n\n== History ==\nText.\n'
    )
    assert [f.message for f in bold.run(unbolded, {"title": "Vell"})] == [
        "the lead does not bold the title (MoS 3.1)"
    ]


def test_the_lead_is_never_a_line_under_a_heading():
    from checks import lead

    assert lead(NO_LEAD) is None


def test_a_motto_banner_that_ends_a_sentence_is_not_the_lead_when_a_lead_follows():
    # Corpus: Tleyew-Pas pages open with a tagline div ("Our shores are open to friendship.")
    # and a navigation bar holding bold, then the real lead.
    text = (
        '<div style="font-style:italic;">Our shores are open to friendship.</div>\n'
        "<div style=\"text-align:center;\">'''Explore the republic''' · [[Vell|Welcome]]</div>\n"
        '<div style="padding:9px;">To welcome another nation is to listen.</div>\n'
        "\n'''Vell''' is a coastal state.\n\n== History ==\nIt was founded in 1802.\n"
    )
    assert bold.run(text, {"title": "Vell"}) == []
    unbolded = text.replace("'''Vell''' is", "Vell is")
    assert [(f.line, f.message) for f in bold.run(unbolded, {"title": "Vell"})] == [
        (5, "the lead does not bold the title (MoS 3.1)")
    ]


def test_bold_in_a_layout_block_after_the_first_paragraph_is_still_an_error():
    # Corpus: the Tleyew-Pas page bolds a line inside a callout div lower in its lead.
    text = (
        '<div style="font-style:italic;">Our shores are open to friendship.</div>\n'
        "\n'''Vell''' is a coastal state.\n\n"
        "<div style=\"padding:9px;\">'''A connected republic.''' Its ports trade widely.</div>\n"
        "\n== History ==\nIt was founded in 1802.\n"
    )
    assert [(f.line, f.message) for f in bold.run(text, {"title": "Vell"})] == [
        (5, "'''A connected republic.''': bold in the lead after its first paragraph (MoS 6.3)")
    ]


def test_a_lead_inside_a_block_may_end_in_a_ref_or_italics():
    # Review finding: the sentence end sits before a ref, closing italics or a quote mark.
    for ending in (".<ref>Vell Gazette</ref>", ".''", '."'):
        text = (
            f"<div>'''Vell''' is a coastal state{ending}</div>\n\n== History ==\nIt was founded.\n"
        )
        assert bold.run(text, {"title": "Vell"}) == [], ending
