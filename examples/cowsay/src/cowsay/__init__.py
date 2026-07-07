"""A tiny cowsay used to demo and end-to-end test axe."""

import os
import sys

import six


def say(message: str) -> str:
    top = " " + "_" * (len(message) + 2)
    bottom = " " + "-" * (len(message) + 2)
    cow = r"""
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||"""
    return f"{top}\n< {message} >\n{bottom}{cow}"


def main() -> int:
    message = six.ensure_str(" ".join(sys.argv[1:]) or "moo")
    print(say(message))
    if os.environ.get("AXE") == "1":
        print("(running from an axe binary)", file=sys.stderr)
    return 0
