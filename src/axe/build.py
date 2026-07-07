"""The `axe build` implementation: stub + offline payload -> single binary.

Everything an installation needs (uv, CPython, the app wheel, every
dependency wheel) is fetched on the build machine and embedded, so the end
user's first run never touches the network.
"""

from __future__ import annotations

import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from . import output, payload, trailer
from .config import load_config
from .fetch import fetch_python, fetch_uv, resolve_python
from .platforms import (
    SUPPORTED_PLATFORMS,
    binary_filename,
    current_platform,
    parse_platform,
    stub_filename,
)
from .proc import run_tool
from .resolve import compile_requirements, download_wheels, pinned_count
from .wheel import validate_entrypoint


class BuildError(Exception):
    pass


def find_uv() -> str:
    uv = shutil.which("uv")
    if not uv:
        raise BuildError("uv not found on PATH; install it from https://docs.astral.sh/uv/")
    return uv


def build_wheel(uv: str, project_dir: Path, out_dir: Path) -> Path:
    output.progress("building project wheel...")
    run_tool(
        [uv, "build", "--wheel", "--out-dir", str(out_dir), str(project_dir)],
        what="uv build",
        timeout=300,
    )
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


def build(
    project_dir: Path,
    output_dir: Path | None = None,
    platforms: list[str] | None = None,
    all_platforms: bool = False,
) -> list[Path]:
    project_dir = project_dir.resolve()
    config = load_config(project_dir)
    uv = find_uv()

    if all_platforms:
        targets = SUPPORTED_PLATFORMS
    elif platforms:
        targets = [parse_platform(p) for p in platforms]
    else:
        targets = [current_platform()]

    # Fail before any network work if a needed stub is absent.
    stubs = {target: load_stub(*target) for target in targets}

    output_dir = (output_dir or project_dir / "dist" / "bin").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="axe-build-") as tmp:
        wheel_path = build_wheel(uv, project_dir, Path(tmp))
        wheel_bytes = wheel_path.read_bytes()

        # Refuse to ship a binary whose entrypoint the wheel can't satisfy;
        # that failure would otherwise surface on the end user's machine.
        validate_entrypoint(wheel_bytes, config.entrypoint)

        outputs = []
        for (goos, goarch), stub in stubs.items():
            target = f"{goos}/{goarch}"
            python_version, python_artifact = resolve_python(
                config.python_version, config.python_release, goos, goarch
            )
            python_path = fetch_python(python_artifact, config.python_release)
            uv_path = fetch_uv(config.uv_version, goos, goarch)

            output.progress(f"{target}: resolving dependencies...")
            requirements = compile_requirements(
                uv, project_dir, goos, goarch, python_version
            )
            if count := pinned_count(requirements):
                output.progress(f"{target}: downloading {count} dependency wheels...")
            dep_wheels = download_wheels(
                uv,
                requirements,
                goos,
                goarch,
                python_version,
                Path(tmp) / f"wheels-{goos}-{goarch}",
            )

            payload_zip = payload.compose(
                config.runtime_config(python_version),
                wheel_path.name,
                wheel_bytes,
                dep_wheels,
                uv_path,
                python_path,
            )

            out = output_dir / binary_filename(config.name, config.version, goos, goarch)
            out.write_bytes(trailer.pack(stub, payload_zip))
            out.chmod(0o755)
            outputs.append(out)
            output.result(
                f"built {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}"
                f" ({out.stat().st_size / 1e6:.0f} MB, python {python_version},"
                f" {len(dep_wheels)} dependency wheels)"
            )
    return outputs
