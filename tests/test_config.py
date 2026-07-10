import pytest

from axe.config import (
    ConfigError,
    load_config,
    parse_entrypoint,
    python_from_requires,
)


def write_pyproject(tmp_path, body):
    (tmp_path / "pyproject.toml").write_text(body)
    return tmp_path


def test_defaults_from_project_scripts(tmp_path):
    config = load_config(
        write_pyproject(
            tmp_path,
            """
[project]
name = "demo"
version = "1.2.3"
requires-python = ">=3.10"

[project.scripts]
demo = "demo:main"
""",
        )
    )
    assert config.name == "demo"
    assert config.version == "1.2.3"
    assert config.entrypoint.kind == "script"
    assert config.entrypoint.value == "demo"
    assert config.python_version == "3.10"
    assert config.expose == []


def test_tool_axe_overrides(tmp_path):
    config = load_config(
        write_pyproject(
            tmp_path,
            """
[project]
name = "demo"
version = "0.1.0"

[tool.axe]
entrypoint = "-m demo"
python = "3.13"
uv-version = "0.9.0"
expose = ["metadata", "python-path"]
""",
        )
    )
    assert config.entrypoint.kind == "module"
    assert config.entrypoint.value == "demo"
    assert config.python_version == "3.13"
    assert config.uv_version == "0.9.0"
    assert config.expose == ["metadata", "python-path"]


def test_expose_all(tmp_path):
    config = load_config(
        write_pyproject(
            tmp_path,
            """
[project]
name = "demo"
version = "0.1.0"

[tool.axe]
entrypoint = "demo"
expose = "all"
""",
        )
    )
    assert set(config.expose) == {"python", "python-path", "cache", "metadata"}


def test_no_entrypoint_errors(tmp_path):
    with pytest.raises(ConfigError, match="no entrypoint"):
        load_config(write_pyproject(tmp_path, '[project]\nname = "demo"\nversion = "0.1.0"\n'))


def test_ambiguous_scripts_error(tmp_path):
    with pytest.raises(ConfigError, match="multiple"):
        load_config(
            write_pyproject(
                tmp_path,
                """
[project]
name = "demo"
version = "0.1.0"

[project.scripts]
a = "demo:a"
b = "demo:b"
""",
            )
        )


def test_unknown_expose_command(tmp_path):
    with pytest.raises(ConfigError, match="unknown expose"):
        load_config(
            write_pyproject(
                tmp_path,
                """
[project]
name = "demo"
version = "0.1.0"

[tool.axe]
entrypoint = "demo"
expose = ["pip"]
""",
            )
        )


def test_missing_pyproject(tmp_path):
    with pytest.raises(ConfigError, match="no pyproject.toml"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    ("value", "kind", "parsed"),
    [
        ("demo", "script", "demo"),
        ("-m demo.cli", "module", "demo.cli"),
        ("demo.cli:main", "spec", "demo.cli:main"),
    ],
)
def test_parse_entrypoint(value, kind, parsed):
    entrypoint = parse_entrypoint(value)
    assert (entrypoint.kind, entrypoint.value) == (kind, parsed)


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (">=3.10", "3.10"),
        (">=3.11,<4", "3.11"),
        ("~=3.12.1", "3.12.1"),
        ("==3.10.*", "3.10"),
        ("<4", None),
        ("", None),
    ],
)
def test_python_from_requires(spec, expected):
    assert python_from_requires(spec) == expected
