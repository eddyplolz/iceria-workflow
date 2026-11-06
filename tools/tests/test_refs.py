from checks import refs

BAD = """'''Vell''' is a state.<ref name="a" /> It was founded in 1802.<ref name="b" />
Its claim is recorded in [[Proposal:Vell]].
It traded widely.<ref>[https://example.com A site]</ref>

== References ==
<references>
<ref name="a">[[Talk:Vell]]</ref>
<ref name="c">[[History of Iceria]]</ref>
</references>
"""


def test_each_reference_fault_is_named_on_its_line():
    found = refs.run(BAD, {})
    assert [(f.line, f.level, f.message.split(":")[0]) for f in found] == [
        (1, "error", "ref cited but never defined"),
        (2, "error", "body link to a proposal"),
        (3, "warning", "full ref in the body"),
        (3, "error", "outside source"),
        (7, "error", "ref to a meta page"),
        (8, "error", "ref defined but never cited"),
    ]


def test_list_defined_refs_to_wiki_pages_and_proposals_pass():
    clean = """'''Vell''' is a state.<ref name="a" /> It was founded in 1802.<ref name="b" />

== References ==
<references>
<ref name="a">[[History of Iceria]]</ref>
<ref name="b">[[Proposal:Vell|Vell proposal]]</ref>
</references>
"""
    assert refs.run(clean, {}) == []


def _kinds(text):
    return [(f.level, f.message.split(":")[0]) for f in refs.run(text, {})]


def test_meta_and_interwiki_links_in_prose_are_errors():
    for link in (
        "[[User:Eddy]]",
        "[[Water cooler]]",
        "[[The World of Iceria:Nations/Alexandria]]",
        "[[w:Harbor]]",
        "[[wikipedia:Harbor]]",
        "[[Talk:Vell]]",
    ):
        assert ("error", "link to a meta page in the text") in _kinds(f"It lies near {link}.\n")
    assert _kinds("It lies near [[Alexandria]] and [[:Category:Ports]].\n") == []


def test_a_ref_that_cites_a_person_or_an_outside_encyclopedia_is_an_error():
    assert ("error", "ref cites a person") in _kinds(
        '<ref name="a">Eddy, personal communication.</ref>'
    )
    assert ("error", "out-of-world voice in a ref") in _kinds(
        '<ref name="a">Encyclopaedia Britannica, "Harbors", 1998.</ref>'
    )
    assert _kinds('<ref name="a">[[Alexandria]]</ref>') == [("warning", "full ref in the body")]


def test_a_link_to_a_steward_page_in_prose_is_an_error():
    # Category:Meta Iceria holds these steward pages.
    for link in ("[[Charter]]", "[[World Standards|the standards]]", "[[Manual of Style]]"):
        assert ("error", "link to a meta page in the text") in _kinds(f"It follows {link}.\n")


def test_a_link_to_the_shared_world_reference_pages_is_a_warning():
    for link in (
        "[[History of Iceria]]",
        "[[Atlas of Iceria|atlas]]",
        "[[Culture zones of Iceria]]",
    ):
        assert ("warning", "link to a shared reference page") in _kinds(f"See {link}.\n")
    assert _kinds("It follows [[Charter]] in a ref.<ref>[[Charter]]</ref>\n")


def test_a_page_about_all_of_iceria_may_link_the_shared_reference_pages():
    # The warning says the link is "not part of this nation"; a world-wide page has no nation.
    text = "Every official map is in the [[Atlas of Iceria]].\n"
    for title in ("List of nations of Iceria", "Iceria", "2000 in Iceria"):
        assert refs.run(text, {"title": title}) == [], title
    for title in ("Alexandria", "Baudrix", "Icerian Navy"):
        found = refs.run(text, {"title": title})
        assert [f.message.split(":")[0] for f in found] == ["link to a shared reference page"]
    # A nation's own page is a nation's, even when its name ends "of Iceria".
    ctx = {"title": "Republic of Iceria", "nations": {"Republic of Iceria": "Port Alba"}}
    found = refs.run(text, ctx)
    assert [f.message.split(":")[0] for f in found] == ["link to a shared reference page"]


def test_a_user_link_is_allowed_only_in_a_nation_s_participants_list():
    text = """{{Infobox Country
}}
'''Vell''' is a state. [[User:Ada]] wrote it.

== Participants ==
* [[User:Example]] (creator)
* [[Water cooler]] (participant)
"""
    found = refs.run(text, {})
    assert [(f.line, f.message.split(":")[0]) for f in found] == [
        (3, "link to a meta page in the text"),
        (7, "link to a meta page in the text"),
    ]


def _numeric(name_attr):
    text = (
        f"'''Vell''' is a state.<ref {name_attr} /> It traded.<ref {name_attr} />\n\n"
        "== References ==\n<references>\n"
        f"<ref {name_attr}>[[History of Iceria]]</ref>\n</references>\n"
    )
    return [f.message for f in refs.run(text, {}) if f.level == "error"]


def test_all_digit_ref_name_is_an_error_in_every_quoting():
    for attr in ('name="1978"', "name='1978'", "name=1978"):
        found = _numeric(attr)
        assert found and all(m.startswith("all-digit ref name '1978'") for m in found), attr


def test_descriptive_ref_name_ending_in_digits_passes():
    assert _numeric('name="constitution1978"') == []
