# Axe

[![Tests](https://github.com/soasme/axe/actions/workflows/test.yml/badge.svg)](https://github.com/soasme/axe/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/axe)](https://pypi.org/project/axe/)

Axe ships your Python app as a **fully self-contained** single-file binary —
for every major platform, from any machine, with zero extra toolchain.

- **App developers** need no Go, no cross-compilers, no Docker. Axe's wheel
  ships precompiled runtime stubs; `axe build` glues your app onto them.
- **App users** need no Python, no uv, and **no network**. The binary embeds
  uv, CPython, and every dependency wheel; the first run unpacks them into a
  cached environment and every run after is instant. Corporate proxy, air-gap,
  TLS-intercepting middlebox — none of it matters.

## Quick start

Your project needs to be an installable package with a console script — a
project created with `uv init --package` is already set up correctly (a bare
`uv init` app is not packaged; `axe build` will tell you what to add):

```console
$ uv init --package mycli
$ cd mycli
$ uv add --dev axe
$ uv run axe build --all-platforms
built dist/bin/mycli-0.1.0-linux-amd64 (52 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-linux-arm64 (50 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-darwin-amd64 (48 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-darwin-arm64 (47 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-windows-amd64.exe (55 MB, python 3.12.13, 0 dependency wheels)
```

Hand the binary to anyone — nothing to install, nothing to download:

```console
$ ./dist/bin/mycli-0.1.0-darwin-arm64
[axe] bootstrapping mycli 0.1.0...
Hello from mycli!

$ ./dist/bin/mycli-0.1.0-darwin-arm64   # instant from now on
Hello from mycli!
```

A fuller example lives in [`examples/cowsay`](examples/cowsay).

## Documentation

Browsable at [soasme.github.io/axe](https://soasme.github.io/axe/), or right
here in the repo:

- [Getting started](docs/getting-started.md) — from zero to a shippable binary
- [Tutorial: package a CLI as a single binary](docs/tutorials/first-binary.md)
- [Tutorial: release binaries from GitHub Actions](docs/tutorials/github-actions.md)
- [CLI reference](docs/reference/cli.md)
- [Configuration reference](docs/reference/configuration.md) — the `[tool.axe]` table
- [Runtime reference](docs/reference/runtime.md) — `self` commands, environment
  variables, install locations
- [Runtime internals](docs/runtime.md) — how the bootstrap works under the hood

## How it works

`axe build` assembles, per target platform, a payload containing everything a
machine needs to run your app:

- your project's wheel (built with uv),
- every dependency wheel, resolved *for that platform* (`uv pip compile
  --python-platform` + `pip download`),
- a pinned CPython from
  [python-build-standalone](https://github.com/astral-sh/python-build-standalone),
- a pinned [uv](https://github.com/astral-sh/uv),

and appends it to a small precompiled Go runtime stub. All artifacts are
fetched once on the *build* machine (checksum-verified, cached), so builds
after the first are seconds.

At first run the stub unpacks the embedded Python and uv, creates a venv, and
installs the embedded wheels with `--offline --no-index` — the runtime
contains no network code at all. Installations live in a per-app directory
keyed by payload fingerprint, so a new binary version gets a fresh
environment automatically. Subsequent runs are a single existence check, then
`execvp` straight into your app.

The full runtime flow — and how it maps onto pyapp's — is documented in
[`docs/runtime.md`](docs/runtime.md). Apps run in Python's isolated mode, so
the user's `PYTHONPATH`, user site-packages, and uv/pip configuration never
leak in.

Because dependencies are shipped as wheels, every dependency must publish a
wheel for each target platform (pure-Python wheels cover all of them).
Binaries weigh roughly 45–60 MB — that's a complete CPython plus uv; disk is
cheap, broken installs are not.

## Configuration

Everything is optional; defaults come from `[project]`:

```toml
[tool.axe]
entrypoint = "mycli"          # default: the sole [project.scripts] entry
                              # also accepts "-m pkg" or "pkg.mod:func"
python = "3.12"               # "3.X" picks the newest 3.X.*; "3.X.Y" pins
                              # default: lower bound of requires-python
uv-version = "0.10.6"         # uv embedded into the binary
python-release = "20260623"   # python-build-standalone release tag
expose = ["metadata"]         # extra `self` commands: python, python-path,
                              # cache, metadata — or "all"
self-command-group = true     # false: don't reserve `self` at all
```

## CLI

```console
$ axe build [PROJECT] [-o DIR] [-p OS/ARCH]... [--all-platforms] [-q | -v]
$ axe platforms
```

`-q`/`--quiet` prints nothing but errors; `-v`/`--verbose` streams the output
of the underlying tools (useful behind corporate proxies — if downloads fail
or stall there, set `UV_NATIVE_TLS=1` so uv uses the system trust store).

Targets: `linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`,
`windows/amd64`.

## Runtime management commands

Built binaries reserve one command group, `self`; everything else goes to
your app:

```console
$ myapp self remove    # wipe the installation
$ myapp self restore   # wipe and reinstall
$ myapp self update    # reinstall from the embedded payload
```

If your CLI needs `self` for itself, set `self-command-group = false` in
`[tool.axe]` and the binary reserves nothing — `self` reaches your app like
any other argument.

`AXE=1` is set in your app's environment so it can detect axe installs, and
`AXE_DEBUG=1` makes the stub verbose.

## Developing axe itself

This is the one place a Go toolchain is required:

```console
$ python scripts/build_stubs.py   # cross-compile runtime stubs (needs go)
$ uv run pytest                   # unit + end-to-end tests (offline-verified)
$ cd runtime && go test ./...     # runtime unit tests
$ uv build                        # the wheel, stubs included
```

Lint and formatting are enforced by [pre-commit](https://pre-commit.com)
(ruff check + format); install the hooks once with `uvx pre-commit install`.
CI runs the same hooks plus both test suites on every pull request.

Runtime behavior is documented in [`docs/runtime.md`](docs/runtime.md).
