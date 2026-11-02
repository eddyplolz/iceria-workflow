from checks import participants, refs, voice

NATION = """{{Infobox Country
| common_name = Vell
}}
'''Vell''' is a state.

== History ==
Vell was founded in 1802.

== Participants ==
* [[User:Example]] (creator)
* [[User:Sample]] (participant), writes the navy

== See also ==
"""


def _rules(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_a_nation_with_a_well_formed_list_passes():
    assert participants.run(NATION, {}) == []


def test_a_line_that_is_not_a_member_line_is_named():
    text = NATION.replace("* [[User:Sample]] (participant)", "* Sample (owner)")
    assert _rules(participants.run(text, {})) == [(11, "warning", "not a member line")]


def test_two_creators_are_named_on_the_second():
    text = NATION.replace("(participant)", "(creator)")
    assert _rules(participants.run(text, {})) == [(11, "warning", "more than one creator")]


def test_a_nation_without_participants_is_named():
    text = NATION.split("== Participants ==")[0] + "== See also ==\n"
    assert _rules(participants.run(text, {})) == [(1, "warning", "no Participants section")]


def test_a_participants_section_with_no_member_is_named():
    text = NATION.replace(
        "* [[User:Example]] (creator)\n* [[User:Sample]] (participant), writes the navy\n", ""
    )
    assert _rules(participants.run(text, {})) == [(9, "warning", "Participants lists no member")]


def test_participants_on_a_page_that_is_not_a_nation_is_named():
    text = NATION.replace("{{Infobox Country", "{{Infobox Person")
    assert _rules(participants.run(text, {})) == [
        (9, "warning", "Participants on a page that is not a nation")
    ]


def test_prose_checks_skip_the_participants_list_but_not_the_body():
    text = NATION.replace("writes the navy", "one of the players who writes the navy")
    assert voice.run(text, {}) == []
    body = text.replace("Vell was founded in 1802.", "Vell was founded by its players in 1802.")
    assert [f.line for f in voice.run(body, {})] == [7]


def test_a_participants_subsection_is_prose_and_not_the_list():
    text = NATION.replace(
        "Vell was founded in 1802.",
        "Vell was founded in 1802.\n\n=== Participants ===\nIts players met in 1802.",
    ).replace("== Participants ==\n* [[User:Example]]", "== Members ==\n* [[User:Example]]")
    assert [f.line for f in voice.run(text, {})] == [10]
    assert _rules(participants.run(text, {})) == [(1, "warning", "no Participants section")]


def test_a_participants_section_off_a_nation_is_still_prose():
    text = NATION.replace("{{Infobox Country", "{{Infobox Person").replace(
        "writes the navy", "one of the players"
    )
    assert [f.line for f in voice.run(text, {})] == [11]
    assert [f.line for f in refs.run(text, {}) if "meta page" in f.message] == [10, 11]


def test_categories_after_a_last_participants_section_are_not_member_lines():
    text = NATION.replace("== See also ==\n", "[[Category:Vell]]\n{{DEFAULTSORT:Vell}}\n")
    assert participants.run(text, {}) == []


def test_a_commented_out_infobox_does_not_make_a_nation():
    text = NATION.replace(
        "{{Infobox Country\n| common_name = Vell\n}}", "<!-- {{Infobox Country}} -->"
    )
    assert _rules(participants.run(text, {})) == [
        (7, "warning", "Participants on a page that is not a nation")
    ]


def test_an_infobox_spelled_with_two_spaces_is_still_a_nation():
    assert participants.run(NATION.replace("Infobox Country", "Infobox  Country"), {}) == []


def test_the_template_s_placeholder_name_is_named():
    text = NATION.replace("User:Example", "User:YourName")
    assert _rules(participants.run(text, {})) == [(10, "warning", "placeholder member")]


def test_the_missing_section_message_quotes_the_manual():
    text = NATION.split("== Participants ==")[0]
    (found,) = participants.run(text, {})
    assert "creator first" not in found.message
    assert "its creator where it has one" in found.message


def test_a_placeholder_written_as_two_words_is_named():
    for name in ("Your Name", "Your_Name"):
        text = NATION.replace("User:Example", f"User:{name}")
        assert _rules(participants.run(text, {})) == [(10, "warning", "placeholder member")]


def test_a_template_spanning_lines_after_the_list_holds_no_member_lines():
    text = NATION.replace("== See also ==\n", "{{Navbox\n|list=\n[[Alba]] and [[Mantua]]\n}}\n")
    assert participants.run(text, {}) == []
