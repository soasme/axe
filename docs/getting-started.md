# Getting started

This page takes you from an empty directory to a binary you can hand to
someone who has never heard of Python.

## What you need

- **Python 3.11+ and [uv](https://docs.astral.sh/uv/)** on the *build*
  machine. That's all — no Go, no cross-compilers, no Docker. Axe's wheel
  ships precompiled runtime stubs for every supported platform.
- **Nothing** on the *target* machine. The binary embeds uv, CPython, and
  every dependency wheel; it bootstraps itself offline on first run.

Axe builds *installable packages with a console script*. A project created
with `uv init --package` is already set up correctly; if yours isn't, axe
tells you exactly what to add (see [Project requirements](#project-requirements)
below).

## Install

Add axe as a development dependency of your project:

```console
$ uv add --dev axe
```

Or install it as a standalone tool: `uv tool install axe` (or `pip install axe`).

## Build your first binary

```console
$ uv init --package mycli
$ cd mycli
$ uv add --dev axe
$ uv run axe build
built dist/bin/mycli-0.1.0-darwin-arm64 (47 MB, python 3.12.13, 0 dependency wheels)
```

With no flags, `axe build` targets the platform you're on. Add
`--all-platforms` to build all five supported targets in one go, or pick
specific ones with `-p`:

```console
$ uv run axe build --all-platforms
$ uv run axe build -p linux/amd64 -p windows/amd64
```

All artifacts (CPython, uv, dependency wheels) are fetched once on the build
machine, checksum-verified, and cached — builds after the first take seconds.

## Run it

```console
$ ./dist/bin/mycli-0.1.0-darwin-arm64
[axe] bootstrapping mycli 0.1.0...
Hello from mycli!

$ ./dist/bin/mycli-0.1.0-darwin-arm64   # instant from now on
Hello from mycli!
```

The first run unpacks the embedded Python and installs the embedded wheels
into a cached per-app environment — entirely offline. Every run after that is
a single existence check, then a direct hand-off to your app. Corporate
proxy, air gap, TLS-intercepting middlebox: none of it matters, because the
runtime contains no network code at all.

Hand the file to anyone on a matching OS/architecture; there is nothing to
install and nothing to download.

## Project requirements

`axe build` reads everything from your `pyproject.toml`:

- a `[project]` table with `name` and a static `version`,
- an entrypoint — by default the sole `[project.scripts]` entry
  ([configurable](reference/configuration.md#entrypoint)),
- every dependency must publish a wheel for each platform you target
  (pure-Python wheels cover all of them).

A bare `uv init` project (no package, no console script) is not buildable
as-is; `axe build` prints the exact `pyproject.toml` additions it needs.

## Where to go next

- [Tutorial: package a CLI as a single binary](tutorials/first-binary.md) —
  a complete walkthrough with a real dependency and runtime management.
- [Tutorial: release binaries from GitHub Actions](tutorials/github-actions.md).
- [Configuration reference](reference/configuration.md) — pin the Python
  version, choose an entrypoint, expose extra runtime commands.
- [Runtime reference](reference/runtime.md) — what `myapp self remove /
  restore / update` do and where installations live.
