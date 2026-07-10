# Tutorial: package a CLI as a single binary

In this tutorial you'll build a small command-line app with a real
dependency, compile it into self-contained binaries for every major
platform, and manage the resulting installation on a user's machine. It
takes about ten minutes.

A finished project following the same shape lives in
[`examples/cowsay`](https://github.com/soasme/axe/tree/main/examples/cowsay).

## 1. Create a packaged project

Axe builds installable packages, so start with `--package`:

```console
$ uv init --package greet
$ cd greet
```

This produces a `src/` layout and — crucially — a `[project.scripts]` entry,
which is what axe uses as the entrypoint:

```toml
[project.scripts]
greet = "greet:main"
```

## 2. Add a dependency and some code

```console
$ uv add rich
```

Replace `src/greet/__init__.py` with:

```python
import sys

from rich.console import Console


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "world"
    Console().print(f"[bold magenta]Hello, {name}![/bold magenta]")
```

Check that it works the ordinary way first:

```console
$ uv run greet axe
Hello, axe!
```

## 3. Build binaries

Add axe and build for every supported platform:

```console
$ uv add --dev axe
$ uv run axe build --all-platforms
built dist/bin/greet-0.1.0-linux-amd64 (52 MB, python 3.12.13, 4 dependency wheels)
built dist/bin/greet-0.1.0-linux-arm64 (50 MB, python 3.12.13, 4 dependency wheels)
built dist/bin/greet-0.1.0-darwin-amd64 (48 MB, python 3.12.13, 4 dependency wheels)
built dist/bin/greet-0.1.0-darwin-arm64 (47 MB, python 3.12.13, 4 dependency wheels)
built dist/bin/greet-0.1.0-windows-amd64.exe (55 MB, python 3.12.13, 4 dependency wheels)
```

For each target, axe built your project's wheel, resolved and downloaded
`rich`'s wheels *for that platform*, fetched a pinned CPython and uv, and
appended it all to a precompiled runtime stub. No Go toolchain, no Docker,
no VM — the Linux and Windows binaries were built right here.

Everything downloaded is cached, so rebuilding after a code change takes
seconds. If downloads stall behind a corporate proxy, set `UV_NATIVE_TLS=1`
so uv uses the system trust store.

## 4. Run it like a user would

```console
$ ./dist/bin/greet-0.1.0-darwin-arm64 axe
[axe] bootstrapping greet 0.1.0...
Hello, axe!

$ ./dist/bin/greet-0.1.0-darwin-arm64 axe    # instant from now on
Hello, axe!
```

The first run unpacked the embedded CPython, created a venv, and installed
the embedded wheels with `--offline --no-index` — no network involved. The
installation lives in a per-app directory keyed by payload fingerprint (see
the [runtime reference](../reference/runtime.md#install-locations)), so
shipping `greet 0.2.0` later gets users a fresh environment automatically.

Your app can detect it's running from an axe install by checking the `AXE=1`
environment variable.

## 5. Manage the installation

Every axe binary reserves one command group, `self`; everything else is
passed to your app:

```console
$ ./dist/bin/greet-0.1.0-darwin-arm64 self remove    # wipe the install
$ ./dist/bin/greet-0.1.0-darwin-arm64 self restore   # wipe and reinstall
```

Extra `self` commands can be *exposed* at build time. Add to
`pyproject.toml`:

```toml
[tool.axe]
expose = ["python-path", "metadata"]
```

Rebuild, and users can now inspect the install:

```console
$ ./dist/bin/greet-0.1.0-darwin-arm64 self metadata
name: greet
version: 0.1.0
python: 3.12.13
uv: 0.10.6
install: /Users/you/Library/Application Support/axe/greet/2f8a…
```

The full list is in the [runtime reference](../reference/runtime.md#self-commands).

## 6. Pin the toolchain (optional)

By default axe picks the newest CPython matching the lower bound of your
`requires-python`. To pin things explicitly:

```toml
[tool.axe]
python = "3.12"               # newest 3.12.x; "3.12.13" pins exactly
uv-version = "0.10.6"         # uv embedded into the binary
python-release = "20260623"   # python-build-standalone release tag
```

All options are in the [configuration reference](../reference/configuration.md).

## 7. Ship it

The files under `dist/bin/` are complete — copy one to a matching machine and
it just runs. To automate builds on every release, continue with
[releasing binaries from GitHub Actions](github-actions.md).
