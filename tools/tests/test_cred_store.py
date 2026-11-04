"""Where the bot password is looked up: the variables first, then the machine's store."""

import sys
import types

import cred_store
import pytest

PW = "p" * 8  # a stand-in; never the 32-character shape the leak gate looks for


class FakeStore:
    name = "the fake store"

    def __init__(self, found=None):
        self.found = found

    def read(self):
        return self.found

    def who(self):
        return self.found and self.found[0]

    def write(self, user, password):
        self.found = (user, password)


@pytest.fixture(autouse=True)
def no_env(monkeypatch):
    monkeypatch.delenv(cred_store.ENV_USER, raising=False)
    monkeypatch.delenv(cred_store.ENV_PASS, raising=False)


def test_the_variables_win_over_the_store(monkeypatch):
    monkeypatch.setenv(cred_store.ENV_USER, "Ana@kit")
    monkeypatch.setenv(cred_store.ENV_PASS, PW)
    monkeypatch.setattr(cred_store, "store", lambda: FakeStore(("Other@kit", "x" * 8)))
    creds, where = cred_store.get()
    assert creds == ("Ana@kit", PW)
    assert "ICERIA_BOT_USER" in where


def test_one_variable_alone_falls_through_to_the_store(monkeypatch):
    monkeypatch.setenv(cred_store.ENV_USER, "Ana@kit")
    monkeypatch.setattr(cred_store, "store", lambda: FakeStore(("Ana@kit", PW)))
    assert cred_store.get() == (("Ana@kit", PW), "the fake store")


def test_nothing_set_up_is_none(monkeypatch):
    monkeypatch.setattr(cred_store, "store", lambda: FakeStore())
    assert cred_store.get() is None


def test_no_store_on_the_machine_is_none(monkeypatch):
    def none():
        raise cred_store.NoStore("none here")

    monkeypatch.setattr(cred_store, "store", none)
    assert cred_store.get() is None


def test_the_keyring_store_keeps_user_and_password(monkeypatch):
    kept = {}
    fake = types.SimpleNamespace(
        get_password=lambda service, key: kept.get((service, key)),
        set_password=lambda service, key, value: kept.__setitem__((service, key), value),
    )
    monkeypatch.setitem(sys.modules, "keyring", fake)
    s = cred_store._KeyringStore()
    assert s.read() is None
    s.write("Ana@kit", PW)
    assert s.read() == ("Ana@kit", PW)
    assert set(kept) == {(cred_store.TARGET, "user"), (cred_store.TARGET, "password")}


def test_a_keyring_with_no_backend_is_no_store(monkeypatch):
    # A Linux box with no desktop: keyring imports, then raises NoKeyringError on every call.
    class NoKeyringError(RuntimeError):
        pass

    def refuse(*args):
        raise NoKeyringError("No recommended backend was available.")

    errors = types.SimpleNamespace(KeyringError=RuntimeError, NoKeyringError=NoKeyringError)
    fake = types.SimpleNamespace(get_password=refuse, set_password=refuse, errors=errors)
    monkeypatch.setitem(sys.modules, "keyring", fake)
    monkeypatch.setattr(cred_store, "store", cred_store._KeyringStore)
    assert cred_store.get() is None
    with pytest.raises(cred_store.NoStore, match=cred_store.ENV_PASS):
        cred_store._KeyringStore().write("Ana@kit", PW)


@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
def test_the_windows_store_keeps_user_and_password(monkeypatch):
    import ctypes
    import uuid

    target = f"iceria-kit-test-{uuid.uuid4().hex[:8]}"  # never the member's real entry
    monkeypatch.setattr(cred_store, "TARGET", target)
    s = cred_store._WindowsStore()
    try:
        assert s.read() is None
        s.write("Ana@kit", PW)
        assert s.read() == ("Ana@kit", PW)
        assert s.who() == "Ana@kit"
    finally:
        ctypes.WinDLL("advapi32").CredDeleteW(target, 1, 0)  # 1 = CRED_TYPE_GENERIC


def test_no_keyring_package_says_how_to_get_one(monkeypatch):
    monkeypatch.setitem(sys.modules, "keyring", None)  # makes `import keyring` fail
    with pytest.raises(cred_store.NoStore, match="pip install keyring"):
        cred_store._KeyringStore()


