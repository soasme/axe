"""Resolve and download the app's dependency wheels for a target platform."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .fetch import cache_dir
from .platforms import pip_platform_tags, target_triple


class ResolveError(Exception):
    pass


def compile_requirements(uv: str, project_dir: Path, goos: str, goarch: str, python: str) -> str:
    """Pin the full dependency tree for a target platform (markers evaluated
    for that platform, not the build host)."""
    result = subprocess.run(
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
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ResolveError(
            f"dependency resolution for {goos}/{goarch} failed:\n{result.stderr.strip()}"
        )
    return result.stdout


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
        "--quiet",
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    Path(reqs_path).unlink(missing_ok=True)
    if result.returncode != 0:
        raise ResolveError(
            f"downloading dependency wheels for {goos}/{goarch} failed "
            f"(a dependency may not publish wheels for that platform):\n"
            f"{result.stderr.strip()}"
        )
    return sorted(dest.glob("*.whl"))
