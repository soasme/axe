"""Resolve and download the app's dependency wheels for a target platform."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .fetch import cache_dir
from .platforms import pip_platform_tags, target_triple
from .proc import NETWORK_HINT, run_tool

COMPILE_TIMEOUT = 300
DOWNLOAD_TIMEOUT = 900


def compile_requirements(uv: str, project_dir: Path, goos: str, goarch: str, python: str) -> str:
    """Pin the full dependency tree for a target platform (markers evaluated
    for that platform, not the build host)."""
    return run_tool(
        [
            uv,
            "pip",
            "compile",
            "pyproject.toml",
            "--python-platform",
            target_triple(goos, goarch),
            "--python-version",
            python,
            "--no-header",
            "--no-annotate",
            # NB: --quiet would also silence the -o - output itself.
            "-o",
            "-",
        ],
        what=f"dependency resolution for {goos}/{goarch}",
        timeout=COMPILE_TIMEOUT,
        cwd=project_dir,
        hint=NETWORK_HINT,
    )


def pinned_count(requirements: str) -> int:
    return sum(
        1
        for line in requirements.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "-"))
    )


def download_wheels(
    uv: str, requirements: str, goos: str, goarch: str, python: str, dest: Path
) -> list[Path]:
    """Download the pinned requirements as wheels built for the target.

    Uses `pip download` (run via uvx, so pip need not be installed anywhere)
    with an explicit tag set; sdists are rejected because they cannot be
    built for a foreign platform.
    """
    if not requirements.strip():
        return []
    dest.mkdir(parents=True, exist_ok=True)
    major, minor = python.split(".")[:2]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(requirements)
        reqs_path = f.name
    cmd = [
        uv,
        "tool",
        "run",
        "--from",
        "pip",
        "pip",
        "download",
        "--no-deps",  # the tree is already pinned by uv pip compile
        "--only-binary=:all:",
        "--dest",
        str(dest),
        "--cache-dir",
        str(cache_dir() / "pip"),
        "--implementation",
        "cp",
        "--python-version",
        f"{major}.{minor}",
        "--abi",
        f"cp{major}{minor}",
        "--abi",
        "abi3",
        "--abi",
        "none",
        "-r",
        reqs_path,
    ]
    for tag in pip_platform_tags(goos, goarch):
        cmd += ["--platform", tag]
    try:
        run_tool(
            cmd,
            what=f"downloading dependency wheels for {goos}/{goarch}",
            timeout=DOWNLOAD_TIMEOUT,
            hint=("A dependency may not publish wheels for that platform. " + NETWORK_HINT),
        )
    finally:
        Path(reqs_path).unlink(missing_ok=True)
    return sorted(dest.glob("*.whl"))
