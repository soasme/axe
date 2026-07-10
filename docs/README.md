# Axe documentation

Axe ships your Python app as a fully self-contained single-file binary — for
every major platform, from any machine, with zero extra toolchain. Users need
no Python, no uv, and no network.

## Getting started

- [Getting started](getting-started.md) — requirements, installation, and
  your first binary in five minutes.

## Tutorials

Step-by-step walkthroughs of complete workflows:

- [Package a CLI as a single binary](tutorials/first-binary.md) — build a
  small app with a real dependency into binaries for every platform, and
  learn what happens on the user's machine.
- [Release binaries from GitHub Actions](tutorials/github-actions.md) —
  attach binaries for every platform to a GitHub release on each tag push.

## Reference

Precise descriptions of every knob:

- [CLI](reference/cli.md) — `axe build`, `axe platforms`, and all flags.
- [Configuration](reference/configuration.md) — the `[tool.axe]` table in
  `pyproject.toml` and how defaults are derived from `[project]`.
- [Runtime](reference/runtime.md) — the `self` management commands,
  environment variables, and where installations live on disk.

## Internals

- [Runtime internals](runtime.md) — the bootstrap flow inside built
  binaries, and how it compares to pyapp and PyInstaller.
