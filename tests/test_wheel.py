import io
import zipfile

import pytest

from axe.config import Entrypoint
from axe.wheel import WheelError, console_scripts, has_module, validate_entrypoint


def make_wheel(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


GOOD_WHEEL = make_wheel(
    {
        "demo/__init__.py": "def main(): ...",
        "demo-1.0.dist-info/METADATA": "Name: demo",
        "demo-1.0.dist-info/entry_points.txt": (
            "[console_scripts]\ndemo = demo:main\nDemo-Alt = demo:alt\n"
        ),
    }
)

# What a bare `uv init` project produces via the legacy setuptools fallback:
# just main.py, no entry points.
BARE_UV_INIT_WHEEL = make_wheel(
    {
        "main.py": "def main(): ...",
        "testaxe-0.1.0.dist-info/METADATA": "Name: testaxe",
        "testaxe-0.1.0.dist-info/top_level.txt": "main\n",
    }
)


def test_console_scripts():
    assert console_scripts(GOOD_WHEEL) == {"demo", "Demo-Alt"}
    assert console_scripts(BARE_UV_INIT_WHEEL) == set()


def test_has_module():
    assert has_module(GOOD_WHEEL, "demo")
    assert has_module(GOOD_WHEEL, "demo.sub")
    assert has_module(BARE_UV_INIT_WHEEL, "main")
    assert not has_module(GOOD_WHEEL, "other")


def test_script_entrypoint_ok():
    validate_entrypoint(GOOD_WHEEL, Entrypoint("script", "demo"))


def test_script_entrypoint_missing_lists_alternatives():
    with pytest.raises(WheelError, match=r"no console script named 'nope'.*demo"):
        validate_entrypoint(GOOD_WHEEL, Entrypoint("script", "nope"))


def test_bare_uv_init_project_is_rejected():
    # Regression: a bare `uv init` app used to build a binary that failed on
    # the end user's machine with "entrypoint ... does not exist".
    with pytest.raises(WheelError, match=r"(?s)no console scripts.*project\.scripts"):
        validate_entrypoint(BARE_UV_INIT_WHEEL, Entrypoint("script", "testaxe"))


def test_module_entrypoint():
    validate_entrypoint(BARE_UV_INIT_WHEEL, Entrypoint("module", "main"))
    with pytest.raises(WheelError, match="does not contain the module"):
        validate_entrypoint(BARE_UV_INIT_WHEEL, Entrypoint("module", "missing"))


def test_spec_entrypoint():
    validate_entrypoint(GOOD_WHEEL, Entrypoint("spec", "demo:main"))
    with pytest.raises(WheelError, match="does not contain the module"):
        validate_entrypoint(GOOD_WHEEL, Entrypoint("spec", "missing:main"))


def test_invalid_zip():
    with pytest.raises(WheelError, match="not a valid zip"):
        validate_entrypoint(b"not a wheel", Entrypoint("module", "x"))
