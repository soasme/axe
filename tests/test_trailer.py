import io
import zipfile

import pytest

from axe import trailer


def make_payload(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


PAYLOAD = make_payload({"config.json": b'{"name": "demo"}', "wheels/demo.whl": b"PK demo"})


def test_round_trip():
    stub = b"fake ELF bytes"
    binary = trailer.pack(stub, PAYLOAD)

    assert binary.startswith(stub)
    payload = trailer.unpack(binary)
    assert payload.data == PAYLOAD
    with zipfile.ZipFile(io.BytesIO(payload.data)) as zf:
        assert zf.read("config.json") == b'{"name": "demo"}'


def test_no_magic():
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(b"a plain binary without any axe trailer at all............")


def test_too_small():
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(b"tiny")


def test_corrupt_offsets():
    binary = bytearray(trailer.pack(b"stub", PAYLOAD))
    binary[-trailer.TRAILER_SIZE + 8 : -trailer.TRAILER_SIZE + 16] = (1 << 40).to_bytes(8, "little")
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(bytes(binary))


def test_unsupported_version():
    binary = bytearray(trailer.pack(b"stub", PAYLOAD))
    binary[-trailer.TRAILER_SIZE + 16 : -trailer.TRAILER_SIZE + 20] = (99).to_bytes(4, "little")
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(bytes(binary))
