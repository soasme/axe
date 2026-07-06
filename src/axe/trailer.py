"""Binary payload trailer: how a stub finds the wheel + config appended to it.

Layout of a built binary:

    [stub executable bytes]
    [wheel bytes]
    [config JSON, UTF-8]
    [trailer, 44 bytes:
        wheel offset   u64 LE
        wheel length   u64 LE
        config offset  u64 LE
        config length  u64 LE
        format version u32 LE
        magic          "AXEBIN01"]

The Go runtime (runtime/trailer.go) reads this backwards from EOF; both sides
must agree exactly.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from . import TRAILER_FORMAT_VERSION

MAGIC = b"AXEBIN01"
TRAILER_STRUCT = struct.Struct("<QQQQI8s")
TRAILER_SIZE = TRAILER_STRUCT.size  # 44


class TrailerError(Exception):
    pass


@dataclass
class Payload:
    wheel: bytes
    config: bytes  # JSON document


def pack(stub: bytes, wheel: bytes, config: bytes) -> bytes:
    wheel_offset = len(stub)
    config_offset = wheel_offset + len(wheel)
    trailer = TRAILER_STRUCT.pack(
        wheel_offset,
        len(wheel),
        config_offset,
        len(config),
        TRAILER_FORMAT_VERSION,
        MAGIC,
    )
    return stub + wheel + config + trailer


def unpack(binary: bytes) -> Payload:
    if len(binary) < TRAILER_SIZE:
        raise TrailerError("binary too small to contain a trailer")
    wheel_offset, wheel_len, config_offset, config_len, version, magic = TRAILER_STRUCT.unpack(
        binary[-TRAILER_SIZE:]
    )
    if magic != MAGIC:
        raise TrailerError("no axe payload trailer found (bad magic)")
    if version != TRAILER_FORMAT_VERSION:
        raise TrailerError(f"unsupported trailer format version {version}")
    end = len(binary) - TRAILER_SIZE
    if config_offset + config_len > end or wheel_offset + wheel_len > end:
        raise TrailerError("corrupt trailer: payload extends past end of file")
    return Payload(
        wheel=binary[wheel_offset : wheel_offset + wheel_len],
        config=binary[config_offset : config_offset + config_len],
    )
