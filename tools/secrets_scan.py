"""Find a bot password sitting in a file of the kit. refresh_canon.py runs this first and stops on
a hit, and the stewards' export runs the same patterns over every file it ships.

    python tools/secrets_scan.py     exit 0 clean, 1 with each hit as "file:line: what"
"""

import os
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
PATTERNS = {
    # Special:BotPasswords hands out 32 lowercase letters and digits. A run of hex alone is an md5
    # or a dashless uuid; a real password is all hex less than once in 10^11.
    "bot password": re.compile(
        r"(?<![0-9a-z])(?![0-9a-f]{32}(?![0-9a-z]))[0-9a-z]{32}(?![0-9a-z])"
    ),
    # A value, not a placeholder such as <your bot password>, $VAR or %VAR%.
    "bot password variable": re.compile(r"ICERIA_BOT_PASS\s*=\s*[\"']?[^\s<$%{\"']{8,}"),
}


# Folders tools write and members never type into; a folder holding pyvenv.cfg is a virtualenv.
SKIPPED = frozenset({".git", "__pycache__", ".pytest_cache", "node_modules"})


def _files(root: Path) -> list[Path]:
    """Every file under root, tracked or not: a member's drafts and .env are untracked, and those
    are where a pasted password lands."""
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [
            d for d in dirs if d not in SKIPPED and not (Path(folder, d) / "pyvenv.cfg").exists()
        ]
        found += (Path(folder, f) for f in files)
    return sorted(found)


def scan(root: Path = KIT) -> list[str]:
    """Every hit as "file:line: what". The matched text is never shown: it may be the password."""
    hits = []
    for path in _files(root):
        if not path.is_file():
            continue
        found = {}
        for text in _texts(path.read_bytes()):
            for n, line in enumerate(text.splitlines(), 1):
                for what, rx in PATTERNS.items():
                    if rx.search(line):
                        found[f"{path.relative_to(root).as_posix()}:{n}: {what}"] = None
        hits += found
    return hits


def _texts(data: bytes) -> list[str]:
    """The file read every way it may hold text. A NUL marks UTF-16 (PowerShell's > writes it, with
    or without a byte-order mark), which as UTF-8 puts a NUL between every letter."""
    texts = [data.decode("utf-8", errors="replace")]
    if b"\0" in data:
        texts += [data.decode(e, errors="replace") for e in ("utf-16-le", "utf-16-be")]
    return texts


def main() -> int:
    hits = scan()
    for hit in hits:
        print(hit, file=sys.stderr)
    if hits:
        print(
            "A file of the kit holds what looks like a bot password. Remove it, and if it was "
            "real, revoke it at Special:BotPasswords and make a new one.",
            file=sys.stderr,
        )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
