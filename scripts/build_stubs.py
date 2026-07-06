#!/usr/bin/env python3
"""Cross-compile the Go runtime stub for every supported platform.

Requires a Go toolchain (only for axe development/CI; never for axe users).

    python scripts/build_stubs.py [--current-only]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from axe.platforms import SUPPORTED_PLATFORMS, current_platform, stub_filename  # noqa: E402

STUBS_DIR = REPO / "src" / "axe" / "stubs"


def build_stub(goos: str, goarch: str) -> Path:
    out = STUBS_DIR / stub_filename(goos, goarch)
    env = os.environ | {"GOOS": goos, "GOARCH": goarch, "CGO_ENABLED": "0"}
    subprocess.run(
        ["go", "build", "-trimpath", "-ldflags", "-s -w", "-o", str(out), "."],
        cwd=REPO / "runtime",
        env=env,
        check=True,
    )
    print(f"built {out.relative_to(REPO)} ({out.stat().st_size // 1024} KiB)")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-only", action="store_true", help="build only the current platform's stub"
    )
    args = parser.parse_args()

    if not shutil.which("go"):
        print("error: Go toolchain not found (needed only to develop axe itself)", file=sys.stderr)
        return 1

    STUBS_DIR.mkdir(parents=True, exist_ok=True)
    targets = [current_platform()] if args.current_only else SUPPORTED_PLATFORMS
    for goos, goarch in targets:
        build_stub(goos, goarch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
