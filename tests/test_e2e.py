"""End-to-end contract: `axe build` produces a binary that bootstraps and runs.

Requires uv on PATH and the current platform's stub (scripts/build_stubs.py).
The binary runs against isolated AXE_DATA_DIR/AXE_CACHE_DIR; AXE_UV points at
the host uv so the default suite stays off the network. Set AXE_TEST_NETWORK=1
to also exercise the real uv download path.
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
def isolated_env(tmp_path_factory) -> dict[str, str]:
    root = tmp_path_factory.mktemp("axe-home")
    env = os.environ.copy()
    env["AXE_DATA_DIR"] = str(root / "data")
    env["AXE_CACHE_DIR"] = str(root / "cache")
    env["AXE_UV"] = shutil.which("uv")
    return env


def run(binary: Path, args: list[str], env: dict[str, str], timeout: int = 600):
    return subprocess.run(
        [str(binary), *args], env=env, capture_output=True, text=True, timeout=timeout
    )


def test_binary_lifecycle(binary: Path, isolated_env: dict[str, str]):
    stub_size = len(load_stub(*current_platform()))
    assert binary.stat().st_size > stub_size
    assert os.access(binary, os.X_OK)

    # First run bootstraps, then speaks.
    result = run(binary, ["hello", "world"], isolated_env)
    assert result.returncode == 0, result.stderr
    assert "< hello world >" in result.stdout
    assert "first run" in result.stderr
    # The app can detect it's running from an axe binary (AXE=1).
    assert "(running from an axe binary)" in result.stderr

    # Second run takes the fast path: no bootstrap chatter.
    result = run(binary, ["again"], isolated_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "< again >" in result.stdout
    assert "first run" not in result.stderr

    # Exit codes pass through untouched.
    result = run(
        binary,
        ["self", "python-path"],
        isolated_env,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    python_path = result.stdout.strip()
    assert python_path.startswith(isolated_env["AXE_DATA_DIR"])
    assert Path(python_path).is_file()


def test_self_commands(binary: Path, isolated_env: dict[str, str]):
    # metadata is exposed in the example's [tool.axe].
    result = run(binary, ["self", "metadata"], isolated_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "name: cowsay" in result.stdout
    assert "version: 0.1.0" in result.stdout

    # `python` is NOT exposed, so it must not exist.
    result = run(binary, ["self", "python"], isolated_env, timeout=60)
    assert result.returncode != 0
    assert "unknown self command" in result.stderr

    # remove wipes the installation; the next run bootstraps again.
    result = run(binary, ["self", "remove"], isolated_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "removed" in result.stderr

    result = run(binary, ["moo"], isolated_env)
    assert result.returncode == 0, result.stderr
    assert "< moo >" in result.stdout
    assert "first run" in result.stderr

    # restore reinstalls in one step.
    result = run(binary, ["self", "restore"], isolated_env)
    assert result.returncode == 0, result.stderr
    result = run(binary, ["back"], isolated_env, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "first run" not in result.stderr


def test_plain_stub_refuses_to_run(tmp_path, isolated_env: dict[str, str]):
    stub = tmp_path / "bare-stub"
    stub.write_bytes(load_stub(*current_platform()))
    stub.chmod(0o755)
    result = run(stub, [], isolated_env, timeout=60)
    assert result.returncode != 0
    assert "no axe payload" in result.stderr


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


@pytest.mark.skipif(
    not os.environ.get("AXE_TEST_NETWORK"),
    reason="set AXE_TEST_NETWORK=1 to test the real uv download path",
)
def test_uv_download_path(binary: Path, tmp_path):
    env = os.environ.copy()
    env.pop("AXE_UV", None)
    env["AXE_DATA_DIR"] = str(tmp_path / "data")
    env["AXE_CACHE_DIR"] = str(tmp_path / "cache")
    result = run(binary, ["network"], env)
    assert result.returncode == 0, result.stderr
    assert "< network >" in result.stdout
    assert "downloading uv" in result.stderr
    assert list((tmp_path / "cache" / "uv").iterdir())