class FakeSecurity:
    """The /usr/bin/security boundary: a keychain held in a dict, and every argv it was run with."""

    def __init__(self, sticks=True):
        self.kept, self.argvs, self.sticks = {}, [], sticks

    def run(self, argv, input=None, **kw):
        import shlex
        import subprocess

        self.argvs.append(argv)
        if argv[1] == "find-generic-password":
            found = self.kept.get((argv[argv.index("-s") + 1], argv[argv.index("-a") + 1]))
            if found is None:
                return subprocess.CompletedProcess(argv, 44, "", "could not be found")
            return subprocess.CompletedProcess(argv, 0, found + "\n", "")
        assert argv[1:] == ["-i"]
        for line in input.splitlines():
            words = shlex.split(line)
            assert words[:2] == ["add-generic-password", "-U"]
            s, a, w = (words[words.index(flag) + 1] for flag in ("-s", "-a", "-w"))
            if self.sticks:
                self.kept[(s, a)] = w
        return subprocess.CompletedProcess(argv, 0, "", "")


def test_the_mac_store_keeps_user_and_password_off_the_command_line(monkeypatch):
    fake = FakeSecurity()
    monkeypatch.setattr(cred_store.subprocess, "run", fake.run)
    s = cred_store._MacStore()
    assert s.read() is None
    s.write("Ana@kit", PW)
    assert s.read() == ("Ana@kit", PW)
    # The same two entries the keyring package would make, so either one reads the other's.
    assert set(fake.kept) == {(cred_store.TARGET, "user"), (cred_store.TARGET, "password")}
    assert not any(PW in word for argv in fake.argvs for word in argv)


@pytest.mark.parametrize("bad", ['pa"ss', "pa\\ss", "pa\nss", "pässword"])
def test_the_mac_store_refuses_what_security_cannot_quote(monkeypatch, bad):
    fake = FakeSecurity()
    monkeypatch.setattr(cred_store.subprocess, "run", fake.run)
    with pytest.raises(cred_store.NoStore, match=cred_store.ENV_PASS):
        cred_store._MacStore().write("Ana@kit", bad)
    assert fake.kept == {}


def test_the_mac_store_names_the_value_it_refused(monkeypatch):
    monkeypatch.setattr(cred_store.subprocess, "run", FakeSecurity().run)
    with pytest.raises(cred_store.NoStore, match="login name"):
        cred_store._MacStore().write("Zoë@kit", PW)


def test_a_mac_write_that_does_not_stick_is_no_store(monkeypatch):
    # A locked or missing login keychain: security -i reports nothing, so the store reads it back.
    monkeypatch.setattr(cred_store.subprocess, "run", FakeSecurity(sticks=False).run)
    with pytest.raises(cred_store.NoStore, match="keychain"):
        cred_store._MacStore().write("Ana@kit", PW)


def test_each_platform_gets_its_own_store(monkeypatch, tmp_path):
    security = tmp_path / "security"
    security.touch()
    monkeypatch.setattr(cred_store.sys, "platform", "darwin")
    monkeypatch.setattr(cred_store._MacStore, "SECURITY", str(security))
    assert isinstance(cred_store.store(), cred_store._MacStore)
    monkeypatch.setitem(sys.modules, "keyring", types.SimpleNamespace())
    security.unlink()  # a Mac without the security tool falls back to keyring
    assert isinstance(cred_store.store(), cred_store._KeyringStore)
    monkeypatch.setattr(cred_store.sys, "platform", "linux")
    assert isinstance(cred_store.store(), cred_store._KeyringStore)


@pytest.mark.skipif(sys.platform != "darwin", reason="the login keychain is macOS only")
def test_the_real_mac_keychain_keeps_user_and_password(monkeypatch):
    import subprocess
    import uuid

    target = f"iceria-kit-test-{uuid.uuid4().hex[:8]}"  # never the member's real entry
    monkeypatch.setattr(cred_store, "TARGET", target)
    s = cred_store._MacStore()
    try:
        assert s.read() is None
        s.write("Ana@kit", PW)
        assert s.read() == ("Ana@kit", PW)
    finally:
        for account in ("user", "password"):
            subprocess.run(
                ["/usr/bin/security", "delete-generic-password", "-s", target, "-a", account],
                capture_output=True,
            )


