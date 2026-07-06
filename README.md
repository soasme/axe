# Axe

Axe ships your Python app as a self-bootstrapping single-file binary — for
every major platform, from any machine, with **zero** extra toolchain.

- **App developers** need no Go, no cross-compilers, no Docker. Axe's wheel
  ships precompiled runtime stubs; `axe build` just glues your app onto them.
- **App users** need no Python and no uv. The binary bootstraps a cached
  environment on first run (uv installs Python and your app) and is instant on
  every run after — the same runtime contract as
  [pyapp](https://github.com/ofek/pyapp), uv-first.

## Quick start

```console
$ uv add --dev axe-build
$ axe build --all-platforms
built dist/bin/cowsay-0.1.0-linux-amd64
built dist/bin/cowsay-0.1.0-linux-arm64
built dist/bin/cowsay-0.1.0-darwin-amd64
built dist/bin/cowsay-0.1.0-darwin-arm64
built dist/bin/cowsay-0.1.0-windows-amd64.exe
```

Hand the binary to anyone:

```console
$ ./cowsay-0.1.0-darwin-arm64 hello
setting up cowsay 0.1.0 (first run)...
done.
 _______
< hello >
 -------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```

## How it works

`axe build` builds your project's wheel with uv, then appends it — plus a
small JSON config — to a precompiled Go runtime stub for each target platform.
Building is byte concatenation, so cross-"compiling" all platforms takes
seconds anywhere.

At first run the stub downloads a pinned uv (checksum-verified, cached across
apps), lets uv provision the pinned CPython, installs the embedded wheel into
a per-app environment keyed by payload fingerprint, and hands off to your app
(`execvp` on Unix). Subsequent runs are a single existence check.

## Configuration

Everything is optional; defaults come from `[project]`:

```toml
[tool.axe]
entrypoint = "mycli"          # default: the sole [project.scripts] entry
                              # also accepts "-m pkg" or "pkg.mod:func"
python = "3.12"               # default: lower bound of requires-python
uv-version = "0.10.6"         # uv the runtime bootstraps
expose = ["metadata"]         # extra `self` commands: python, python-path,
                              # cache, metadata — or "all"
```

## CLI

```console
$ axe build [PROJECT] [-o DIR] [-p OS/ARCH]... [--all-platforms]
$ axe platforms
```

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

`AXE=1` is set in your app's environment so it can detect axe installs, and
`AXE_DEBUG=1` makes the stub verbose.

## Developing axe itself

This is the one place a Go toolchain is required:

```console
$ python scripts/build_stubs.py   # cross-compile runtime stubs (needs go)
$ uv run pytest                   # unit + end-to-end tests
$ cd runtime && go test ./...     # runtime unit tests
$ uv build                        # the wheel, stubs included
```

Design doc: `docs/superpowers/specs/2026-07-07-axe-design.md`.
