"""The leak gate: a bot password in a file of the kit is found before anything runs."""

import subprocess

import pytest
import secrets_scan

PLANTED = "q7" * 16  # 32 lowercase letters and digits, the shape Special:BotPasswords hands out


@pytest.mark.parametrize(
    "line, what",
    [
        (f"password = {PLANTED}", "bot password"),
        # Split so this file does not trip the gate it tests.
        ("ICERIA_BOT_PASS" + "=hunter2hunter2", "bot password variable"),
    ],
)
def test_a_planted_secret_is_found(tmp_path, line, what):
    (tmp_path / "notes.md").write_text(f"Fine.\n{line}\n", encoding="utf-8")
    assert secrets_scan.scan(tmp_path) == [f"notes.md:2: {what}"]


def test_ordinary_text_and_an_empty_variable_pass(tmp_path):
    (tmp_path / "README.md").write_text(
        "Set ICERIA_BOT_PASS=<your bot password> in your shell.\n"
        "A revision id like 3017 or a 31-letter word abcdefghijabcdefghijabcdefghija.\n",
        encoding="utf-8",
    )
    assert secrets_scan.scan(tmp_path) == []


def test_the_hit_never_prints_the_secret(tmp_path):
    (tmp_path / "a.txt").write_text(PLANTED, encoding="utf-8")
    assert PLANTED not in "".join(secrets_scan.scan(tmp_path))


def test_an_untracked_or_ignored_draft_is_scanned_too(tmp_path):
    # A member's drafts are untracked and .env is ignored: those are where a password lands.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / "tracked.md").write_text(PLANTED, encoding="utf-8")
    (tmp_path / "draft.wiki").write_text(PLANTED, encoding="utf-8")
    (tmp_path / ".env").write_text(PLANTED, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.md"], check=True)
    assert secrets_scan.scan(tmp_path) == [
        ".env:1: bot password",
        "draft.wiki:1: bot password",
        "tracked.md:1: bot password",
    ]


def test_tool_folders_are_not_scanned(tmp_path):
    for folder in (".git", "__pycache__", ".pytest_cache", "node_modules", "env"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "x.txt").write_text(PLANTED, encoding="utf-8")
    (tmp_path / "env" / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
    assert secrets_scan.scan(tmp_path) == []


def test_a_hex_digest_is_not_a_bot_password(tmp_path):
    # Audit P1-5a: an md5 or a dashless uuid is 32 lowercase hex characters, and a member's notes
    # or a tool's output can hold one.
    (tmp_path / "notes.md").write_text(
        "md5 9e107d9d372bb6826bd81d3542a419d6\nid 0f8fad5bd9cb469fa16570867728950e\n",
        encoding="utf-8",
    )
    assert secrets_scan.scan(tmp_path) == []


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-le", "utf-16-be"])
def test_a_password_in_a_utf16_file_is_found(tmp_path, encoding):
    # Audit R10: PowerShell's > writes UTF-16, which put a NUL between every letter of the password.
    (tmp_path / ".env").write_bytes(f"Fine.\npassword = {PLANTED}\n".encode(encoding))
    assert secrets_scan.scan(tmp_path) == [".env:2: bot password"]
