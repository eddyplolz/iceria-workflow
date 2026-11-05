import json

import check
import iceria_wiki

GOOD = """{{SHORTDESC:State on the Serenian Ocean}}
'''Vell''' is a state on the Serenian Ocean.<ref name="ws" />

== History ==
Vell was founded in 1802.<ref name="ws" />

== References ==
<references>
<ref name="ws">[[World Standards]]</ref>
</references>

[[Category:Nations]]
"""


def _kit(tmp_path, date=None):
    (tmp_path / "canon").mkdir()
    geo = {
        "oceans": [{"id": "o1", "name": "Serenian Ocean"}],
        "ranges": [{"id": "r1", "name": "the Dorsal Range"}],
    }
    zones = {"zones": [{"id": "z1", "family": "Vellic"}]}
    (tmp_path / "canon" / "geography.json").write_text(json.dumps(geo), encoding="utf-8")
    (tmp_path / "canon" / "culture-zones.json").write_text(json.dumps(zones), encoding="utf-8")
    (tmp_path / "VERSION.json").write_text(json.dumps({"in_world_date": date}), encoding="utf-8")
    return tmp_path


def test_context_comes_from_the_canon_files(tmp_path):
    ctx = check.load_ctx(_kit(tmp_path, "4 Frost 1820"))
    assert ctx == {
        "names": ["Serenian Ocean", "the Dorsal Range"],
        "families": ["Vellic"],
        "in_world_date": "4 Frost 1820",
    }


def test_nations_and_their_capitals_come_from_the_nation_infoboxes(tmp_path):
    nations = tmp_path / "canon" / "nations"
    nations.mkdir(parents=True)
    (nations / "vell.md").write_text(
        "# Vell\n\n## Infobox\n\n- common_name: Vell (pronounced 'vel')\n- capital: [[Orra]]\n",
        encoding="utf-8",
    )
    (nations / "brenn.md").write_text("# Brenn\n\n- common_name: Brenn\n", encoding="utf-8")
    assert check.load_ctx(tmp_path) == {"nations": {"Vell": "Orra", "Brenn": None}}


def test_a_nation_page_titled_with_its_long_name_maps_to_its_common_name(tmp_path):
    nations = tmp_path / "canon" / "nations"
    nations.mkdir(parents=True)
    (nations / "kingdom-of-vell.md").write_text(
        "# Kingdom of Vell\n\n- common_name: Vell\n- capital: Orra\n", encoding="utf-8"
    )
    ctx = check.load_ctx(tmp_path)
    assert ctx["nation_pages"] == {"Kingdom of Vell": "Vell"}


def test_a_kit_without_canon_files_has_an_empty_context(tmp_path):
    assert check.load_ctx(tmp_path) == {}


