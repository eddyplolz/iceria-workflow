"""doctor.py: one OK or FIX line per part of the setup, and nothing written anywhere."""

import datetime
import json
import subprocess

import cred_store
import doctor
import iceria_wiki
import pytest

TODAY = datetime.date(2026, 11, 20)


def _fixes(results):
    return [r.name for r in results if r.fix]


class Wiki:
    def __init__(self, down=None):
        self.down = down

    def latest_revids(self, titles):
        if self.down:
            raise iceria_wiki.WikiUnavailable(self.down)
        return dict.fromkeys(titles, 1)


def _kit(tmp_path, built="2026-11-10"):
    (tmp_path / "VERSION.json").write_text(json.dumps({"built": built}), encoding="utf-8")
    return tmp_path


def _setup(monkeypatch, cas=150, login=("Ana@kit", "Windows Credential Manager"), humanizer=True):
    monkeypatch.setattr(doctor, "_ca_count", lambda: cas)
    monkeypatch.setattr(doctor.cred_store, "who", lambda: login)
    monkeypatch.setattr(doctor.check.shutil, "which", lambda name: "/bin/x" if humanizer else None)
    monkeypatch.setattr(doctor.check.importlib.util, "find_spec", lambda name: None)


def test_a_working_setup_is_all_ok_and_exits_zero(tmp_path, monkeypatch, capsys):
    _setup(monkeypatch)
    assert doctor.main(_kit(tmp_path), Wiki(), TODAY) == 0
    out = capsys.readouterr().out.splitlines()
    end = out.index("7 of 7 checks are OK.")
    assert all(line.startswith("OK ") for line in out[:end])
    assert any("Ana@kit" in line and "Credential Manager" in line for line in out)


def test_each_problem_is_a_fix_line_with_one_step(tmp_path, monkeypatch, capsys):
    _setup(monkeypatch, cas=0, humanizer=False)
    code = doctor.main(_kit(tmp_path, "2026-09-01"), Wiki(down="timed out"), TODAY)
    assert code == 1
    out = capsys.readouterr().out
    assert "FIX certificates" in out and "Install Certificates.command" in out
    assert "FIX wiki" in out and "timed out" in out
    assert "FIX canon copy" in out and "80 days old" in out and "refresh_canon.py --check" in out
    assert "FIX humanizer" not in out  # optional, so never a fix
    assert "4 of 7 checks are OK; fix the 3 above, then run this again." in out


def test_a_missing_humanizer_is_an_optional_line_and_still_exits_zero(
    tmp_path, monkeypatch, capsys
):
    # A clean install has no humanizer, and FIX is kept for what blocks the kit.
    _setup(monkeypatch, humanizer=False)
    assert doctor.main(_kit(tmp_path), Wiki(), TODAY) == 0
    out = capsys.readouterr().out
    assert "OK  humanizer: optional, not installed: to add it, " in out
    assert "-m pip install humanizer-pro" in out and "FIX" not in out


def test_no_saved_login_is_fine_since_the_tools_read_as_a_guest(monkeypatch):
    _setup(monkeypatch, login=None)
    r = doctor.login()
    assert r.fix is None and "setup_bot.py" in r.detail


def test_a_machine_with_no_store_gets_the_stores_own_fix(monkeypatch):
    def none():
        raise cred_store.NoStore("no credential store: install one with `pip install keyring`")

    monkeypatch.setattr(doctor.cred_store, "who", none)
    r = doctor.login()
    assert r.fix and "pip install keyring" in r.fix


def test_a_kit_without_its_version_file_says_to_get_the_kit_again(tmp_path):
    r = doctor.canon_copy(tmp_path, TODAY)
    assert r.fix and "git pull" in r.fix


def test_humanizer_found_as_a_module_off_the_path_is_ok(monkeypatch):
    monkeypatch.setattr(doctor.check.shutil, "which", lambda name: None)
    monkeypatch.setattr(doctor.check.importlib.util, "find_spec", lambda name: object())
    assert doctor.humanizer().fix is None


def test_the_doctor_never_reads_the_password():
    # The keychain check goes through who(), which looks up the login name alone.
    src = (doctor.Path(doctor.__file__)).read_text(encoding="utf-8")
    assert "cred_store.get(" not in src and ".read()" not in src


