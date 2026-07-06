# axe — Design Spec

Date: 2026-07-07
Status: Approved

## Summary

`axe` is a uv-managed Python package that turns a Python project into
self-bootstrapping single-file binaries for every major platform. It gives
zero-friction shipping on both sides:

- **App developers** need no Go, no cross-compilers, no Docker. `uv add --dev
  axe`, write a couple of lines in `pyproject.toml`, run `axe build
  --all-platforms`.
- **App users** need no Python and no uv. They run the binary; it bootstraps
  a cached virtual environment on first run (uv downloads Python and installs
  the embedded wheel) and is instant on every run after.

Behavior parity target: [pyapp](https://github.com/ofek/pyapp)'s runtime flow
(see its `docs/runtime.md`), restricted to the uv-first path. Not
option-for-option parity; pyapp features outside the uv path (pip mode, custom
CPython distributions, full isolation) are explicitly out of scope for v1.

## Decisions made

| Decision | Choice |
|---|---|
| v1 scope | uv-first core; pyapp behavioral parity for the main flow only |
| App payload | Embed the wheel in the binary (offline app delivery; only Python + deps fetched at first run) |
| Dev toolchain | Go installed via Homebrew for axe development; CI builds release stubs |

## Architecture

Two halves connected by a byte-level payload format:

### 1. Go runtime stub (`runtime/`, a Go module)

A small static binary (CGO disabled) compiled once per platform. At startup it
opens **its own executable file**, seeks to the end, and reads a trailer that
locates an appended payload (JSON config + the app's wheel). The compiled
stubs ship inside the published axe wheel at
`src/axe/stubs/axe-runtime-<os>-<arch>[.exe]`.

### 2. Python CLI (`axe`)

`axe build` never compiles anything:

1. Read config from `[tool.axe]` in `pyproject.toml` (with defaults derived
   from `[project]`).
2. Build the project's wheel with `uv build`.
3. For each target platform, write out
   `stub + wheel bytes + JSON config + trailer` as the final binary.

Because building is byte concatenation, `axe build --all-platforms` produces
all targets in seconds on any machine.

### Payload trailer format (v1)

Appended after the stub bytes, read backwards from EOF by the runtime:

```
[stub executable bytes]
[wheel bytes]
[config JSON (UTF-8)]
[fixed-size trailer:
    wheel offset   (u64 LE)
    wheel length   (u64 LE)
    config offset  (u64 LE)
    config length  (u64 LE)
    format version (u32 LE)
    magic          "AXEBIN01" (8 bytes)]
```

The config JSON carries: app name, app version, entrypoint spec, requested
Python version, uv version to bootstrap, exposed management commands, and the
payload fingerprint (SHA-256 of wheel + config), which keys the install dir.

### Supported target platforms (v1)

`linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`,
`windows/amd64`.

## Runtime behavior

Mirrors pyapp's initialization flow on the uv path:

- **First run** (install dir absent):
  1. Ensure uv: use the shared cache at `~/.cache/axe/uv/<version>`
     (platform-appropriate cache dir); if absent, download the pinned uv
     version from official GitHub releases and verify its SHA-256 checksum.
  2. Create the venv: `uv venv --python <pinned>` — uv downloads CPython if
     needed.
  3. Extract the embedded wheel to a temp location and `uv pip install` it
     into the venv (isolated; no user pip config).
  4. Installation is atomic: bootstrap into a temp dir, rename into place.
     A file lock guards against concurrent first runs.
- **Install dir**: `<data-dir>/axe/<app-name>/<fingerprint>` where data-dir is
  `~/.local/share` (XDG-aware) on Linux, `~/Library/Application Support` on
  macOS, `%LOCALAPPDATA%` on Windows. A new binary version has a new
  fingerprint, so it gets a fresh environment automatically.
- **Subsequent runs**: only an install-dir existence check, then execute —
  maximizing CLI responsiveness (same contract as pyapp).
- **Execution**: `execvp` process replacement on non-Windows; spawn +
  exit-code and signal forwarding on Windows. Python runs in isolated mode
  (`-I`). The env var `AXE=1` is injected so apps can detect this
  installation mode.

### Management commands

A single reserved top-level command group `self`; everything else is
forwarded to the app.

Always exposed:

- `self remove` — wipe the installation
- `self restore` — wipe and reinstall
- `self update` — reinstall the environment from the embedded payload
  (fresh Python/deps resolution); PyPI-based update is out of scope for v1

Hidden by default, exposable via build config:

- `self python` — invoke the installed Python
- `self python-path` — print the installed Python's path
- `self cache [uv] [-r]` — show or remove cached assets
- `self metadata` — print app name/version/install dir

## Config surface — `[tool.axe]`

Minimal with smart defaults; a trivial project needs zero or near-zero axe
config:

| Key | Default | Meaning |
|---|---|---|
| `entrypoint` | the sole entry in `[project.scripts]` (error if 0 or >1 and unset) | console-script name or `module:func` / `-m module` spec |
| `python` | lowest version satisfying `requires-python`, else a maintained default | CPython version uv should provision |
| `uv-version` | pinned per axe release | uv version the stub bootstraps |
| `expose` | `[]` | extra `self` subcommands to expose |

CLI commands: `axe build [--all-platforms | --platform <os/arch>] [-o DIR]`
and `axe platforms` (list supported targets). Output goes to `dist/bin/` by
default, named `<app>-<version>-<os>-<arch>[.exe]`.

## Repo layout

```
axe/
├── pyproject.toml          # uv-managed, hatchling build backend
├── src/axe/                # CLI (build, platforms), config loader, payload packer
│   └── stubs/              # prebuilt runtime binaries (git-ignored; CI/script-built)
├── runtime/                # Go module: trailer reader, uv bootstrap, self commands
├── scripts/build_stubs.py  # cross-compiles stubs via GOOS/GOARCH for all targets
├── examples/cowsay/        # end-to-end demo app
└── tests/                  # pytest suite
```

Release stubs are built in CI (GitHub Actions with Go) and bundled into the
wheel; developers working on axe itself use a local Go (Homebrew) via
`scripts/build_stubs.py`.

## Testing

- **Python (pytest)**: trailer pack/unpack round-trip, config parsing and
  defaulting, build command wiring.
- **Go (`go test`)**: trailer parsing (including corrupt/missing trailer),
  install-dir/fingerprint logic, config decoding.
- **End-to-end (the contract)**: build the cowsay example for the current
  platform, run the produced binary against a clean cache dir, assert output;
  run again and assert the fast path (no re-bootstrap); exercise `self
  remove`/`restore`.

## Error handling

- Human-readable failures naming the actual cause: uv download/network
  failure, checksum mismatch, unsupported platform, missing/ambiguous
  entrypoint, corrupt payload.
- Non-zero exit codes on all failures; the app's own exit code is passed
  through untouched.
- `AXE_DEBUG=1` enables verbose bootstrap logging from the stub.

## Out of scope (v1)

- pip-based installation, custom CPython distributions, full-isolation mode
- PyPI-fetch payload mode and `self update` to newer released versions
- Code signing / notarization
- Compression of the embedded payload (revisit if binary size matters)
