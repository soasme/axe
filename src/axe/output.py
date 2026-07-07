"""Build output control: -q silences progress, -v streams tool output.

Progress goes to stderr so stdout stays clean for scripting; result lines
(the built binaries) go to stdout.
"""

from __future__ import annotations

import sys

QUIET, NORMAL, VERBOSE = range(3)

_level = NORMAL


def set_level(level: int) -> None:
    global _level
    _level = level


def verbose() -> bool:
    return _level >= VERBOSE


def progress(message: str) -> None:
    if _level > QUIET:
        print(message, file=sys.stderr, flush=True)


def result(message: str) -> None:
    if _level > QUIET:
        print(message, flush=True)
