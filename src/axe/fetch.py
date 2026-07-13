"""Build-time downloads of the artifacts embedded into binaries.

Everything is fetched on the *build* machine, checksum-verified, and cached,
so end users never touch the network. Cache layout:

    <cache>/artifacts/uv/<uv release artifact>
    <cache>/artifacts/python/<pbs artifact>
    <cache>/artifacts/python/SHA256SUMS-<release>
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import output
from .platforms import target_triple

# Socket inactivity timeout: long enough for slow links, short enough that a
# black-holing proxy surfaces as an error rather than an apparent hang.
FETCH_TIMEOUT = 60

# Default release download locations; overridable per project via
# [tool.axe] uv-releases-url / python-build-standalone-releases-url
# (mirrors for network-isolated environments).
UV_RELEASES = "https://github.com/astral-sh/uv/releases/download"
PBS_RELEASES = "https://github.com/astral-sh/python-build-standalone/releases/download"


class FetchError(Exception):
    pass


def _auth_header(env_prefix: str) -> str | None:
    """HTTP Basic credentials for a release mirror, from <PREFIX>_USERNAME /
    <PREFIX>_PASSWORD. Env vars rather than pyproject.toml keys so secrets
    never end up committed."""
    username = os.environ.get(f"{env_prefix}_USERNAME", "")
    password = os.environ.get(f"{env_prefix}_PASSWORD", "")
    if not username and not password:
        return None
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


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


def fetch_url(url: str, auth: str | None = None) -> bytes:
    if output.verbose():
        output.progress(f"GET {url}")
    request = urllib.request.Request(url)
    if auth:
        request.add_header("Authorization", auth)
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT) as resp:
            return resp.read()
    except TimeoutError:
        raise FetchError(
            f"timed out fetching {url} (no data for {FETCH_TIMEOUT}s) — "
            "check network/proxy connectivity to the release host"
        ) from None
    except urllib.error.URLError as e:
        raise FetchError(f"failed to fetch {url}: {e}") from None


def _fetch_verified(url: str, dest: Path, sha256: str | None, auth: str | None = None) -> Path:
    if dest.is_file():
        return dest
    output.progress(f"fetching {url.rsplit('/', 1)[-1]}...")
    data = fetch_url(url, auth)
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


def fetch_uv(uv_version: str, goos: str, goarch: str, releases_url: str = UV_RELEASES) -> Path:
    name = uv_artifact_name(uv_version, goos, goarch)
    url = f"{releases_url}/{uv_version}/{name}"
    auth = _auth_header("UV_RELEASES")
    sha256 = fetch_url(url + ".sha256", auth).split()[0].decode()
    return _fetch_verified(url, cache_dir() / "artifacts" / "uv" / uv_version / name, sha256, auth)


def _pbs_checksums(release: str, releases_url: str = PBS_RELEASES) -> dict[str, str]:
    """artifact filename -> sha256 for a python-build-standalone release."""
    path = cache_dir() / "artifacts" / "python" / f"SHA256SUMS-{release}"
    auth = _auth_header("PYTHON_BUILD_STANDALONE_RELEASES")
    _fetch_verified(f"{releases_url}/{release}/SHA256SUMS", path, None, auth)
    sums = {}
    for line in path.read_text().splitlines():
        if fields := line.split():
            sums[fields[1]] = fields[0]
    return sums


def resolve_python(
    python_version: str, release: str, goos: str, goarch: str, releases_url: str = PBS_RELEASES
) -> tuple[str, str]:
    """Pick the PBS artifact for a requested version ("3.12" or "3.12.3").

    Returns (full python version, artifact filename). Prefers the stripped
    variant; a "3.X" request resolves to the newest 3.X.* in the release.
    """
    sums = _pbs_checksums(release, releases_url)
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


def fetch_python(artifact: str, release: str, releases_url: str = PBS_RELEASES) -> Path:
    sha256 = _pbs_checksums(release, releases_url)[artifact]
    url = f"{releases_url}/{release}/{artifact}"
    auth = _auth_header("PYTHON_BUILD_STANDALONE_RELEASES")
    return _fetch_verified(
        url, cache_dir() / "artifacts" / "python" / release / artifact, sha256, auth
    )
