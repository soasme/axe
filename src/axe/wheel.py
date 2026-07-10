"""Validate that a built wheel can actually satisfy the configured entrypoint.

Without this check, a binary would bootstrap fine on the end user's machine
and then fail to exec — the worst possible place to discover the problem. The
classic trap is a bare `uv init` project: no [project.scripts] and no
[build-system], so the legacy setuptools fallback builds a wheel containing
only main.py and zero console scripts.
"""

from __future__ import annotations

import io
import zipfile
from configparser import ConfigParser

from .config import Entrypoint


class WheelError(Exception):
    pass


def _namelist(wheel_bytes: bytes) -> list[str]:
    try:
        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as zf:
            return zf.namelist()
    except zipfile.BadZipFile as e:
        raise WheelError(f"built wheel is not a valid zip: {e}") from None


def console_scripts(wheel_bytes: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as zf:
        for name in zf.namelist():
            if name.endswith(".dist-info/entry_points.txt"):
                parser = ConfigParser()
                parser.optionxform = str  # script names are case-sensitive
                parser.read_string(zf.read(name).decode())
                if parser.has_section("console_scripts"):
                    return set(parser.options("console_scripts"))
    return set()


def has_module(wheel_bytes: bytes, module: str) -> bool:
    top = module.split(".")[0]
    return any(name == f"{top}.py" or name.startswith(f"{top}/") for name in _namelist(wheel_bytes))


PACKAGING_HINT = (
    "Make sure pyproject.toml declares a build backend that packages your "
    "code (projects created with `uv init --package` are set up correctly; "
    "a bare `uv init` project is not packaged at all)."
)


def validate_entrypoint(wheel_bytes: bytes, entrypoint: Entrypoint) -> None:
    if entrypoint.kind == "script":
        scripts = console_scripts(wheel_bytes)
        if entrypoint.value in scripts:
            return
        if scripts:
            raise WheelError(
                f"the built wheel provides no console script named {entrypoint.value!r} "
                f"(it provides: {', '.join(sorted(scripts))})"
            )
        raise WheelError(
            f"the built wheel provides no console scripts, so the binary could "
            f"never run {entrypoint.value!r}. Declare the script in pyproject.toml:\n\n"
            f"    [project.scripts]\n"
            f'    {entrypoint.value} = "<module>:<function>"\n\n' + PACKAGING_HINT
        )

    module = entrypoint.value.split(":")[0] if entrypoint.kind == "spec" else entrypoint.value
    if not has_module(wheel_bytes, module):
        raise WheelError(
            f"the built wheel does not contain the module {module!r} needed by "
            f"entrypoint {entrypoint.value!r}. " + PACKAGING_HINT
        )
