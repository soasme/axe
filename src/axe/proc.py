"""Run external tools (uv, pip) with timeouts and controllable output.

Normally output is captured and only shown on failure; with --verbose the
tool's stderr streams live to the terminal. A timeout turns a silent network
stall into an actionable error instead of an apparent hang.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import output

NETWORK_HINT = (
    "If this machine is behind a corporate (TLS-intercepting) proxy, set "
    "UV_NATIVE_TLS=1 so uv uses the system trust store; for pip also set "
    "PIP_CERT to your CA bundle."
)


class ToolError(Exception):
    pass


def run_tool(
    cmd: list[str],
    *,
    what: str,
    timeout: float,
    cwd: Path | None = None,
    hint: str = "",
    env: dict[str, str] | None = None,
) -> str:
    """Run a tool and return its stdout. The build machine's environment is
    inherited (env=None) so UV_*/PIP_* variables steer uv and pip; pass env
    to substitute a modified copy."""
    if output.verbose():
        output.progress(f"$ {' '.join(str(c) for c in cmd)}")
    stderr = None if output.verbose() else subprocess.PIPE
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(
            f"{what} timed out after {timeout:.0f}s — this usually means a "
            f"stalled network connection. {hint} "
            "Rerun with --verbose to watch the underlying tool."
        ) from None
    except FileNotFoundError as e:
        raise ToolError(f"{what}: {e}") from None

    if proc.returncode != 0:
        message = f"{what} failed"
        if detail := (proc.stderr or "").strip():
            message += f":\n{detail}"
        else:
            message += " (rerun with --verbose to see the tool's output)"
        if hint:
            message += f"\n{hint}"
        raise ToolError(message)
    return proc.stdout or ""
