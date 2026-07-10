# Changelog

## Unreleased

### Enhancements

- Run apps in Python isolated mode for every entrypoint kind: console-script
  entrypoints now strip `PYTHON*` variables and disable user site-packages,
  matching what `-I` already did for module and spec entrypoints
- Isolate the first-run bootstrap from the user's environment: `UV_*`,
  `PIP_*`, `PYTHON*`, `VIRTUAL_ENV`, and `CONDA_PREFIX` no longer influence
  uv during installation (the uv analogue of `pip --isolated`)
- Install embedded wheels in a deterministic (sorted) order

### Documentation

- Document the runtime flow in `docs/runtime.md`, mirroring pyapp's runtime
  behavior page with axe's offline-specialized flowchart

## 0.2.1

### Enhancements

- Print progress lines for each build step (wheel build, per-platform
  dependency resolution and downloads); suppress with `axe build --quiet`
- Add `axe build --verbose` to stream the output of underlying tools (uv, pip)
- Fail with an actionable error instead of hanging when a network operation
  stalls (timeouts on all tool invocations and artifact downloads, with a
  hint about TLS-intercepting proxies and `UV_NATIVE_TLS=1`)

## 0.2.0

### Breaking changes

- Built binaries are now fully offline: uv, CPython
  ([python-build-standalone](https://github.com/astral-sh/python-build-standalone)),
  and all dependency wheels are embedded at build time; the first run touches
  no network. Binaries grow to ~45–60 MB, and every dependency must publish
  wheels for each target platform
- Payload format v2; binaries must be rebuilt with `axe build`

### Enhancements

- Resolve dependencies per target platform (`uv pip compile --python-platform`)
- Cache build artifacts (checksum-verified) so repeat builds are fast
- Add `[tool.axe] python-release` to pin the python-build-standalone release;
  `python` now accepts full `X.Y.Z` pins
- Remove all network code from the runtime stub (6 MB → 2.5 MB)
- Recover automatically from an interrupted first-run bootstrap

## 0.1.1

### Bug fixes

- Validate at build time that the wheel provides the configured entrypoint,
  instead of shipping a binary that fails on the end user's machine (a bare
  `uv init` project produces no console scripts)

### Documentation

- Document that projects must be packaged (`uv init --package`)

## 0.1.0

Initial release: `axe build` wraps a Python project into self-bootstrapping
single-file binaries for linux/darwin/windows (amd64/arm64) with no Go or
cross-compiler needed; the runtime bootstraps a cached environment with uv on
first run and supports `self remove|restore|update` management commands.
