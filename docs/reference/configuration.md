# Configuration reference

Axe reads its build configuration from your project's `pyproject.toml`.
Everything lives in the optional `[tool.axe]` table; every key has a default
derived from `[project]`, so most projects need no `[tool.axe]` at all.

```toml
[tool.axe]
entrypoint = "mycli"          # default: the sole [project.scripts] entry
python = "3.12"               # default: lower bound of requires-python
uv-version = "0.10.6"         # uv embedded into the binary
python-release = "20260623"   # python-build-standalone release tag
uv-releases-url = "https://mirror.corp/uv"    # mirror for uv downloads
python-build-standalone-releases-url = "https://mirror.corp/pbs"  # ...and CPython
expose = ["metadata"]         # extra `self` commands, or "all"
self-command-group = true     # false: don't reserve `self` at all
```

## Required `[project]` metadata

- `name` and `version` — used to name binaries and key installations.
  `version` must be static; dynamic versions are not supported yet.
- An entrypoint (see below).

## `entrypoint`

What the binary runs. Three forms are accepted:

| Form | Example | Runs as |
| --- | --- | --- |
| console script | `"mycli"` | the script `[project.scripts]` installs into the venv |
| module | `"-m mypkg"` | `python -I -m mypkg` |
| spec | `"mypkg.cli:main"` | imports `mypkg.cli` and calls `main()` |

**Default:** the sole `[project.scripts]` entry. If the project has no
scripts, or more than one, axe asks you to set `entrypoint` explicitly:

```toml
[project.scripts]
mycli = "mycli:main"
mycli-admin = "mycli.admin:main"

[tool.axe]
entrypoint = "mycli"    # each binary gets exactly one entrypoint
```

## `python`

The CPython version embedded into the binary.

- `"3.12"` — the newest available `3.12.x` from the pinned
  python-build-standalone release.
- `"3.12.13"` — pins the exact version.

**Default:** the lower bound of `[project] requires-python` (its first
`>=`, `==`, or `~=` specifier). If `requires-python` only has upper bounds,
axe falls back to its per-release default (currently 3.12).

## `uv-version`

The uv release embedded into the binary and used at runtime to create the
venv and install wheels offline.

**Default:** pinned per axe release (currently 0.10.6).

## `python-release`

The [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
release tag that provides the embedded CPython.

**Default:** pinned per axe release (currently 20260623).

## `uv-releases-url` and `python-build-standalone-releases-url`

Where `axe build` downloads the uv and CPython
(python-build-standalone) release artifacts it embeds. Point these at an
internal mirror when the build machine can't reach github.com — a
network-isolated environment behind a proxy, an artifact repository like
Artifactory or Nexus, or a plain file server.

```toml
[tool.axe]
uv-releases-url = "https://mirror.corp/astral-sh/uv/releases/download"
python-build-standalone-releases-url = "https://mirror.corp/astral-sh/python-build-standalone/releases/download"
```

The mirror must serve the same layout as the GitHub release download URLs;
axe appends `/<release tag>/<artifact filename>` (plus `.sha256` and
`SHA256SUMS` checksum files) to the configured base. Downloads are still
checksum-verified, but the checksums come from the same mirror as the
artifacts, so this catches corruption and incomplete mirroring — it cannot
detect a malicious mirror that serves matching tampered artifacts and
checksum files. Only point axe at a mirror you trust as much as github.com.

**Defaults:**

- `https://github.com/astral-sh/uv/releases/download`
- `https://github.com/astral-sh/python-build-standalone/releases/download`

### Mirror credentials

If the mirror requires HTTP Basic authentication, set credentials as
environment variables on the build machine (never in `pyproject.toml`,
where they would be committed):

| Variable | Applies to |
| --- | --- |
| `UV_RELEASES_USERNAME` / `UV_RELEASES_PASSWORD` | `uv-releases-url` downloads |
| `PYTHON_BUILD_STANDALONE_RELEASES_USERNAME` / `PYTHON_BUILD_STANDALONE_RELEASES_PASSWORD` | `python-build-standalone-releases-url` downloads |

For token-based mirrors that ignore the username, setting just the
password variable works (an empty username is sent).

## `expose`

Extra `self` management commands compiled into the binary, beyond the
always-available `remove`, `restore`, and `update`. A list drawn from:

- `"python"` — run the installed interpreter
- `"python-path"` — print the installed interpreter's path
- `"cache"` — show or remove the shared uv cache
- `"metadata"` — print name, version, python, uv, and install path

or the string `"all"` for all four. See the
[runtime reference](runtime.md#self-commands) for what each command does.

**Default:** none — a minimal management surface for end users.

## `self-command-group`

Set to `false` and built binaries won't reserve the `self` command group at
all — `myapp self …` is passed to your app like any other arguments. Use it
when your CLI has its own `self` subcommand.

Combining `false` with `expose` is a configuration error, since the exposed
commands would be unreachable.

**Default:** `true` — binaries get `self remove`, `self restore`, and
`self update`. Without them, the only way to manage an installation is
deleting its [install directory](runtime.md#install-locations) by hand.
