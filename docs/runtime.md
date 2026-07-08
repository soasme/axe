# Runtime behavior

Axe's runtime stub replicates [pyapp](https://ofek.dev/pyapp/latest/runtime/)'s
runtime behavior, rewritten in Go and specialized for axe's design: everything
the app needs is embedded in the binary, so every network-dependent branch of
pyapp's flow disappears.

## Initialization

Binaries bootstrap themselves on the first run. All subsequent invocations
only check that the installation marker exists and nothing else, to maximize
CLI responsiveness.

The nodes with rounded edges are conditions and those with jagged edges are
actions.

```mermaid
flowchart TD
    SELF([self command invoked]) -- Yes --> MANAGE[[Run management command]]
    SELF -- No --> INSTALLED([Installed])
    INSTALLED -- Yes --> EXECUTE[[Execute project]]
    INSTALLED -- No --> LOCK[[Acquire bootstrap lock]]
    LOCK --> UVCACHED([uv cached])
    UVCACHED -- No --> UVEXTRACT[[Extract embedded uv into shared cache]]
    UVCACHED -- Yes --> PYEXTRACT[[Extract embedded CPython]]
    UVEXTRACT --> PYEXTRACT
    PYEXTRACT --> WHEELS[[Extract embedded wheels]]
    WHEELS --> VENV[[Create virtual environment]]
    VENV --> INSTALL[[Install wheels offline]]
    INSTALL --> MARKER[[Write completion marker]]
    MARKER --> EXECUTE
```

Step by step:

- **Installed** — a single `stat` of the `.axe-installed` marker inside the
  installation directory (`<data dir>/<app name>/<payload fingerprint>`). A
  new binary version has a new fingerprint, so it gets a fresh environment
  automatically. `AXE_DATA_DIR` overrides the base directory.
- **Bootstrap lock** — concurrent first runs are serialized with an
  exclusively-created lock file; stale locks from crashed processes are
  reclaimed. A directory without the completion marker is treated as crash
  residue and rebuilt from scratch.
- **uv cached** — the embedded uv release archive is extracted once into a
  shared cache (`<cache dir>/uv/<version>`) and reused by every axe app
  pinning the same uv version. `AXE_CACHE_DIR` overrides the location,
  `AXE_UV` bypasses it entirely.
- **Extract / venv / install** — the embedded python-build-standalone
  distribution and dependency wheels are unpacked, then uv creates the venv
  and installs the app with `--offline --no-index --find-links`. The runtime
  contains no network code at all.
- **Execute / manage** — `self` is the reserved management command group
  (`remove`, `restore`, `update` always; `python`, `python-path`, `cache`,
  `metadata` when exposed at build time); everything else goes to the app.

### Differences from pyapp

pyapp's conditions that axe resolves at *build* time instead of runtime:

| pyapp runtime condition | axe |
| --- | --- |
| Distribution cached / embedded / from source | always embedded |
| Full isolation | not supported; always a venv |
| UV enabled / UV cached / download UV | uv always embedded, cached on first run |
| External pip / pip cached / download pip | uv only |
| Project embedded / dependency file / single project | project + dependency wheels always embedded |
| Management enabled | always enabled as `self` |

## Execution

Projects are executed using `execvp` on non-Windows systems, replacing the
process. On Windows the app runs as a child process and its exit code is
forwarded.

To provide consistent behavior on each user's machine:

- Python runs projects in [isolated mode](https://docs.python.org/3/using/cmdline.html#cmdoption-I).
  Module (`-m pkg`) and spec (`pkg.mod:func`) entrypoints pass `-I` directly;
  console-script entrypoints get the environment equivalent (all `PYTHON*`
  variables are stripped, user site-packages and script-dir `sys.path`
  prepending are disabled).
- During installation, uv runs with configuration and environment influence
  disabled — the uv analogue of pip's `--isolated`: `UV_NO_CONFIG=1`,
  `UV_OFFLINE=1`, and any inherited `UV_*`, `PIP_*`, `PYTHON*`,
  `VIRTUAL_ENV`, or `CONDA_PREFIX` variables are dropped.

The app's environment gets `AXE=1` so it can detect axe installs;
`AXE_DEBUG=1` makes the stub verbose.
