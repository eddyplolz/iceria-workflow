"""The core of a {{Proposal}} form: filled in, a family the world has, a capital of its own."""

from checks import proposal

FULL = """{{Proposal
| name       = Halvorden
| claim      = Halvorden-claim.png
| family     = Thulean <!-- your culture family -->
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
    text = FULL.replace("Thulean <!-- your culture family -->", "Eostrian")
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
