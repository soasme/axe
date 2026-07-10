# CLI reference

```console
$ axe build [PROJECT] [-o DIR] [-p OS/ARCH]... [--all-platforms] [-q | -v]
$ axe platforms
$ axe --version
```

## `axe build`

Builds self-contained single-file binaries for one or more target platforms.

```console
$ axe build [PROJECT] [options]
```

| Argument / option | Meaning | Default |
| --- | --- | --- |
| `PROJECT` | project directory containing `pyproject.toml` | `.` |
| `-o`, `--output DIR` | output directory | `<project>/dist/bin` |
| `-p`, `--platform OS/ARCH` | target platform; repeatable | the current platform |
| `--all-platforms` | build every supported platform | off |
| `-q`, `--quiet` | print nothing but errors | off |
| `-v`, `--verbose` | stream the output of the underlying tools (uv, pip) | off |

`-q` and `-v` are mutually exclusive.

For each target platform, `axe build`:

1. builds your project's wheel with uv,
2. resolves and downloads every dependency wheel *for that platform*
   (`uv pip compile --python-platform` + `pip download`),
3. fetches the pinned CPython from
   [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
   and the pinned [uv](https://github.com/astral-sh/uv),
4. appends everything as a payload to the precompiled Go runtime stub for
   that platform.

All downloads are checksum-verified and cached on the build machine, so
builds after the first take seconds. Configuration comes from
`pyproject.toml` — see the [configuration reference](configuration.md).

Output files are named `<name>-<version>-<os>-<arch>` (plus `.exe` on
Windows), e.g. `mycli-0.1.0-linux-amd64`.

### Exit status

`0` on success; `1` with an `error: …` line on stderr for configuration,
resolution, download, or build failures.

### Troubleshooting

- **Downloads fail or stall behind a corporate proxy** — set
  `UV_NATIVE_TLS=1` so uv uses the system trust store, and run with `-v` to
  see the underlying tool output.
- **"no entrypoint" / "multiple [project.scripts] entries"** — see
  [entrypoint](configuration.md#entrypoint).
- **A dependency has no wheel for a target platform** — every dependency
  must publish a wheel per target (pure-Python wheels cover all platforms);
  sdist-only dependencies cannot be embedded.

## `axe platforms`

Prints the supported target platforms, one per line:

```
linux/amd64
linux/arm64
darwin/amd64
darwin/arm64
windows/amd64
```

## `axe --version`

Prints `axe <version>`.
