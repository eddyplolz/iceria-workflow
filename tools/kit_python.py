"""Stops a kit tool on a Python older than 3.10, with the fix, before it fails on newer syntax.

Imported first by each tool a member runs. A Mac's built-in python3 is 3.9, so this is the error a
member meets when they have not installed Python from python.org yet.
"""

import sys

if sys.version_info < (3, 10):  # noqa: UP036  the point of the module
    sys.exit(
        f"The kit needs Python 3.10 or newer, and this is Python {sys.version.split()[0]}. "
        "Install the latest Python from https://www.python.org/downloads/ and run the command "
        "again (README.md, 'Set up your computer', step 1)."
    )
