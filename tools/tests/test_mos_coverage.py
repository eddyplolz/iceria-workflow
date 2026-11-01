import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
COVERAGE = (KIT / "style" / "mos-coverage.md").read_text(encoding="utf-8")
CHECKLIST = (KIT / "style" / "writing-checklist.md").read_text(encoding="utf-8")
HOLDERS = re.compile(r"^check: \w+$|^checklist \d+$|^template$|^steward$|^by hand$")


def _rows():
    return [
        (cells[1].strip(), [h.strip() for h in cells[3].split(";")])
        for cells in (line.split("|") for line in COVERAGE.splitlines())
        if re.match(r"\d", cells[1].strip() if len(cells) > 3 else "")
    ]


def test_every_row_says_what_holds_its_rule():
    rows = _rows()
    assert len(rows) == 83
    bad = [(n, h) for n, held in rows for h in held if not HOLDERS.match(h)]
    assert bad == []


def test_every_check_named_is_a_module_in_checks():
    named = {h.split()[1] for _, held in _rows() for h in held if h.startswith("check:")}
    modules = {p.stem for p in (KIT / "tools" / "checks").glob("*.py")} - {"__init__"}
    assert named and named - modules == set()


def test_every_checklist_rule_named_exists():
    rules = {int(n) for n in re.findall(r"^(\d+)\. ", CHECKLIST, re.M)}
    named = {int(h.split()[1]) for _, held in _rows() for h in held if h.startswith("checklist")}
    assert rules == set(range(1, 22))
    assert named - rules == set()
