# Axe

Axe ships your Python app as a fully self-contained single-file binary — for
every major platform, from any machine, with zero extra toolchain.

- **App developers** need no Go, no cross-compilers, no Docker. Axe's wheel
  ships precompiled runtime stubs; `axe build` glues your app onto them.
- **App users** need no Python, no uv, and **no network**. The binary embeds
  uv, CPython, and every dependency wheel; the first run unpacks them into a
  cached environment and every run after is instant.

```console
$ uv init --package mycli && cd mycli
$ uv add --dev axe
$ uv run axe build --all-platforms
built dist/bin/mycli-0.1.0-linux-amd64 (52 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-linux-arm64 (50 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-darwin-amd64 (48 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-darwin-arm64 (47 MB, python 3.12.13, 0 dependency wheels)
built dist/bin/mycli-0.1.0-windows-amd64.exe (55 MB, python 3.12.13, 0 dependency wheels)
```

New here? Start with [getting started](getting-started.md).

```{toctree}
:hidden:

getting-started
```

```{toctree}
:hidden:
:caption: Tutorials

tutorials/first-binary
tutorials/github-actions
```

```{toctree}
:hidden:
:caption: Reference

reference/cli
reference/configuration
reference/runtime
```

```{toctree}
:hidden:
:caption: Internals

runtime
```