def test_the_humanizer_line_names_the_python_that_runs_the_kit(monkeypatch):
    _setup(monkeypatch, humanizer=False)
    monkeypatch.setattr(doctor.sys, "executable", "/usr/local/bin/python3.13")
    r = doctor.humanizer()
    assert r.fix is None
    assert r.detail.endswith("to add it, /usr/local/bin/python3.13 -m pip install humanizer-pro")


def test_help_prints_usage_and_runs_no_check(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "main", lambda *a, **k: pytest.fail("--help ran the checks"))
    with pytest.raises(SystemExit) as e:
        doctor.cli(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("usage:") and "OK " not in out


def _block(out):
    return out[out.index("--- for the maintainer: copy from here ---") :]


def test_the_support_block_carries_the_setup_and_never_the_login(tmp_path, monkeypatch, capsys):
    _setup(monkeypatch)
    monkeypatch.setattr(doctor.cred_store, "who", cred_store.who)  # the real lookup, off the env
    monkeypatch.setenv("ICERIA_BOT_USER", "Ana@kit")
    monkeypatch.setenv("ICERIA_BOT_PASS", "s3cretbotpassw0rd")
    monkeypatch.setattr(doctor.sys, "executable", "/usr/local/bin/python3.13")
    ran = subprocess.CompletedProcess([], 0, stdout="ab12cd3\n", stderr="")
    monkeypatch.setattr(doctor.subprocess, "run", lambda *a, **k: ran)
    doctor.main(_kit(tmp_path), Wiki(), TODAY)
    block = _block(capsys.readouterr().out)
    assert "OS: " in block
    assert f"Python: {doctor.sys.version.split()[0]} at /usr/local/bin/python3.13" in block
    assert "Kit commit: ab12cd3" in block
    assert (
        "Checks: Python OK, certificates OK, bot login OK, wiki OK, canon copy OK, refreshed files OK, humanizer OK"
        in block
    )
    assert "Bot login saved: yes" in block
    assert "Ana@kit" not in block and "s3cretbotpassw0rd" not in block
    assert block.rstrip().endswith("--- to here ---")


def test_the_support_block_says_no_login_and_marks_each_fix(tmp_path, monkeypatch, capsys):
    _setup(monkeypatch, cas=0, login=None)

    def no_git(*a, **k):
        raise FileNotFoundError("git")

    monkeypatch.setattr(doctor.subprocess, "run", no_git)
    assert doctor.main(_kit(tmp_path), Wiki(), TODAY) == 1
    block = _block(capsys.readouterr().out)
    assert "Bot login saved: no" in block and "certificates FIX" in block
    assert "Kit commit: unknown (git is not installed)" in block


RESTORE = "git restore canon style templates project-pack/knowledge VERSION.json"


def test_refreshed_files_are_a_note_with_the_restore_command_not_a_failure(
    tmp_path, monkeypatch, capsys
):
    # refresh_canon.py rewrites files that git pull also updates, so the two clash. The README
    # offers the refresh, so doctor must not fail after it (Eddy: "Note, not FIX").
    _setup(monkeypatch)
    monkeypatch.setattr(
        doctor,
        "refreshed_files",
        lambda kit: ["canon/a.md", "canon/b.md", "style/c.md", "templates/d.md"],
        raising=False,
    )
    assert doctor.main(_kit(tmp_path), Wiki(), TODAY) == 0
    out = capsys.readouterr().out
    assert (
        f"OK  refreshed files: canon/a.md and 3 more refreshed locally; before git pull, run: {RESTORE}"
        in out
    )
    assert "FIX refreshed files" not in out
    assert "refreshed files OK" in _block(out)


def _git(path, *args):
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.email=a@b.c", "-c", "user.name=t", *args],
        check=True,
        capture_output=True,
    )


def test_refreshed_files_lists_exactly_the_modified_tracked_files_of_the_refreshed_folders(
    tmp_path,
):
    for rel in ("canon/a.md", "style/b.md", "notes/mine.md", "tools/x.py"):
        (tmp_path / rel).parent.mkdir(exist_ok=True)
        (tmp_path / rel).write_text("old", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "kit")
    assert doctor.refreshed_files(tmp_path) == []
    for rel in ("canon/a.md", "notes/mine.md", "tools/x.py"):
        (tmp_path / rel).write_text("new", encoding="utf-8")
    assert doctor.refreshed_files(tmp_path) == ["canon/a.md"]  # not the member's notes or tools


def test_a_folder_that_is_not_a_clone_has_no_refresh_clash(tmp_path):
    assert doctor.refreshed_files(tmp_path) == []
