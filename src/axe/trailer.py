"""Binary payload trailer: how a stub finds the payload appended to it.

Layout of a built binary (format version 2):

    [stub executable bytes]
    [payload: a single ZIP archive]
    [trailer, 28 bytes:
        payload offset u64 LE
        payload length u64 LE
        format version u32 LE
        magic          "AXEBIN01"]

The payload zip contains everything the first run needs, so no network access
is ever required on the user's machine:

    config.json                 runtime configuration
    wheels/*.whl                the app wheel + all dependency wheels
    uv/<uv release artifact>    uv-<triple>.tar.gz (or .zip on Windows)
    python/<pbs artifact>       python-build-standalone install_only tarball

The Go runtime (runtime/trailer.go) reads this backwards from EOF; both sides
must agree exactly.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from . import TRAILER_FORMAT_VERSION

MAGIC = b"AXEBIN01"
TRAILER_STRUCT = struct.Struct("<QQI8s")
TRAILER_SIZE = TRAILER_STRUCT.size  # 28


class TrailerError(Exception):
    pass


@dataclass
class Payload:
    data: bytes  # the payload zip


def pack(stub: bytes, payload: bytes) -> bytes:
    trailer = TRAILER_STRUCT.pack(
        len(stub),
        len(payload),
        TRAILER_FORMAT_VERSION,
        MAGIC,
    )
    return stub + payload + trailer


def unpack(binary: bytes) -> Payload:
    if len(binary) < TRAILER_SIZE:
        raise TrailerError("binary too small to contain a trailer")
    offset, length, version, magic = TRAILER_STRUCT.unpack(binary[-TRAILER_SIZE:])
    if magic != MAGIC:
        raise TrailerError("no axe payload trailer found (bad magic)")
    if version != TRAILER_FORMAT_VERSION:
        raise TrailerError(f"unsupported trailer format version {version}")
    if offset + length > len(binary) - TRAILER_SIZE:
        raise TrailerError("corrupt trailer: payload extends past end of file")
    return Payload(data=binary[offset : offset + length])
