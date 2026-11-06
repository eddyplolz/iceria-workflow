"""The core of a {{Proposal}} form: filled in, a family the world has, a capital of its own."""

from checks import proposal

FULL = """{{Proposal
| name       = Halvorden
| claim      = Halvorden-claim.png
| family     = Thulean
| twist      =
| history    = Settlers reached the fjord around 1190.
| capital    = Brannvik
| differs    =
| problem    = The fish stocks have thinned.
| neighbor   =
| status     = draft
}}
"""
CTX = {"form": True, "families": ["Hesperic", "Thulean"], "nations": {"Mantua": "Cavaletta"}}


def _run(text, **ctx):
    return [(f.line, f.level, f.message) for f in proposal.run(text, {**CTX, **ctx})]


def test_a_full_core_passes():
    assert _run(FULL) == []


def test_a_page_that_is_not_a_form_is_not_read():
    assert proposal.run(FULL.replace("capital    = Brannvik", "capital    ="), {}) == []


def test_each_empty_core_field_is_an_error_on_its_line():
    text = FULL.replace("= Brannvik", "= <!-- its name -->")
    assert _run(text) == [
        (
            7,
            "error",
            "the core field 'capital' is empty: fill it in before the form goes to the "
            "stewards (Template:Proposal)",
        )
    ]


def test_one_of_differs_problem_or_neighbor_is_needed():
    text = FULL.replace("= The fish stocks have thinned.", "=")
    assert _run(text) == [
        (
            1,
            "error",
            "the core asks for one of differs, problem or neighbor: answer one of them "
            "in a few sentences (Template:Proposal)",
        )
    ]


def test_a_family_the_world_does_not_have_is_an_error():
    text = FULL.replace("= Thulean", "= Eostrian")
    assert _run(text) == [
        (
            4,
            "error",
            "family is not a culture family of Iceria: Eostrian; use one from "
            "canon/culture-zones.md, such as Hesperic or Thulean (Culture zones of Iceria)",
        )
    ]
    assert _run(text.replace("Eostrian", "thulean")) == []
    assert _run(text, families=[]) == []


def test_another_nation_s_capital_is_an_error():
    text = FULL.replace("Brannvik", "Cavaletta")
    assert _run(text) == [
        (
            7,
            "error",
            "capital is already the capital of Mantua: Cavaletta; give your nation a "
            "capital of its own (World Standards 6)",
        )
    ]


def test_a_name_that_is_already_a_canon_nation_is_an_error():
    ctx = {"nations": {"Mantua": "Cavaletta", "Alexandria": "Port Alba"}}
    assert _run(FULL.replace("Halvorden\n", "Alexandria\n", 1), **ctx) == [
        (
            2,
            "error",
            "name is already a nation of Iceria: Alexandria; choose a name of your own "
            "(World Standards 6.5)",
        )
    ]
    assert [m for _, _, m in _run(FULL.replace("= Halvorden\n", "= alexandria\n"), **ctx)] == [
        "name is already a nation of Iceria: alexandria; choose a name of your own "
        "(World Standards 6.5)"
    ]


def test_a_name_that_is_a_real_world_country_is_an_error():
    assert _run(FULL.replace("= Halvorden\n", "= France\n")) == [
        (
            2,
            "error",
            "name is a real-world place: France; Iceria has its own names (World Standards 6.2, "
            "MoS 7.2)",
        )
    ]


def test_the_prose_answers_are_read_for_dashes_bold_lead_ins_and_real_places():
    text = FULL.replace(
        "Settlers reached the fjord around 1190.",
        "'''Origin:''' Settlers — mostly from Norway — reached the fjord.",
    )
    assert _run(text) == [
        (6, "warning", "em dash: recast the sentence; MoS 6.4 allows no dashes in prose"),
        (6, "warning", "'''Origin:''': bolded lead-in (MoS 4.3)"),
        (6, "warning", "real-world name: Norway; Iceria has its own places (MoS 7.2)"),
    ]


def test_a_proposal_may_speak_about_iceria_as_a_project():
    text = FULL.replace(
        "Settlers reached the fjord around 1190.",
        "Settlers reached the fjord; see the wiki and Discord.",
    )
    assert _run(text) == []


def test_an_answer_shorter_than_a_sentence_is_a_warning():
    assert _run(FULL.replace("The fish stocks have thinned.", "asdf")) == [
        (
            9,
            "warning",
            "problem is too short to be an answer: write a sentence or two (Template:Proposal)",
        )
    ]
    assert [
        m for _, _, m in _run(FULL.replace("Settlers reached the fjord around 1190.", "N/A"))
    ] == ["history is too short to be an answer: write a sentence or two (Template:Proposal)"]


def test_the_claim_is_the_name_of_an_image_file():
    assert _run(FULL.replace("Halvorden-claim.png", "my claim")) == [
        (
            3,
            "error",
            "claim is not an image file name: my claim; give the file you uploaded, such as "
            "Halvorden-claim.png (Template:Proposal)",
        )
    ]
    for ok in ("Halvorden-claim.JPG", "claim.svg", "a b.jpeg"):
        assert _run(FULL.replace("Halvorden-claim.png", ok)) == []


def test_a_comment_in_the_form_is_left_to_the_comments_check():
    text = FULL.replace("= Thulean", "= Thulean <!-- your culture family -->")
    assert _run(text) == []


def test_an_answer_may_start_on_the_line_below_its_field():
    # Accepted proposals (Axxannuzru, Xuna) write the history as paragraphs under "| history =".
    text = FULL.replace(
        "| history    = Settlers reached the fjord around 1190.\n",
        "| history    =\nSettlers reached the fjord around 1190.\n\nThe jarls ruled it after.\n",
    )
    assert _run(text) == []
    assert proposal._fields(text)["history"] == (
        6,
        "Settlers reached the fjord around 1190.\n\nThe jarls ruled it after.",
    )


def test_a_value_ends_at_the_next_field_or_the_close_of_the_form():
    fields = proposal._fields(FULL.replace("| status     = draft\n}}", "| status = draft }}"))
    assert fields["status"] == (11, "draft")
    assert fields["problem"] == (9, "The fish stocks have thinned.")


def test_a_field_the_kit_does_not_know_still_ends_the_answer_above_it():
    # On the wiki any top-level "| x =" starts a new field, whatever its name.
    text = FULL.replace("| family", "| flag       = Halvorden-flag.png\n| family")
    assert _run(text) == []


def test_one_line_outside_the_form_is_counted_in_the_singular():
    body, found = proposal.scope("A note.\n{{Proposal\n| name = Vell\n}}\n")
    assert [(f.line, f.message.split(":")[0]) for f in found] == [
        (1, "1 line outside the {{Proposal}} form was not checked")
    ]
    assert body.splitlines()[0].strip() == ""
