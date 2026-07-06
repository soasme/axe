import pytest

from axe import trailer


def test_round_trip():
    stub = b"fake ELF bytes"
    wheel = b"PK\x03\x04 wheel contents"
    config = b'{"name": "demo"}'
    binary = trailer.pack(stub, wheel, config)

    assert binary.startswith(stub)
    payload = trailer.unpack(binary)
    assert payload.wheel == wheel
    assert payload.config == config


def test_empty_sections_round_trip():
    payload = trailer.unpack(trailer.pack(b"stub", b"", b""))
    assert payload.wheel == b""
    assert payload.config == b""


def test_no_magic():
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(b"a plain binary without any axe trailer at all............")


def test_too_small():
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(b"tiny")


def test_corrupt_offsets():
    binary = bytearray(trailer.pack(b"stub", b"wheel", b"config"))
    binary[-trailer.TRAILER_SIZE + 8 : -trailer.TRAILER_SIZE + 16] = (1 << 40).to_bytes(
        8, "little"
    )
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(bytes(binary))


def test_unsupported_version():
    binary = bytearray(trailer.pack(b"stub", b"wheel", b"config"))
    binary[-trailer.TRAILER_SIZE + 32 : -trailer.TRAILER_SIZE + 36] = (99).to_bytes(4, "little")
    with pytest.raises(trailer.TrailerError):
        trailer.unpack(bytes(binary))
