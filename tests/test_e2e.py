"""End-to-end contract: `axe build` produces a fully offline binary.

Building needs the network (uv + CPython artifacts and dependency wheels are
fetched and cached on the build machine). Running must not: every binary is
executed with proxies pointed at a dead address and no AXE_UV escape hatch,
so any network attempt fails loudly.

Requires uv on PATH and the current platform's stub (scripts/build_stubs.py).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from axe.build import build, load_stub
from axe.platforms import current_platform

REPO = Path(__file__).resolve().parent.parent
COWSAY = REPO / "examples" / "cowsay"
DEAD_PROXY = "http://127.0.0.1:1"

try:
    load_stub(*current_platform())
    HAVE_STUB = True
except Exception:
    HAVE_STUB = False

pytestmark = [
    pytest.mark.skipif(not shutil.which("uv"), reason="uv not on PATH"),
    pytest.mark.skipif(
        not HAVE_STUB, reason="current platform stub missing; run scripts/build_stubs.py"
    ),
]


@pytest.fixture(scope="module")
def binary(tmp_path_factory) -> Path:
    outputs = build(COWSAY, output_dir=tmp_path_factory.mktemp("bin"))
    assert len(outputs) == 1
    return outputs[0]


@pytest.fixture(scope="module")
def offline_env(tmp_path_factory) -> dict[str, str]:
    """Isolated dirs + all network routes poisoned."""
    root = tmp_path_factory.mktemp("axe-home")
    env = os.environ.copy()
    env.pop("AXE_UV", None)
    env["AXE_DATA_DIR"] = str(root / "data")
    env["AXE_CACHE_DIR"] = str(root / "cache")
    env["HTTP_PROXY"] = env["HTTPS_PROXY"] = DEAD_PROXY
    env["http_proxy"] = env["https_proxy"] = DEAD_PROXY
    env.pop("NO_PROXY", None)
    env.pop("no_proxy", None)
    return env


def run(binary: Path, args: list[str], env: dict[str, str], timeout: int = 300):
    return subprocess.run(
        [str(binary), *args], env=env, capture_output=True, text=True, timeout=timeout
    )


def test_binary_lifecycle_offline(binary: Path, offline_env: dict[str, str]):
    stub_size = len(load_stub(*current_platform()))
    assert binary.stat().st_size > stub_size
    assert os.access(binary, os.X_OK)

    # First run bootstraps — uv, Python, and all wheels come from the
    # payload; the dead proxy proves no network is touched.
    result = run(binary, ["hello", "world"], offline_env)
    assert result.returncode == 0, result.stderr
    assert "< hello world >" in result.stdout
    assert "first run" in result.stderr
    # The app can detect it's running from an axe binary (AXE=1), and its
    # dependency (six) was importable, or the run would have crashed.
    assert "(running from an axe binary)" in result.stderr

    # The embedded uv was extracted into the shared cache.
    uv_cache = Path(offline_env["AXE_CACHE_DIR"]) / "uv"
    assert any(uv_cache.rglob("uv*")), "embedded uv not extracted to cache"

    # Second run takes the fast path: no bootstrap chatter.
    result = run(binary, ["again"], offline_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "< again >" in result.stdout
    assert "first run" not in result.stderr

    result = run(binary, ["self", "python-path"], offline_env, timeout=60)
    assert result.returncode == 0, result.stderr
    python_path = result.stdout.strip()
    assert python_path.startswith(offline_env["AXE_DATA_DIR"])
    assert Path(python_path).is_file()

    # The venv's interpreter is the embedded python-build-standalone one, not
    # anything from the host.
    resolved = Path(python_path).resolve()
    assert str(resolved).startswith(offline_env["AXE_DATA_DIR"])


def test_self_commands_offline(binary: Path, offline_env: dict[str, str]):
    # metadata is exposed in the example's [tool.axe].
    result = run(binary, ["self", "metadata"], offline_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "name: cowsay" in result.stdout
    assert "version: 0.1.0" in result.stdout

    # `python` is NOT exposed, so it must not exist.
    result = run(binary, ["self", "python"], offline_env, timeout=60)
    assert result.returncode != 0
    assert "unknown self command" in result.stderr

    # remove wipes the installation; the next run bootstraps again, offline.
    result = run(binary, ["self", "remove"], offline_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "removed" in result.stderr

    result = run(binary, ["moo"], offline_env)
    assert result.returncode == 0, result.stderr
    assert "< moo >" in result.stdout
    assert "first run" in result.stderr

    # restore reinstalls in one step.
    result = run(binary, ["self", "restore"], offline_env)
    assert result.returncode == 0, result.stderr
    result = run(binary, ["back"], offline_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "first run" not in result.stderr


def test_interrupted_bootstrap_recovers(binary: Path, offline_env: dict[str, str], tmp_path):
    # Simulate a crash mid-bootstrap: install dir exists but has no
    # completion marker. The next run must rebuild, not trust the residue.
    env = dict(offline_env, AXE_DATA_DIR=str(tmp_path / "data"))
    result = run(binary, ["ok"], env)
    assert result.returncode == 0, result.stderr

    (install,) = (tmp_path / "data" / "cowsay").iterdir()
    (install / ".axe-installed").unlink()
    result = run(binary, ["rebuilt"], env)
    assert result.returncode == 0, result.stderr
    assert "first run" in result.stderr
    assert "< rebuilt >" in result.stdout


def test_plain_stub_refuses_to_run(tmp_path, offline_env: dict[str, str]):
    stub = tmp_path / "bare-stub"
    stub.write_bytes(load_stub(*current_platform()))
    stub.chmod(0o755)
    result = run(stub, [], offline_env, timeout=60)
    assert result.returncode != 0
    assert "no axe payload" in result.stderr


def test_bare_uv_init_project_fails_at_build_time(tmp_path):
    # A bare `uv init` app (no [project.scripts], no [build-system]) must be
    # rejected at build time, not fail on the end user's machine.
    from axe.wheel import WheelError

    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "testaxe"
version = "0.1.0"
requires-python = ">=3.12"

[tool.axe]
entrypoint = "testaxe"
"""
    )
    (tmp_path / "main.py").write_text("def main():\n    print('hi')\n")
    with pytest.raises(WheelError, match="no console scripts"):
        build(tmp_path, output_dir=tmp_path / "out")


def test_all_platforms_build(tmp_path):
    outputs = build(COWSAY, output_dir=tmp_path, all_platforms=True)
    names = sorted(p.name for p in outputs)
    assert names == [
        "cowsay-0.1.0-darwin-amd64",
        "cowsay-0.1.0-darwin-arm64",
        "cowsay-0.1.0-linux-amd64",
        "cowsay-0.1.0-linux-arm64",
        "cowsay-0.1.0-windows-amd64.exe",
    ]
    # Each binary embeds its own platform's Python: they must differ.
    sizes = {p.stat().st_size for p in outputs}
    assert len(sizes) > 1


def test_cli_smoke(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    result = subprocess.run(
        [sys.executable, "-m", "axe.cli", "platforms"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "darwin/arm64" in result.stdout

    result = subprocess.run(
        [sys.executable, "-m", "axe.cli", "build", str(COWSAY), "-o", str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.glob("cowsay-*"))
