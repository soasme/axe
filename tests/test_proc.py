import sys

import pytest

from axe import output
from axe.proc import ToolError, run_tool


@pytest.fixture(autouse=True)
def normal_level():
    output.set_level(output.NORMAL)
    yield
    output.set_level(output.NORMAL)


def test_returns_stdout():
    out = run_tool(
        [sys.executable, "-c", "print('hello')"], what="test tool", timeout=30
    )
    assert out.strip() == "hello"


def test_timeout_is_actionable():
    with pytest.raises(ToolError, match=r"timed out after 1s.*stalled network.*--verbose"):
        run_tool(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            what="sleepy tool",
            timeout=1,
        )


def test_failure_includes_stderr_and_hint():
    with pytest.raises(ToolError, match=r"(?s)broken tool failed:.*boom.*try the hint"):
        run_tool(
            [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"],
            what="broken tool",
            timeout=30,
            hint="try the hint",
        )


def test_missing_binary():
    with pytest.raises(ToolError, match="ghost tool"):
        run_tool(["/nonexistent/binary"], what="ghost tool", timeout=30)


def test_output_levels(capsys):
    output.set_level(output.QUIET)
    output.progress("nope")
    output.result("nope")
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""

    output.set_level(output.NORMAL)
    output.progress("working")
    output.result("built it")
    captured = capsys.readouterr()
    assert captured.err == "working\n"  # progress -> stderr
    assert captured.out == "built it\n"  # results -> stdout
    assert not output.verbose()

    output.set_level(output.VERBOSE)
    assert output.verbose()
