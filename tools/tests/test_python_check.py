"""An old Python stops every kit tool with the fix, and a new one passes straight through."""

import importlib
import sys

import pytest

TOOLS = ("check", "setup_bot", "refresh_canon")


def test_python_3_9_is_stopped_with_the_fix(monkeypatch):
    import kit_python

    monkeypatch.setattr(sys, "version_info", (3, 9, 6, "final", 0))
    with pytest.raises(SystemExit, match="Python 3.10 or newer") as stop:
        importlib.reload(kit_python)
    assert "python.org" in str(stop.value)


def test_python_3_10_passes(monkeypatch):
    import kit_python

    monkeypatch.setattr(sys, "version_info", (3, 10, 0, "final", 0))
    importlib.reload(kit_python)


@pytest.mark.parametrize("tool", TOOLS)
def test_each_tool_checks_the_python_before_anything_else(tool):
    # Before any other kit import, which is where an old Python would fail first.
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / f"{tool}.py").read_text(encoding="utf-8")
    kit_imports = [
        line
        for line in source.splitlines()
        if line.startswith(("import ", "from "))
        and line.split()[1].split(".")[0] not in sys.stdlib_module_names
    ]
    assert kit_imports[0] == "import kit_python  # noqa: F401  stops on Python < 3.10"
