"""Tool messages that send a member to a README step must name steps that exist.

The README is the only place the setup steps live. Renumbering it turns these tests red, so no
message can keep pointing at a step that moved.
"""

import importlib
import re
import sys
from pathlib import Path

import pytest

README = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
MAC_HEADING = "Set up a Mac (once)"
WINDOWS_HEADING = "Set up Windows (once)"


def _section(heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## )", README, re.S | re.M)
    assert match, f"README.md has no '## {heading}' heading"
    return match.group(1)


def test_both_setup_headings_exist():
    _section(MAC_HEADING)
    _section(WINDOWS_HEADING)


def test_the_humanizer_is_step_7_on_a_mac():
    step = re.search(r"^7\. \*\*(.*?)\*\*", _section(MAC_HEADING), re.M)
    assert step and "AI-tell audit" in step.group(1)


def test_the_humanizer_is_step_5_on_windows():
    row = re.search(r"^\| 5\. (.*?) \|", _section(WINDOWS_HEADING), re.M)
    assert row and "AI-tell audit" in row.group(1)


def test_python_is_step_1_on_both_systems():
    assert re.search(r"^1\. \*\*Install Python", _section(MAC_HEADING), re.M)
    assert re.search(r"^\| 1\. Python \|", _section(WINDOWS_HEADING), re.M)


def test_the_old_python_message_names_headings_that_exist(monkeypatch):
    import kit_python

    monkeypatch.setattr(sys, "version_info", (3, 9, 6, "final", 0))
    with pytest.raises(SystemExit) as stop:
        importlib.reload(kit_python)
    message = str(stop.value)
    assert MAC_HEADING in message and WINDOWS_HEADING in message
    assert "Set up your computer" not in message
    assert "step 1" in message


def test_the_missing_humanizer_message_names_both_step_numbers(tmp_path, monkeypatch, capsys):
    from test_check_cli import _humanize

    _humanize(tmp_path, monkeypatch, None, None)
    err = capsys.readouterr().err
    assert f"'{MAC_HEADING}' step 7" in err
    assert f"'{WINDOWS_HEADING}' step 5" in err
    assert "setup step 5" not in err
