"""Where a member's own bot password lives: the operating system's credential store, never a file
of the kit. On Windows that is Credential Manager and on a Mac the login keychain, neither needing
an install; elsewhere it is the keyring package (`pip install keyring`, the Secret Service on
Linux). The variables ICERIA_BOT_USER and ICERIA_BOT_PASS, when both are set, win over the store."""

import os
import subprocess
import sys

TARGET = "iceria-contributor-kit"  # the store entry's name
ENV_USER, ENV_PASS = "ICERIA_BOT_USER", "ICERIA_BOT_PASS"


class NoStore(Exception):
    """This machine has no credential store the kit can use."""


class _WindowsStore:
    """Credential Manager through advapi32, as a generic credential named TARGET."""

    name = "Windows Credential Manager"

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class FILETIME(ctypes.Structure):
            _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        self.ctypes, self.CREDENTIAL = ctypes, CREDENTIAL
        self.api = ctypes.WinDLL("advapi32", use_last_error=True)
        self.api.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(CREDENTIAL)),
        ]
        self.api.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
        self.api.CredFree.argtypes = [ctypes.c_void_p]

    def _read(self, take):
        ctypes = self.ctypes
        ptr = ctypes.POINTER(self.CREDENTIAL)()
        if not self.api.CredReadW(TARGET, 1, 0, ctypes.byref(ptr)):  # 1 = CRED_TYPE_GENERIC
            code = ctypes.get_last_error()
            if code == 1168:  # ERROR_NOT_FOUND
                return None
            raise NoStore(
                f"Windows Credential Manager could not be read (error {code}); try again, "
                f"or set {ENV_USER} and {ENV_PASS} in your shell"
            )
        try:
            return take(ptr.contents)
        finally:
            self.api.CredFree(ptr)

    def read(self) -> tuple[str, str] | None:
        def both(cred):
            blob = self.ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
            return cred.UserName, blob.decode("utf-16-le")

        return self._read(both)

    def who(self) -> str | None:
        return self._read(lambda cred: cred.UserName)

    def write(self, user: str, password: str):
        ctypes = self.ctypes
        blob = password.encode("utf-16-le")
        buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        cred = self.CREDENTIAL(
            Type=1,  # CRED_TYPE_GENERIC
            TargetName=TARGET,
            CredentialBlobSize=len(blob),
            CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)),
            Persist=2,  # CRED_PERSIST_LOCAL_MACHINE: this user, this machine
            UserName=user,
        )
        if not self.api.CredWriteW(ctypes.byref(cred), 0):
            raise NoStore(
                f"Windows Credential Manager could not save the login (error "
                f"{ctypes.get_last_error()}); try again, or set {ENV_USER} and {ENV_PASS} in your shell"
            )


class _MacStore:
    """The login keychain through /usr/bin/security, which every Mac has. The entries are the two
    the keyring package makes (service TARGET, accounts "user" and "password"), though the
    keychain may ask before one program reads an entry another program wrote."""

    name = "the macOS keychain"
    SECURITY = "/usr/bin/security"

    def _find(self, account: str) -> str | None:
        out = subprocess.run(
            [self.SECURITY, "find-generic-password", "-s", TARGET, "-a", account, "-w"],
            capture_output=True,
            text=True,
        )
        if out.returncode == 0:
            return out.stdout.rstrip("\n")
        # 44 is errSecItemNotFound; any other code is a locked or denied keychain.
        if out.returncode == 44:
            return None
        raise NoStore(
            f"the macOS keychain could not be read (security exit {out.returncode}: "
            f"{out.stderr.strip()}); unlock the login keychain in Keychain Access and try again, "
            f"or set {ENV_USER} and {ENV_PASS} in your shell"
        )

    def read(self) -> tuple[str, str] | None:
        user = self._find("user")
        password = self._find("password") if user else None
        return (user, password) if password else None

    def who(self) -> str | None:
        return self._find("user")

    def write(self, user: str, password: str):
        # `security -i` reads its commands from stdin, so the password never shows in the process
        # list. Inside its double quotes a quote or backslash would end or bend the value, and a
        # value that is not plain ASCII reads back as hex; a bot password is letters and digits.
        for label, value in (("login name", user), ("password", password)):
            if not value.isascii() or not value.isprintable() or set(value) & {'"', "\\"}:
                raise NoStore(
                    f"the macOS keychain here can only keep a {label} of plain letters, digits "
                    f'and symbols other than " and \\; set {ENV_USER} and {ENV_PASS} in your '
                    "shell instead"
                )
        lines = "".join(
            f'add-generic-password -U -s "{TARGET}" -a "{account}" -w "{value}"\n'
            for account, value in (("user", user), ("password", password))
        )
        subprocess.run([self.SECURITY, "-i"], input=lines, capture_output=True, text=True)
        if self.read() != (user, password):  # security -i exits 0 even when a command fails
            raise NoStore(
                "the macOS keychain did not keep the password. The login keychain may be locked, "
                f'or an older "{TARGET}" entry may belong to another program: unlock the keychain, '
                "or delete that entry in Keychain Access, and try again; or set "
                f"{ENV_USER} and {ENV_PASS} in your shell"
            )


class _KeyringStore:
    """The keyring package; the user name is kept as its own entry so one lookup finds both."""

    name = "the system keyring"

    def __init__(self):
        try:
            import keyring
        except ImportError as e:
            raise NoStore(
                "no credential store: install one with `pip install keyring`, or set "
                f"{ENV_USER} and {ENV_PASS} in your shell"
            ) from e
        self.keyring = keyring

    def _call(self, method: str, *args):
        # keyring imports fine on a machine with no backend (a Linux box with no desktop) and
        # raises only when used.
        try:
            return getattr(self.keyring, method)(TARGET, *args)
        except self.keyring.errors.KeyringError as e:
            raise NoStore(
                f"the system keyring is not usable here ({e}); set {ENV_USER} and {ENV_PASS} "
                "in your shell instead"
            ) from e

    def read(self) -> tuple[str, str] | None:
        user = self._call("get_password", "user")
        password = self._call("get_password", "password") if user else None
        return (user, password) if password else None

    def who(self) -> str | None:
        return self._call("get_password", "user")

    def write(self, user: str, password: str):
        self._call("set_password", "user", user)
        self._call("set_password", "password", password)


def store():
    """The credential store for this machine. Raises NoStore when there is none."""
    if sys.platform == "win32":
        return _WindowsStore()
    if sys.platform == "darwin" and os.path.exists(_MacStore.SECURITY):
        return _MacStore()
    return _KeyringStore()


def get() -> tuple[tuple[str, str], str] | None:
    """((user, password), where it came from), or None when no bot password is set up."""
    user, password = os.environ.get(ENV_USER), os.environ.get(ENV_PASS)
    if user and password:
        return (user, password), f"the {ENV_USER} and {ENV_PASS} variables"
    try:
        s = store()
        found = s.read()
    except NoStore:
        return None
    return (found, s.name) if found else None


def who() -> tuple[str, str] | None:
    """(login name, where it is kept), or None when none is saved. Never reads the password, so
    a Mac keychain asks no question; raises NoStore when the machine has no store."""
    user = os.environ.get(ENV_USER)
    if user and os.environ.get(ENV_PASS):
        return user, f"the {ENV_USER} and {ENV_PASS} variables"
    s = store()
    name = s.who()
    return (name, s.name) if name else None
