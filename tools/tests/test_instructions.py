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


def test_agents_md_the_draft_skill_and_the_readme_all_send_drafts_to_notes_drafts():
    readme = (KIT / "README.md").read_text(encoding="utf-8")
    skill = (KIT / ".claude" / "skills" / "iceria-draft" / "SKILL.md").read_text(encoding="utf-8")
    for text in (AGENTS, skill, readme):
        assert "notes/drafts/" in text


def test_the_readme_marks_the_two_paths_no_person_has_run_as_untested():
    readme = (KIT / "README.md").read_text(encoding="utf-8")
    start = readme.split("## Start")[1].split("\n## ")[0]
    rows = [r.split("|")[1:3] for r in start.splitlines() if r.startswith("| ")]
    by_runtime = {runtime.strip(): how for runtime, how in rows}
    codex = next(k for k in by_runtime if k.startswith("Codex"))
    projects = next(k for k in by_runtime if k.startswith("A claude.ai"))
    claude = next(k for k in by_runtime if k.startswith("Claude Code"))
    assert "untested" in codex and "untested" in projects
    assert "untested" not in claude and "untested" not in by_runtime[claude]


def test_the_readme_gives_the_documented_install_commands_for_a_novice():
    readme = (KIT / "README.md").read_text(encoding="utf-8")
    assert "curl -fsSL https://claude.ai/install.sh | bash" in readme
    assert "irm https://claude.ai/install.ps1 | iex" in readme
    assert "https://code.claude.com/docs/en/terminal-guide" in readme
