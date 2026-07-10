"""axe: ship Python apps as self-bootstrapping single-file binaries."""

__version__ = "0.4.0"

# uv version embedded into built binaries. Bumped per axe release.
DEFAULT_UV_VERSION = "0.10.6"

# CPython version used when requires-python gives no lower bound.
DEFAULT_PYTHON_VERSION = "3.12"

# python-build-standalone release tag providing the embedded CPython.
# Bumped per axe release; overridable via [tool.axe] python-release.
DEFAULT_PYTHON_RELEASE = "20260623"

TRAILER_FORMAT_VERSION = 2
