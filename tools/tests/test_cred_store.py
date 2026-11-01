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
