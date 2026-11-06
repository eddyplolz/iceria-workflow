from checks import headings

BAD = """'''Vell''' is a state.

= Vell =
== HISTORY ==
==== Early years ====
== Rise of the [[Vell League]] ==
== Geography. ==
== Economy ==
== Economy ==
== References ==
== See also ==
== External links ==
"""


def _rules(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_each_heading_fault_is_named_on_its_line():
    found = headings.run(BAD, {"title": "Vell"})
    assert _rules(found) == [
        (3, "error", "level 1 heading"),
        (3, "warning", "heading repeats the title"),
        (4, "error", "all-caps heading"),
        (5, "error", "heading skips a level"),
        (6, "error", "markup in a heading"),
        (7, "error", "heading ends with a full stop"),
        (9, "error", "duplicate heading"),
        (11, "error", "closing sections out of order"),
        (12, "error", "section not used on Iceria"),
    ]


def test_title_case_is_a_warning_and_standard_headings_must_be_sentence_case():
    found = headings.run("Text.\n\n== Early Modern History ==\n== See Also ==\n", {})
    assert _rules(found) == [
        (3, "warning", "heading may be in title case"),
        (4, "error", "standard heading in the wrong case"),
    ]


def test_clean_headings_pass():
    clean = (
        "Text.\n\n== History ==\n=== 1802–1840 ===\n=== Rise of the Vell League ===\n"
        "== See also ==\n== Notes ==\n== References ==\n"
    )
    assert headings.run(clean, {"title": "Vell"}) == []


def test_a_heading_that_links_the_title_still_repeats_it():
    # Review: "History of [[Port-Réal]]" missed the title check because of the link brackets.
    found = headings.run(
        "Text.\n\n== History of [[Port-Réal|Port-Réal]] ==\n", {"title": "Port-Réal"}
    )
    assert _rules(found) == [
        (3, "error", "markup in a heading"),
        (3, "warning", "heading repeats the title"),
    ]


def test_a_title_case_heading_of_unlisted_words_is_a_warning():
    kinds = [
        (f.level, f.message.split(":")[0]) for f in headings.run("== Port Operations ==\n", {})
    ]
    assert kinds == [("warning", "heading may be in title case")]
    assert headings.run("== Port operations ==\n== Rise of the Vell League ==\n", {}) == []
    ctx = {"names": ["Vell"]}
    assert headings.run("== Vell Harbor ==\n", ctx) == []


def test_a_heading_the_page_writes_in_capitals_in_its_prose_is_a_proper_name():
    # "the Imperial Navy" in a sentence shows the capitals are the name's, not title case.
    text = "The fleet of the Imperial Navy sails north.\n\n== Imperial Navy ==\nText.\n"
    assert headings.run(text, {}) == []
    # The phrase only in lower case, or only in the heading, proves nothing.
    for text in (
        "The port operations run all night.\n\n== Port Operations ==\n",
        "Text.\n\n== Port Operations ==\n== Port Operations history ==\n",
        # An infobox value or a table cell is not a sentence.
        "{{Infobox settlement\n| office = Port Operations\n}}\nText.\n\n== Port Operations ==\n",
        '{| class="wikitable"\n| Port Operations\n|}\nText.\n\n== Port Operations ==\n',
        # Nor is a ref body, a piped link's target or a category line.
        "Text.<ref>Port Operations Office, 1802.</ref>\n\n== Port Operations ==\n",
        "The [[Port Operations of Vell|harbor office]] opened.\n\n== Port Operations ==\n",
        "Text.\n\n== Port Operations ==\n[[Category:Port Operations]]\n",
    ):
        assert [f.message.split(":")[0] for f in headings.run(text, {})][:1] == [
            "heading may be in title case"
        ], text


def test_participants_is_the_first_closing_section():
    good = "== History ==\n== Participants ==\n== See also ==\n== Notes ==\n== References ==\n"
    assert headings.run(good, {}) == []
    late = "== History ==\n== References ==\n== Participants ==\n"
    assert _rules(headings.run(late, {})) == [(3, "error", "closing sections out of order")]
    low = "== History ==\n== participants ==\n"
    assert _rules(headings.run(low, {})) == [(2, "error", "standard heading in the wrong case")]


def test_a_heading_named_by_its_main_article_hatnote_is_a_proper_name():
    # Corpus: Foreign relations of Axxannuzru. The hatnote shows "Main article: Jagoton Compact".
    text = "Vell trades widely.\n\n== Treaties ==\n=== Jagoton Compact ===\n{{Main|Jagoton Compact}}\nIt was signed in 1802.\n"
    assert headings.run(text, {"title": "Vell"}) == []
    # A hatnote to some other page does not vouch for the heading's capitals.
    other = text.replace("{{Main|Jagoton Compact}}", "{{Main|Jagoton}}")
    assert [f.message.split(":")[0] for f in headings.run(other, {"title": "Vell"})] == [
        "heading may be in title case"
    ]