def test_who_names_the_saved_login_without_reading_the_password(monkeypatch):
    asked = []
    kept = {(cred_store.TARGET, "user"): "Ana@kit", (cred_store.TARGET, "password"): PW}
    fake = types.SimpleNamespace(get_password=lambda s, key: asked.append(key) or kept[(s, key)])
    monkeypatch.setitem(sys.modules, "keyring", fake)
    monkeypatch.setattr(cred_store, "store", cred_store._KeyringStore)
    assert cred_store.who() == ("Ana@kit", "the system keyring")
    assert asked == ["user"]


def test_who_on_a_mac_never_asks_the_keychain_for_the_password(monkeypatch):
    fake = FakeSecurity()
    fake.kept = {(cred_store.TARGET, "user"): "Ana@kit", (cred_store.TARGET, "password"): PW}
    monkeypatch.setattr(cred_store.subprocess, "run", fake.run)
    assert cred_store._MacStore().who() == "Ana@kit"
    assert all("password" not in argv for argv in fake.argvs)


def test_who_prefers_the_variables_and_is_none_with_nothing_saved(monkeypatch):
    monkeypatch.setattr(cred_store, "store", lambda: FakeStore())
    assert cred_store.who() is None
    monkeypatch.setenv(cred_store.ENV_USER, "Ana@kit")
    monkeypatch.setenv(cred_store.ENV_PASS, PW)
    assert cred_store.who() == ("Ana@kit", "the ICERIA_BOT_USER and ICERIA_BOT_PASS variables")


def test_who_with_no_store_on_the_machine_says_why(monkeypatch):
    def none():
        raise cred_store.NoStore("no credential store: install one")

    monkeypatch.setattr(cred_store, "store", none)
    with pytest.raises(cred_store.NoStore, match="install one"):
        cred_store.who()


def test_a_locked_mac_keychain_is_a_store_error_not_a_missing_login(monkeypatch):
    # Only exit 44 means "no such entry"; a locked or denied keychain (51 here) must not read as
    # "none saved", or the tools quietly fall back to guest reads and doctor says all is well.
    fake = FakeSecurity()
    fake.kept[(cred_store.TARGET, "user")] = "Ana@kit"
    fake.kept[(cred_store.TARGET, "password")] = PW

    def locked(argv, input=None, **kw):
        import subprocess

        if argv[1] == "find-generic-password":
            return subprocess.CompletedProcess(argv, 51, "", "User interaction is not allowed.")
        return fake.run(argv, input=input, **kw)

    monkeypatch.setattr(cred_store.subprocess, "run", locked)
    with pytest.raises(cred_store.NoStore, match="exit 51") as e:
        cred_store._MacStore().read()
    assert PW not in str(e.value) and cred_store.ENV_PASS in str(e.value)


@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
def test_an_unreadable_windows_store_is_a_store_error_not_a_traceback(monkeypatch):
    # Only 1168 (ERROR_NOT_FOUND) means "no such entry"; any other failure is a store doctor
    # must report as a FIX line, so it is NoStore like the Mac keychain's, never a bare OSError.
    import ctypes

    s = cred_store._WindowsStore()
    monkeypatch.setattr(s, "api", types.SimpleNamespace(CredReadW=lambda *a: 0))
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5)  # ERROR_ACCESS_DENIED
    with pytest.raises(cred_store.NoStore, match="error 5") as e:
        s.who()
    assert cred_store.ENV_PASS in str(e.value)


def test_a_windows_write_that_fails_is_a_store_error_with_the_fix(capsys):
    """A stub of advapi32, so this proves the message path and not the real CredWriteW call.

    Credential Manager's refusal (a locked profile, a policy) used to escape as a bare OSError and
    setup_bot.py printed a traceback."""
    import ctypes

    store = cred_store._WindowsStore.__new__(cred_store._WindowsStore)
    store.ctypes = types.SimpleNamespace(
        c_ubyte=ctypes.c_ubyte,
        cast=lambda buf, kind: buf,
        POINTER=ctypes.POINTER,
        byref=lambda cred: cred,
        get_last_error=lambda: 1312,
    )
    store.CREDENTIAL = lambda **fields: types.SimpleNamespace(**fields)
    store.api = types.SimpleNamespace(CredWriteW=lambda cred, flags: 0)
    with pytest.raises(cred_store.NoStore) as err:
        store.write("Ana@kit", PW)
    assert "error 1312" in str(err.value)
    assert cred_store.ENV_USER in str(err.value) and cred_store.ENV_PASS in str(err.value)
    assert PW not in str(err.value)
