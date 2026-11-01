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
