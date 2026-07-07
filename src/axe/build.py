"""The `axe build` implementation: wheel + stub -> single-file binary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from importlib.resources import files
from pathlib import Path

from . import trailer
from .config import BuildConfig, load_config
from .wheel import validate_entrypoint
from .platforms import (
    SUPPORTED_PLATFORMS,
    binary_filename,
    current_platform,
    parse_platform,
    stub_filename,
)


class BuildError(Exception):
    pass


def find_uv() -> str:
    uv = shutil.which("uv")
    if not uv:
        raise BuildError("uv not found on PATH; install it from https://docs.astral.sh/uv/")
    return uv


def build_wheel(project_dir: Path, out_dir: Path) -> Path:
    result = subprocess.run(
        [find_uv(), "build", "--wheel", "--out-dir", str(out_dir), str(project_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BuildError(f"uv build failed:\n{result.stderr.strip()}")
    wheels = sorted(out_dir.glob("*.whl"))
    if not wheels:
        raise BuildError("uv build produced no wheel")
    return wheels[0]


def load_stub(goos: str, goarch: str) -> bytes:
    resource = files("axe").joinpath("stubs", stub_filename(goos, goarch))
    if not resource.is_file():
        raise BuildError(
            f"runtime stub for {goos}/{goarch} is missing from this axe installation "
            "(for a source checkout, run scripts/build_stubs.py first)"
        )
    return resource.read_bytes()


def make_runtime_config(config: BuildConfig, wheel_path: Path, wheel_bytes: bytes) -> bytes:
    doc = config.runtime_config()
    doc["wheel_name"] = wheel_path.name
    base = json.dumps(doc, sort_keys=True).encode()
    doc["fingerprint"] = hashlib.sha256(wheel_bytes + base).hexdigest()[:16]
    return json.dumps(doc, sort_keys=True).encode()


def build(
    project_dir: Path,
    output_dir: Path | None = None,
    platforms: list[str] | None = None,
    all_platforms: bool = False,
) -> list[Path]:
    project_dir = project_dir.resolve()
    config = load_config(project_dir)

    if all_platforms:
        targets = SUPPORTED_PLATFORMS
    elif platforms:
        targets = [parse_platform(p) for p in platforms]
    else:
        targets = [current_platform()]

    # Fail before the wheel build if any needed stub is absent.
    stubs = {target: load_stub(*target) for target in targets}

    output_dir = (output_dir or project_dir / "dist" / "bin").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="axe-build-") as tmp:
        wheel_path = build_wheel(project_dir, Path(tmp))
        wheel_bytes = wheel_path.read_bytes()

    # Refuse to ship a binary whose entrypoint the wheel can't satisfy; that
    # failure would otherwise surface on the end user's machine after
    # bootstrap.
    validate_entrypoint(wheel_bytes, config.entrypoint)

    config_bytes = make_runtime_config(config, wheel_path, wheel_bytes)

    outputs = []
    for (goos, goarch), stub in stubs.items():
        out = output_dir / binary_filename(config.name, config.version, goos, goarch)
        out.write_bytes(trailer.pack(stub, wheel_bytes, config_bytes))
        out.chmod(0o755)
        outputs.append(out)
        print(f"built {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}")
    return outputs


