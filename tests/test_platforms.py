import pytest

from axe.platforms import (
    binary_filename,
    current_platform,
    parse_platform,
    platform_strings,
    stub_filename,
)


def test_parse_platform():
    assert parse_platform("linux/amd64") == ("linux", "amd64")
    with pytest.raises(ValueError, match="unsupported"):
        parse_platform("plan9/mips")
    with pytest.raises(ValueError, match="invalid"):
        parse_platform("linux")


def test_current_platform_is_supported():
    assert f"{'/'.join(current_platform())}" in platform_strings()


def test_filenames():
    assert stub_filename("linux", "amd64") == "axe-runtime-linux-amd64"
    assert stub_filename("windows", "amd64") == "axe-runtime-windows-amd64.exe"
    assert binary_filename("app", "1.0", "windows", "amd64") == "app-1.0-windows-amd64.exe"
    assert binary_filename("app", "1.0", "darwin", "arm64") == "app-1.0-darwin-arm64"
