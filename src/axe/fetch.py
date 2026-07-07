"""Build-time downloads of the artifacts embedded into binaries.

Everything is fetched on the *build* machine, checksum-verified, and cached,
so end users never touch the network. Cache layout:

    <cache>/artifacts/uv/<uv release artifact>
    <cache>/artifacts/python/<pbs artifact>
    <cache>/artifacts/python/SHA256SUMS-<release>
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .platforms import target_triple

UV_RELEASES = "https://github.com/astral-sh/uv/releases/download"
PBS_RELEASES = "https://github.com/astral-sh/python-build-standalone/releases/download"


class FetchError(Exception):
    pass


def cache_dir() -> Path:
    """Matches the Go runtime's cache location so `self cache` finds it."""
    if env := os.environ.get("AXE_CACHE_DIR"):
        return Path(env)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "axe"
    if sys.platform in ("win32", "cygwin"):
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "axe" / "cache"
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "axe"


def fetch_url(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=600) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise FetchError(f"failed to fetch {url}: {e}") from None


def _fetch_verified(url: str, dest: Path, sha256: str | None) -> Path:
    if dest.is_file():
        return dest
    print(f"fetching {url.rsplit('/', 1)[-1]}...")
    data = fetch_url(url)
    if sha256 and hashlib.sha256(data).hexdigest() != sha256:
        raise FetchError(f"checksum mismatch for {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + f".tmp-{os.getpid()}")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


def uv_artifact_name(uv_version: str, goos: str, goarch: str) -> str:
    ext = ".zip" if goos == "windows" else ".tar.gz"
    return f"uv-{target_triple(goos, goarch)}{ext}"


def fetch_uv(uv_version: str, goos: str, goarch: str) -> Path:
    name = uv_artifact_name(uv_version, goos, goarch)
    url = f"{UV_RELEASES}/{uv_version}/{name}"
    sha256 = fetch_url(url + ".sha256").split()[0].decode()
    return _fetch_verified(url, cache_dir() / "artifacts" / "uv" / uv_version / name, sha256)


def _pbs_checksums(release: str) -> dict[str, str]:
    """artifact filename -> sha256 for a python-build-standalone release."""
    path = cache_dir() / "artifacts" / "python" / f"SHA256SUMS-{release}"
    _fetch_verified(f"{PBS_RELEASES}/{release}/SHA256SUMS", path, None)
    sums = {}
    for line in path.read_text().splitlines():
        if fields := line.split():
            sums[fields[1]] = fields[0]
    return sums


def resolve_python(python_version: str, release: str, goos: str, goarch: str) -> tuple[str, str]:
    """Pick the PBS artifact for a requested version ("3.12" or "3.12.3").

    Returns (full python version, artifact filename). Prefers the stripped
    variant; a "3.X" request resolves to the newest 3.X.* in the release.
    """
    sums = _pbs_checksums(release)
    triple = target_triple(goos, goarch)
    pattern = re.compile(
        rf"cpython-({re.escape(python_version)}(?:\.\d+)*)\+{release}-{triple}"
        rf"-install_only(_stripped)?\.tar\.gz$"
    )
    candidates: dict[str, dict[bool, str]] = {}
    for name in sums:
        if m := pattern.fullmatch(name):
            candidates.setdefault(m.group(1), {})[bool(m.group(2))] = name
    if not candidates:
        raise FetchError(
            f"no CPython {python_version} build for {goos}/{goarch} in "
            f"python-build-standalone release {release}"
        )
    full = max(candidates, key=lambda v: [int(p) for p in v.split(".")])
    variants = candidates[full]
    return full, variants.get(True) or variants[False]


def fetch_python(artifact: str, release: str) -> Path:
    sha256 = _pbs_checksums(release)[artifact]
    url = f"{PBS_RELEASES}/{release}/{artifact}"
    return _fetch_verified(
        url, cache_dir() / "artifacts" / "python" / release / artifact, sha256
    )
