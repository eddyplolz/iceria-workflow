import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
AGENTS = (KIT / "AGENTS.md").read_text(encoding="utf-8")


def test_claude_md_lists_exactly_the_skills_that_ship():
    listed = re.findall(
        r"^- `(iceria-[\w-]+)`", (KIT / "CLAUDE.md").read_text(encoding="utf-8"), re.M
    )
    shipped = sorted(p.parent.name for p in (KIT / ".claude" / "skills").glob("*/SKILL.md"))
    assert sorted(listed) == shipped
    assert len(shipped) == 6


def test_every_skill_and_tool_agents_md_names_exists():
    for skill in set(re.findall(r"`(iceria-[\w-]+)`", AGENTS)):
        assert (KIT / ".claude" / "skills" / skill / "SKILL.md").is_file(), skill
    tools = set(re.findall(r"python (tools/\w+\.py)", AGENTS))
    assert {"tools/doctor.py", "tools/map_overlay.py", "tools/redlinks.py"} <= tools
    for tool in tools:
        assert (KIT / tool).is_file(), tool


def test_lessons_and_reports_stay_out_of_git():
    # notes/ holds the member's lessons and problem reports; they choose what to send.
    assert "notes/" in (KIT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "notes/lessons.md" in AGENTS and "30 lines" in AGENTS
