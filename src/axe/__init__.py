"""axe: ship Python apps as self-bootstrapping single-file binaries."""

__version__ = "0.1.0"

# uv version the runtime stub bootstraps when none is configured. Bumped per
# axe release.
DEFAULT_UV_VERSION = "0.10.6"

# CPython version used when requires-python gives no lower bound.
DEFAULT_PYTHON_VERSION = "3.12"

TRAILER_FORMAT_VERSION = 1