def test_clean_draft_exits_zero(tmp_path, capsys):
    draft = tmp_path / "vell.wiki"
    draft.write_text(GOOD, encoding="utf-8")
    (tmp_path / "kit").mkdir()
    assert (
        check.main(
            [str(draft), "--title", "Vell", "--root", str(_kit(tmp_path / "kit")), "--offline"]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "vell.wiki: 0 errors, 0 warnings"


def test_errors_print_by_line_and_exit_one(tmp_path, capsys):
    draft = tmp_path / "vell.wiki"
    draft.write_text(
        GOOD.replace("founded in 1802", "founded in 1802 — by sea").replace(
            "Serenian Ocean.", "Serenyan Ocean."
        ),
        encoding="utf-8",
    )
    (tmp_path / "kit").mkdir()
    assert (
        check.main(
            [str(draft), "--title", "Vell", "--root", str(_kit(tmp_path / "kit")), "--offline"]
        )
        == 1
    )
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "vell.wiki:2: names: warning: unofficial feature name: 'Serenyan Ocean' is not on the world map (MoS 7.3)",
        "vell.wiki:2: names: warning: near an official name: 'Serenyan' looks like 'Serenian' (MoS 7.3)",
        "vell.wiki:5: dashes: error: em dash: recast the sentence; MoS 6.4 allows no dashes in prose",
        "vell.wiki: 1 error, 2 warnings",
    ]


def _run(tmp_path, data: bytes, capsys, name="vell.wiki"):
    draft = tmp_path / name
    draft.write_bytes(data)
    kit = tmp_path / "kit"
    if not kit.exists():
        kit.mkdir()
        _kit(kit)
    code = check.main([str(draft), "--title", "Vell", "--root", str(kit), "--offline"])
    return code, capsys.readouterr()


def test_a_draft_saved_with_a_bom_or_as_utf16_reads_as_plain_utf8(tmp_path, capsys):
    # Audit bug 3: Notepad's UTF-8 BOM hid the lead's bold, and PowerShell's UTF-16 crashed.
    plain = _run(tmp_path, GOOD.encode("utf-8"), capsys)
    assert plain[0] == 0
    assert _run(tmp_path, GOOD.encode("utf-8-sig"), capsys) == plain
    assert _run(tmp_path, GOOD.encode("utf-16"), capsys) == plain


def _humanize(tmp_path, monkeypatch, on_path, installed):
    ran = []
    monkeypatch.setattr(check.shutil, "which", lambda name: on_path)
    monkeypatch.setattr(check.importlib.util, "find_spec", lambda name: installed)
    monkeypatch.setattr(check.subprocess, "run", lambda argv, **kw: ran.append(argv))
    draft = tmp_path / "vell.wiki"
    draft.write_text(GOOD, encoding="utf-8")
    (tmp_path / "kit").mkdir()
    check.main([str(draft), "--humanizer", "--offline", "--root", str(_kit(tmp_path / "kit"))])
    return ran, str(draft)


def test_humanizer_runs_from_the_command_when_it_is_on_the_path(tmp_path, monkeypatch):
    ran, draft = _humanize(tmp_path, monkeypatch, "/bin/humanizer-audit", None)
    assert ran == [["/bin/humanizer-audit", draft]]


def test_humanizer_runs_as_a_module_when_pip_left_it_off_the_path(tmp_path, monkeypatch):
    # Windows: pip puts the command in a Scripts folder the python.org installer leaves off PATH.
    ran, draft = _humanize(tmp_path, monkeypatch, None, object())
    assert ran == [[check.sys.executable, "-m", "humanizer_audit", draft]]


def test_humanizer_missing_says_how_to_install_it(tmp_path, monkeypatch, capsys):
    ran, _ = _humanize(tmp_path, monkeypatch, None, None)
    assert ran == []
    assert "pip install humanizer-pro" in capsys.readouterr().err


def test_a_draft_in_another_encoding_is_refused_with_how_to_fix_it(tmp_path, capsys):
    code, out = _run(tmp_path, "Vell is a state in Vallée.\n".encode("cp1252"), capsys)
    assert code == 2
    assert "save it as UTF-8" in out.err


def test_a_draft_that_is_not_there_is_named_with_how_to_fix_it(tmp_path, capsys):
    code = check.main([str(tmp_path / "vell.wiki"), "--root", str(_kit(tmp_path)), "--offline"])
    err = capsys.readouterr().err
    assert code == 2
    assert "no file at" in err and "vell.wiki" in err


def test_the_install_hint_names_the_python_that_runs_the_kit(tmp_path, monkeypatch, capsys):
    # A bare "python" can be another install, or the Microsoft Store stub, so pip lands elsewhere.
    monkeypatch.setattr(check.sys, "executable", r"C:\Program Files\Python313\python.exe")
    _humanize(tmp_path, monkeypatch, None, None)
    err = capsys.readouterr().err
    assert r'"C:\Program Files\Python313\python.exe" -m pip install humanizer-pro' in err


FORM = (
    "{{Proposal\n| name = Vell\n| claim = Vell-claim.png\n"
    "| family = Vellic\n| history = Founded in 1802.\n| capital = Port Vell\n"
    "| problem = Its harbor silts up.\n| status = draft\n}}\n"
)


def test_a_hidden_comment_fails_a_form_and_an_article_alike(tmp_path, capsys):
    form, article = tmp_path / "proposal.wiki", tmp_path / "vell.wiki"
    form.write_text(FORM.replace("| status = draft", "| status = draft <!-- x -->"), "utf-8")
    article.write_text(GOOD.replace("== History ==", "== History ==\n<!-- x -->"), "utf-8")
    for draft, line in ((form, 8), (article, 5)):
        code = check.main([str(draft), "--title", "Vell", "--root", str(tmp_path), "--offline"])
        out = capsys.readouterr().out
        assert code == 1
        assert f"{draft.name}:{line}: comments: error: hidden comment" in out


def test_a_proposal_form_is_not_held_to_the_article_rules(tmp_path, capsys):
    draft = tmp_path / "proposal.wiki"
    draft.write_text(FORM, encoding="utf-8")
    assert check.main([str(draft), "--root", str(tmp_path), "--offline"]) == 0
    assert "no category" not in capsys.readouterr().out


def test_a_form_after_other_text_is_still_read_as_a_form(tmp_path, capsys):
    # Accepted proposals open with a note or a heading above the form (Tleyew-Pas has 51 lines).
    draft = tmp_path / "proposal.wiki"
    draft.write_text(
        "== Proposal ==\nSent by '''Vell''' - with thanks.\n\n"
        + FORM.replace("| capital = Port Vell", "| capital ="),
        encoding="utf-8",
    )
    assert check.main([str(draft), "--root", str(tmp_path), "--offline"]) == 1
    out = capsys.readouterr().out
    assert "proposal.wiki:9: proposal: error: the core field 'capital' is empty" in out
    assert (
        "proposal.wiki:1: proposal: warning: 2 lines outside the {{Proposal}} form were not "
        "checked: the stewards read the form" in out
    )
    for rule in ("headings", "bold", "dashes", "markup", "refs"):
        assert f": {rule}: " not in out, rule


def test_a_nation_checking_its_own_accepted_proposal_is_not_told_it_clashes(tmp_path, capsys):
    # Once Vell is admitted its proposal names a canon nation and that nation's capital.
    (tmp_path / "kit").mkdir()
    kit = _kit(tmp_path / "kit")
    (kit / "canon" / "nations").mkdir()
    (kit / "canon" / "nations" / "vell.md").write_text(
        "# Vell\n\n- common_name: Vell\n- capital: Port Vell\n", encoding="utf-8"
    )
    draft = tmp_path / "proposal.wiki"
    draft.write_text(FORM, encoding="utf-8")
    args = [str(draft), "--root", str(kit), "--offline"]
    assert check.main(args) == 1
    assert "name is already a nation of Iceria: Vell" in capsys.readouterr().out
    assert check.main([*args, "--own-nation", "Vell"]) == 0
    assert "already" not in capsys.readouterr().out


def test_a_project_page_is_checked_only_for_hidden_comments(tmp_path, capsys):
    # Pages such as World Standards are the project speaking about itself, not in-world articles.
    body = "In Iceria a war is a story - agreed on Discord.\n<!-- x -->\n"
    for page in (
        "{{Iceria Meta Masthead|Dice table|How a war is settled}}\n" + body,
        body + "[[Category:Meta Iceria]]\n",
    ):
        draft = tmp_path / "dice.wiki"
        draft.write_text(page, encoding="utf-8")
        assert check.main([str(draft), "--root", str(tmp_path), "--offline"]) == 1
        out = capsys.readouterr().out
        found = [ln.split(": ")[1] for ln in out.splitlines()[:-1]]
        assert found == ["markup", "comments"], out
        assert (
            "dice.wiki:1: markup: warning: a project page (Iceria Meta Masthead or Category:Meta "
            "Iceria): only hidden comments were checked, since the Manual of Style is for articles"
        ) in out


def test_a_form_value_may_speak_about_the_project(tmp_path, capsys):
    draft = tmp_path / "proposal.wiki"
    draft.write_text(
        FORM.replace("name = Vell", "name = Vell, as agreed on Discord"), encoding="utf-8"
    )
    assert check.main([str(draft), "--root", str(tmp_path), "--offline"]) == 0
    assert "out-of-world" not in capsys.readouterr().out


class BlockedWiki:
    def __getattr__(self, name):
        def refuse(*args, **kwargs):
            raise iceria_wiki.WikiBlocked()

        return refuse


def test_a_firewall_refusal_does_not_blame_the_connection(tmp_path, monkeypatch, capsys):
    draft = tmp_path / "vell.wiki"
    draft.write_text(GOOD, encoding="utf-8")
    (tmp_path / "kit").mkdir()
    monkeypatch.setattr(check, "Wiki", BlockedWiki)
    assert check.main([str(draft), "--title", "Vell", "--root", str(_kit(tmp_path / "kit"))]) == 2
    err = capsys.readouterr().err
    assert err.startswith("NOT CHECKED: categories, infobox fields and links were not looked up.")
    assert "firewall refused this computer (HTTP 403)" in err
    assert "connection" not in err
