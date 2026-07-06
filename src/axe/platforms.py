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


def stub_filename(goos: str, goarch: str) -> str:
    suffix = ".exe" if goos == "windows" else ""
    return f"axe-runtime-{goos}-{goarch}{suffix}"


def binary_filename(name: str, version: str, goos: str, goarch: str) -> str:
    suffix = ".exe" if goos == "windows" else ""
    return f"{name}-{version}-{goos}-{goarch}{suffix}"
