"""Sphinx configuration. Docs are plain Markdown (MyST); README.md stays the
index for people browsing docs/ on GitHub, index.md is the Sphinx root."""

from importlib.metadata import version as pkg_version

project = "axe"
author = "soasme"
release = pkg_version("axe")

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
]

exclude_patterns = ["_build", "README.md"]

# Generate #anchors for headings so cross-doc links like
# configuration.md#entrypoint resolve, and render ```mermaid fences (which
# GitHub also renders) as diagrams.
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

html_theme = "shibuya"
html_title = f"axe {release}"
html_theme_options = {
    "github_url": "https://github.com/soasme/axe",
    "nav_links": [
        {"title": "PyPI", "url": "https://pypi.org/project/axe/"},
    ],
}
