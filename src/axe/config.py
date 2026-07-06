"""Load build configuration from pyproject.toml ([project] + [tool.axe])."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import DEFAULT_PYTHON_VERSION, DEFAULT_UV_VERSION

EXPOSABLE_COMMANDS = ("python", "python-path", "cache", "metadata")


class ConfigError(Exception):
    pass


@dataclass
class Entrypoint:
    # "script": console script installed by the wheel
    # "module": run as `python -I -m <value>`
    # "spec":   "pkg.mod:func" run via the interpreter
    kind: str
    value: str


@dataclass
class BuildConfig:
    name: str
    version: str
    entrypoint: Entrypoint
    python_version: str
    uv_version: str = DEFAULT_UV_VERSION
    expose: list[str] = field(default_factory=list)

    def runtime_config(self) -> dict:
        """The JSON document embedded in built binaries, minus fingerprint."""
        return {
            "name": self.name,
            "version": self.version,
            "entrypoint": {"kind": self.entrypoint.kind, "value": self.entrypoint.value},
            "python_version": self.python_version,
            "uv_version": self.uv_version,
            "expose": self.expose,
        }


def parse_entrypoint(value: str) -> Entrypoint:
    value = value.strip()
    if value.startswith("-m "):
        return Entrypoint("module", value[3:].strip())
    if ":" in value:
        return Entrypoint("spec", value)
    return Entrypoint("script", value)


def python_from_requires(requires_python: str) -> str | None:
    """Pick the lowest CPython version a requires-python specifier allows.

    Only lower-bound specifiers pin a version; pure upper bounds fall back to
    the axe default.
    """
    for spec in requires_python.split(","):
        m = re.match(r"\s*(>=|==|~=)\s*(\d+\.\d+(?:\.\d+)?)", spec.strip())
        if m:
            return m.group(2).removesuffix(".*")
    return None


def load_config(project_dir: Path) -> BuildConfig:
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.is_file():
        raise ConfigError(f"no pyproject.toml found in {project_dir}")
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project")
    if not project:
        raise ConfigError("pyproject.toml has no [project] table")
    name = project.get("name")
    version = project.get("version")
    if not name:
        raise ConfigError("[project] is missing 'name'")
    if not version:
        raise ConfigError("[project] is missing 'version' (dynamic versions are not supported yet)")

    axe = data.get("tool", {}).get("axe", {})

    if raw_entrypoint := axe.get("entrypoint"):
        entrypoint = parse_entrypoint(raw_entrypoint)
    else:
        scripts = project.get("scripts", {})
        if len(scripts) == 1:
            entrypoint = Entrypoint("script", next(iter(scripts)))
        elif not scripts:
            raise ConfigError(
                "no entrypoint: define [project.scripts] or set entrypoint in [tool.axe]"
            )
        else:
            raise ConfigError(
                "multiple [project.scripts] entries; set entrypoint in [tool.axe] "
                f"to one of: {', '.join(sorted(scripts))}"
            )

    if python_version := axe.get("python"):
        python_version = str(python_version)
    else:
        python_version = (
            python_from_requires(project.get("requires-python", "")) or DEFAULT_PYTHON_VERSION
        )

    expose = axe.get("expose", [])
    if expose == "all":
        expose = list(EXPOSABLE_COMMANDS)
    for command in expose:
        if command not in EXPOSABLE_COMMANDS:
            raise ConfigError(
                f"unknown expose command {command!r}; valid: {', '.join(EXPOSABLE_COMMANDS)}"
            )

    return BuildConfig(
        name=name,
        version=str(version),
        entrypoint=entrypoint,
        python_version=python_version,
        uv_version=str(axe.get("uv-version", DEFAULT_UV_VERSION)),
        expose=list(expose),
    )
