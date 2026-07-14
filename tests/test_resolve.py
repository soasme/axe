import sys

from axe.proc import run_tool
from axe.resolve import pip_env

UV_PIP_VARS = (
    "UV_INDEX_URL",
    "UV_DEFAULT_INDEX",
    "UV_EXTRA_INDEX_URL",
    "PIP_INDEX_URL",
    "PIP_EXTRA_INDEX_URL",
)


def clear_index_vars(monkeypatch):
    for var in UV_PIP_VARS:
        monkeypatch.delenv(var, raising=False)


def test_pip_env_inherits_when_nothing_to_map(monkeypatch):
    clear_index_vars(monkeypatch)
    assert pip_env() is None


def test_pip_env_mirrors_uv_index_vars(monkeypatch):
    clear_index_vars(monkeypatch)
    monkeypatch.setenv("UV_INDEX_URL", "https://mirror.corp/simple")
    monkeypatch.setenv("UV_EXTRA_INDEX_URL", "https://extra.corp/simple")
    env = pip_env()
    assert env["PIP_INDEX_URL"] == "https://mirror.corp/simple"
    assert env["PIP_EXTRA_INDEX_URL"] == "https://extra.corp/simple"


def test_pip_env_maps_default_index(monkeypatch):
    clear_index_vars(monkeypatch)
    monkeypatch.setenv("UV_DEFAULT_INDEX", "https://mirror.corp/simple")
    assert pip_env()["PIP_INDEX_URL"] == "https://mirror.corp/simple"


def test_pip_env_prefers_uv_index_url_over_default_index(monkeypatch):
    clear_index_vars(monkeypatch)
    monkeypatch.setenv("UV_INDEX_URL", "https://legacy.corp/simple")
    monkeypatch.setenv("UV_DEFAULT_INDEX", "https://new.corp/simple")
    assert pip_env()["PIP_INDEX_URL"] == "https://legacy.corp/simple"


def test_pip_env_explicit_pip_vars_win(monkeypatch):
    clear_index_vars(monkeypatch)
    monkeypatch.setenv("UV_INDEX_URL", "https://mirror.corp/simple")
    monkeypatch.setenv("PIP_INDEX_URL", "https://pip.corp/simple")
    assert pip_env() is None  # nothing to map: pip already configured


def test_run_tool_inherits_environment(monkeypatch):
    monkeypatch.setenv("UV_INDEX_URL", "https://mirror.corp/simple")
    out = run_tool(
        [sys.executable, "-c", "import os; print(os.environ['UV_INDEX_URL'])"],
        what="env probe",
        timeout=30,
    )
    assert out.strip() == "https://mirror.corp/simple"
