"""Supported target platforms and host detection."""

from __future__ import annotations

import platform
import sys

# (goos, goarch) pairs; the platform string is "os/arch".
SUPPORTED_PLATFORMS: list[tuple[str, str]] = [
    ("linux", "amd64"),
    ("linux", "arm64"),
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("windows", "amd64"),
]


def platform_strings() -> list[str]:
    return [f"{goos}/{goarch}" for goos, goarch in SUPPORTED_PLATFORMS]


def parse_platform(value: str) -> tuple[str, str]:
    try:
        goos, goarch = value.split("/")
    except ValueError:
        raise ValueError(
            f"invalid platform {value!r}; expected <os>/<arch>, one of: "
            + ", ".join(platform_strings())
        ) from None
    if (goos, goarch) not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"unsupported platform {value!r}; supported: " + ", ".join(platform_strings())
        )
    return goos, goarch


def current_platform() -> tuple[str, str]:
    if sys.platform == "darwin":
        goos = "darwin"
    elif sys.platform.startswith("linux"):
        goos = "linux"
    elif sys.platform in ("win32", "cygwin"):
        goos = "windows"
    else:
        raise ValueError(f"unsupported host OS: {sys.platform}")

    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        goarch = "arm64"
    elif machine in ("x86_64", "amd64"):
        goarch = "amd64"
    else:
        raise ValueError(f"unsupported host architecture: {machine}")
    return goos, goarch


# Rust-style target triples used by uv releases, python-build-standalone
# artifacts, and uv's --python-platform flag.
TARGET_TRIPLES: dict[tuple[str, str], str] = {
    ("linux", "amd64"): "x86_64-unknown-linux-gnu",
    ("linux", "arm64"): "aarch64-unknown-linux-gnu",
    ("darwin", "amd64"): "x86_64-apple-darwin",
    ("darwin", "arm64"): "aarch64-apple-darwin",
    ("windows", "amd64"): "x86_64-pc-windows-msvc",
}


def target_triple(goos: str, goarch: str) -> str:
    return TARGET_TRIPLES[(goos, goarch)]


def pip_platform_tags(goos: str, goarch: str) -> list[str]:
    """Wheel platform tags `pip download` should accept for a target.

    pip does not expand e.g. manylinux_2_28 to older glibc tags when
    --platform is given, so enumerate the range wheels actually publish.
    """
    arch = {"amd64": "x86_64", "arm64": "aarch64"}[goarch]
    if goos == "linux":
        tags = [f"manylinux_2_{minor}_{arch}" for minor in range(40, 4, -1)]
        tags += [f"manylinux2014_{arch}", f"manylinux2010_{arch}", f"manylinux1_{arch}"]
        tags.append(f"linux_{arch}")
        return tags
    if goos == "darwin":
        mac_arch = "arm64" if goarch == "arm64" else "x86_64"
        tags = []
        for major in range(26, 10, -1):
            tags += [f"macosx_{major}_0_{mac_arch}", f"macosx_{major}_0_universal2"]
        if mac_arch == "x86_64":
            for minor in range(15, 3, -1):
                tags += [f"macosx_10_{minor}_x86_64", f"macosx_10_{minor}_universal2"]
        else:
            tags += [f"macosx_10_{minor}_universal2" for minor in range(15, 3, -1)]
        return tags
    return ["win_amd64"]


def stub_filename(goos: str, goarch: str) -> str:
    suffix = ".exe" if goos == "windows" else ""
    return f"axe-runtime-{goos}-{goarch}{suffix}"


def binary_filename(name: str, version: str, goos: str, goarch: str) -> str:
    suffix = ".exe" if goos == "windows" else ""
    return f"{name}-{version}-{goos}-{goarch}{suffix}"
