import io
import json
import zipfile

import pytest

from axe import fetch, payload
from axe.platforms import pip_platform_tags


@pytest.fixture
def artifacts(tmp_path):
    uv = tmp_path / "uv-aarch64-apple-darwin.tar.gz"
    uv.write_bytes(b"uv archive bytes")
    python = tmp_path / "cpython-3.12.13+20260623-aarch64-apple-darwin-install_only_stripped.tar.gz"
    python.write_bytes(b"python archive bytes")
    dep = tmp_path / "six-1.17.0-py2.py3-none-any.whl"
    dep.write_bytes(b"PK six")
    return uv, python, dep


def compose(artifacts):
    uv, python, dep = artifacts
    return payload.compose(
        {"name": "demo", "version": "1.0"},
        "demo-1.0-py3-none-any.whl",
        b"PK demo wheel",
        [dep],
        uv,
        python,
    )


def test_compose_layout(artifacts):
    with zipfile.ZipFile(io.BytesIO(compose(artifacts))) as zf:
        names = set(zf.namelist())
        assert names == {
            "config.json",
            "wheels/demo-1.0-py3-none-any.whl",
            "wheels/six-1.17.0-py2.py3-none-any.whl",
            "uv/uv-aarch64-apple-darwin.tar.gz",
            "python/cpython-3.12.13+20260623-aarch64-apple-darwin-install_only_stripped.tar.gz",
        }
        config = json.loads(zf.read("config.json"))
        assert config["wheel_name"] == "demo-1.0-py3-none-any.whl"
        assert config["uv_archive"].startswith("uv/")
        assert config["python_archive"].startswith("python/")
        assert len(config["fingerprint"]) == 16
        # Archives are stored, not double-compressed.
        assert all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist())


def test_fingerprint_changes_with_content(artifacts, tmp_path):
    first = json.loads(zipfile.ZipFile(io.BytesIO(compose(artifacts))).read("config.json"))[
        "fingerprint"
    ]
    uv, python, dep = artifacts
    dep.write_bytes(b"PK six CHANGED")
    second = json.loads(zipfile.ZipFile(io.BytesIO(compose(artifacts))).read("config.json"))[
        "fingerprint"
    ]
    assert first != second


SUMS = {
    "cpython-3.12.12+20260623-aarch64-apple-darwin-install_only.tar.gz": "aa",
    "cpython-3.12.12+20260623-aarch64-apple-darwin-install_only_stripped.tar.gz": "bb",
    "cpython-3.12.13+20260623-aarch64-apple-darwin-install_only.tar.gz": "cc",
    "cpython-3.13.2+20260623-aarch64-apple-darwin-install_only_stripped.tar.gz": "dd",
    "cpython-3.12.13+20260623-x86_64-pc-windows-msvc-install_only_stripped.tar.gz": "ee",
}


def test_resolve_python(monkeypatch):
    monkeypatch.setattr(fetch, "_pbs_checksums", lambda release: SUMS)

    # Minor pin resolves to the newest patch; stripped preferred when present.
    version, artifact = fetch.resolve_python("3.12", "20260623", "darwin", "arm64")
    assert version == "3.12.13"
    assert artifact.endswith("install_only.tar.gz")  # 3.12.13 has no stripped build here

    version, artifact = fetch.resolve_python("3.12.12", "20260623", "darwin", "arm64")
    assert version == "3.12.12"
    assert artifact.endswith("install_only_stripped.tar.gz")

    _, artifact = fetch.resolve_python("3.12", "20260623", "windows", "amd64")
    assert "windows-msvc" in artifact

    with pytest.raises(fetch.FetchError, match="no CPython 3.11"):
        fetch.resolve_python("3.11", "20260623", "darwin", "arm64")


def test_pip_platform_tags():
    linux = pip_platform_tags("linux", "arm64")
    assert "manylinux_2_28_aarch64" in linux
    assert "manylinux2014_aarch64" in linux
    mac = pip_platform_tags("darwin", "arm64")
    assert "macosx_11_0_arm64" in mac
    assert "macosx_12_0_universal2" in mac
    assert pip_platform_tags("windows", "amd64") == ["win_amd64"]
