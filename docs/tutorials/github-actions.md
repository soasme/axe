# Tutorial: release binaries from GitHub Actions

Because axe cross-builds from any machine, one cheap Linux runner can
produce the binaries for every supported platform — no build matrix, no
macOS or Windows runners. This tutorial wires that into a workflow that
attaches binaries to a GitHub release whenever you push a version tag.

It assumes your project already builds locally with `axe build` (if not,
start with [the first tutorial](first-binary.md)) and that axe is in your
dev dependencies (`uv add --dev axe`).

## The workflow

Create `.github/workflows/release-binaries.yml`:

```yaml
name: Release binaries

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write   # create the release and upload assets

jobs:
  binaries:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5

      - name: Build binaries for all platforms
        run: uv run axe build --all-platforms

      - name: Generate checksums
        working-directory: dist/bin
        run: sha256sum * > SHA256SUMS

      - name: Create release and upload binaries
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "${GITHUB_REF_NAME}" dist/bin/* \
            --verify-tag \
            --title "${GITHUB_REF_NAME}" \
            --generate-notes
```

That's the whole thing. Note what's *absent*: no Go setup (axe's wheel ships
precompiled runtime stubs), no matrix over operating systems, and no caching
configuration to get right — a cold build fetches CPython, uv, and the
dependency wheels once, checksum-verified.

## Tag and release

```console
$ git tag v0.1.0
$ git push origin v0.1.0
```

A few minutes later the `v0.1.0` release carries one binary per platform
plus a `SHA256SUMS` file:

```
greet-0.1.0-linux-amd64
greet-0.1.0-linux-arm64
greet-0.1.0-darwin-amd64
greet-0.1.0-darwin-arm64
greet-0.1.0-windows-amd64.exe
SHA256SUMS
```

Users download one file and run it. Nothing to install, nothing else to
download — the binary works offline from the first run.

## Guard against tag/version drift

A tag that doesn't match `[project] version` produces confusingly-named
binaries. Fail fast by inserting this step before the build:

```yaml
      - name: Check tag matches package version
        run: |
          version="$(uv version --short)"
          if [ "${GITHUB_REF_NAME}" != "v${version}" ]; then
            echo "tag ${GITHUB_REF_NAME} does not match pyproject version ${version}" >&2
            exit 1
          fi
```

## Variations

- **Build on every push** (to catch packaging breakage early): trigger on
  `pull_request` and upload with `actions/upload-artifact` instead of
  `gh release create`.
- **Only some platforms**: replace `--all-platforms` with repeated
  `-p` flags, e.g. `-p linux/amd64 -p darwin/arm64`.
- **Rebuild an existing release**: add a `workflow_dispatch` trigger with a
  tag input and check out `refs/tags/${{ inputs.tag }}`. Axe's own
  [`binaries.yml`](https://github.com/soasme/axe/blob/main/.github/workflows/binaries.yml)
  does exactly this.
