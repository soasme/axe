# Runtime reference

This page covers what a *built binary* provides on the user's machine: the
`self` management commands, the environment variables the runtime reads and
sets, and where installations live. For how the bootstrap works internally,
see [runtime internals](../runtime.md).

## `self` commands

Built binaries reserve exactly one command group, `self`; every other
invocation is passed untouched to your app. (Even that reservation is
optional: building with
[`AXE_ENABLE_SELF_COMMAND_GROUP=false`](configuration.md#axe_enable_self_command_group)
produces binaries with no `self` group at all.)

Always available:

| Command | Effect |
| --- | --- |
| `myapp self remove` | delete this binary's installation from disk |
| `myapp self restore` | delete, then reinstall from the embedded payload |
| `myapp self update` | alias of `restore` — reinstall from the embedded payload |

Available only when [exposed at build time](configuration.md#expose):

| Command | Effect |
| --- | --- |
| `myapp self python [args…]` | run the installed venv interpreter (installs first if needed) |
| `myapp self python-path` | print the venv interpreter's path (installs first if needed) |
| `myapp self cache` | print the shared uv cache directory |
| `myapp self cache -r` | remove the shared uv cache (`--remove` also works) |
| `myapp self metadata` | print name, version, python, uv version, and install path |

A `self` subcommand that wasn't exposed fails with `unknown self command`,
indistinguishable from one that doesn't exist.

## Environment variables

Read by the runtime:

| Variable | Effect |
| --- | --- |
| `AXE_DATA_DIR` | override the base directory for per-app installations |
| `AXE_CACHE_DIR` | override the shared cache directory (embedded uv extractions) |
| `AXE_UV` | path to a uv binary to use instead of the embedded one |
| `AXE_DEBUG=1` | make the stub verbose about every bootstrap step |

Set for your app:

| Variable | Meaning |
| --- | --- |
| `AXE=1` | present in the app's environment so it can detect axe installs |

The runtime also *sanitizes* the environment for consistency across user
machines: apps run in Python's isolated mode (user site-packages and
`PYTHON*` variables never leak in), and during installation any inherited
`UV_*`, `PIP_*`, `PYTHON*`, `VIRTUAL_ENV`, or `CONDA_PREFIX` variables are
dropped. Details in [runtime internals](../runtime.md#execution).

## Install locations

Installations live at `<data dir>/<app name>/<payload fingerprint>`, where
the data directory defaults to:

| OS | Data directory |
| --- | --- |
| Linux | `$XDG_DATA_HOME/axe` or `~/.local/share/axe` |
| macOS | `~/Library/Application Support/axe` |
| Windows | `%LOCALAPPDATA%\axe` |

The fingerprint is derived from the payload, so a new binary version gets a
fresh environment automatically. `self remove` deletes the *current*
binary's installation; directories left behind by older versions are safe to
delete manually.

The shared cache — the extracted uv release, reused by every axe app that
pins the same uv version — lives under the platform cache directory:

| OS | Cache directory |
| --- | --- |
| Linux | `$XDG_CACHE_HOME/axe` or `~/.cache/axe` |
| macOS | `~/Library/Caches/axe` |
| Windows | `%LOCALAPPDATA%\axe` |

## Offline guarantee

The runtime contains no network code at all. Bootstrap extracts the embedded
CPython and uv, creates a venv, and installs the embedded wheels with
`--offline --no-index`. If it can't finish (disk full, permissions), it
fails with a clear error — it never falls back to downloading anything.
