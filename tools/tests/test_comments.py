"""No page carries a hidden <!-- --> comment: each one is an error, in every kind of page."""

from pathlib import Path

from checks import comments

MESSAGE = "hidden comment: delete it, pages on Iceria carry no <!-- --> comments"


def _run(text, **ctx):
    return [(f.line, f.level, f.message) for f in comments.run(text, ctx)]


def test_each_comment_is_an_error_on_the_line_it_opens():
    text = "Vell is a port.\n<!-- say more -->\nIt has a harbor. <!-- a\nlong one -->\n"
    assert _run(text) == [(2, "error", MESSAGE), (3, "error", MESSAGE)]


def test_an_unclosed_comment_is_caught_too():
    assert _run("Text.\n\n<!-- forgot to close it\nmore\n") == [(3, "error", MESSAGE)]


def test_a_form_and_a_project_page_get_no_pass():
    form = "{{Proposal\n| name = Vell <!-- your nation's name -->\n}}\n"
    assert _run(form, form=True) == [(2, "error", MESSAGE)]
    assert _run(form, project=True) == [(2, "error", MESSAGE)]


def test_nowiki_and_pre_are_not_comments():
    assert _run("<nowiki><!-- shown as text --></nowiki>\n<pre>x</pre>\n__NOTOC__\n") == []


def test_no_template_in_the_kit_carries_a_comment():
    # A member copies a template into a draft; a comment in it would fail that draft.
    kit = Path(__file__).resolve().parents[2]
    found = {
        p.name: len(comments.run(p.read_text("utf-8"), {})) for p in kit.glob("templates/*.wiki")
    }
    assert found and set(found.values()) == {0}, found
