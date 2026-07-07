"""The `axe` command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, output
from .build import BuildError, build
from .config import ConfigError
from .fetch import FetchError
from .platforms import platform_strings
from .proc import ToolError
from .wheel import WheelError


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="axe",
        description="Ship Python apps as self-bootstrapping single-file binaries.",
    )
    parser.add_argument("--version", action="version", version=f"axe {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build_cmd = sub.add_parser("build", help="build binaries for one or more platforms")
    build_cmd.add_argument(
        "project", nargs="?", default=".", help="project directory (default: current)"
    )
    build_cmd.add_argument(
        "-o", "--output", help="output directory (default: <project>/dist/bin)"
    )
    build_cmd.add_argument(
        "-p",
        "--platform",
        action="append",
        metavar="OS/ARCH",
        help="target platform, repeatable (default: current platform)",
    )
    build_cmd.add_argument(
        "--all-platforms", action="store_true", help="build for every supported platform"
    )
    verbosity = build_cmd.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-q", "--quiet", action="store_true", help="print nothing but errors"
    )
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="stream the output of underlying tools (uv, pip)",
    )

    sub.add_parser("platforms", help="list supported target platforms")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)

    if args.command == "platforms":
        print("\n".join(platform_strings()))
        return 0

    if args.quiet:
        output.set_level(output.QUIET)
    elif args.verbose:
        output.set_level(output.VERBOSE)

    try:
        build(
            Path(args.project),
            output_dir=Path(args.output) if args.output else None,
            platforms=args.platform,
            all_platforms=args.all_platforms,
        )
    except (BuildError, ConfigError, FetchError, ToolError, WheelError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
