---
name: verify
description: Build/launch/drive recipe for verifying axe changes end-to-end
---

# Verifying axe changes

axe is a build-time CLI (`axe build`) plus a Go runtime stub embedded into the
built binaries. Its surface is the `axe` CLI and the binaries it produces.

## Build / launch

- Stubs: `uv run python scripts/build_stubs.py` (needs Go). The stubs under
  `src/axe/stubs/` are gitignored local artifacts and can be **stale** —
  e2e-looking failures like `unknown self command "metadata"` on a clean tree
  mean rebuild stubs, not a real regression. Rebuild takes ~30s.
- Drive: `uv init --package <tmp>/demo`, then
  `uv run axe build <tmp>/demo -v` and run the produced
  `<tmp>/demo/dist/bin/demo-0.1.0-<os>-<arch>` binary.

## Gotchas

- Set `AXE_CACHE_DIR=<fresh dir>` to force real artifact downloads; otherwise
  fetches are served from `~/Library/Caches/axe` and never hit the network.
- To verify download behavior offline, serve `~/Library/Caches/axe/artifacts`
  through a local `http.server` in GitHub-release layout
  (`/<base>/<tag>/<artifact>`, uv needs `<artifact>.sha256` next to each file,
  pbs needs `SHA256SUMS` per tag) and point `[tool.axe] uv-releases-url` /
  `python-build-standalone-releases-url` at it.
- `-v` streams `GET <url>` lines — the quickest evidence of where artifacts
  were fetched from.
